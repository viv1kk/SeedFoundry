<script setup lang="ts">
// The build report (FR-R-1, FR-R-2, FR-R-4, ui-spec.md section 4, D-64, D-65): verdict and counts,
// findings grouped Numeric, Visual, Latency and Boundary, every test, the auto-resolved gates and
// the simulated usage, with View Dashboard, Rebuild and Approve. Everything comes from the report
// the server assembles from the build's kept events. Embeddable: the Build page, the Review page
// and M10's "Feedback + Report" view each place it, with their own heading level, and may leave the
// actions out. A dashboard finding's id links to the dashboard at All products with that finding's
// panels highlighted (`finding=<id>` in the URL). Rebuild and Approve stay stubs that say which
// milestone brings them (D-47).
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DASHBOARD_ID } from '../../dashboard/api'
import type { Finding, Report, Severity, TestStatus } from '../../report'
import { clock } from '../../stepper'
import { useReportsStore } from '../../stores/reports'
import { ITERATIONS, type Build } from '../../stores/lab'
import BaseButton from '../base/BaseButton.vue'
import BaseChip, { type ChipTone } from '../base/BaseChip.vue'

const props = withDefaults(defineProps<{ build: Build; headingLevel?: 1 | 2 | 3; actions?: boolean }>(), { headingLevel: 2, actions: true })

const reports = useReportsStore()
const router = useRouter()

watch(
  () => props.build.id,
  (id) => void reports.load(id),
  { immediate: true },
)

const report = computed<Report | null>(() => reports.reports.get(props.build.id) ?? null)
const error = computed(() => reports.errors.get(props.build.id) ?? '')

const h = (offset: number) => `h${Math.min(props.headingLevel + offset, 6)}`

const SEVERITY: Record<Severity, [string, ChipTone]> = {
  high: ['High', 'negative'],
  medium: ['Medium', 'warning'],
  low: ['Low', 'neutral'],
  advisory: ['Advisory', 'neutral'],
}

const RESULT: Record<TestStatus, [string, ChipTone]> = {
  pass: ['Passed', 'positive'],
  warn: ['Warned', 'warning'],
  fail: ['Failed', 'negative'],
  not_run: ['Not run', 'neutral'],
}

const count = (n: number) => n.toLocaleString('en-US')

const facts = computed(() => {
  const r = report.value
  if (!r) return []
  const c = r.counts
  const tests = [`${c.pass} passed`]
  if (c.warn) tests.push(`${c.warn} warned`)
  if (c.fail) tests.push(`${c.fail} failed`)
  if (c.not_run) tests.push(`${c.not_run} not run`)
  return [
    { label: 'Iteration', value: `${r.iteration} of ${ITERATIONS}` },
    { label: 'Duration', value: `${clock(r.duration)} simulated` },
    { label: 'Phases', value: c.phases_with_findings ? `${c.phases}, ${c.phases_with_findings} with findings` : String(c.phases) },
    { label: 'Tests', value: `${c.tests}: ${tests.join(', ')}` },
    { label: 'Findings', value: String(c.findings) },
    { label: 'Boundary advisories', value: String(c.advisories) },
    { label: 'Gates auto-resolved', value: String(c.gates) },
  ]
})

const phaseNames = computed(() => new Map((report.value?.phases ?? []).map((p) => [p.id, p.name])))

function where(finding: Finding): string {
  if (finding.advisory) return finding.line ? `${finding.file}, line ${finding.line}` : (finding.file ?? '')
  return (finding.panel_titles ?? []).join(', ')
}

function findingLink(finding: Finding) {
  return { name: 'review', params: { iteration: String(props.build.iteration) }, query: { dashboard: DASHBOARD_ID, finding: finding.id } }
}

const usage = computed(() => {
  const u = report.value?.usage
  if (!u) return []
  return [
    { label: 'LLM calls', value: count(u.llm_calls) },
    { label: 'Tokens in', value: count(u.tokens_in) },
    { label: 'Tokens out', value: count(u.tokens_out) },
    { label: 'API calls', value: count(u.api_calls) },
    { label: 'Sandbox time', value: `${u.sandbox_seconds.toFixed(1)} s` },
  ]
})

type Action = 'rebuild' | 'approve'

const WHY: Record<Action, string> = {
  rebuild: 'Rebuild opens the observer feedback editor, which arrives in M10.',
  approve: 'Approve arrives with the Seed page in M11.',
}

const said = ref('')

function viewDashboard(): void {
  void router.push({ name: 'review', params: { iteration: String(props.build.iteration) }, query: { dashboard: DASHBOARD_ID } })
}

const ids = computed(() => `report-${props.build.id}`)
</script>

<template>
  <section class="report" :aria-labelledby="`${ids}-title`" data-test="build-report">
    <header class="report__head">
      <component :is="h(0)" :id="`${ids}-title`" class="report__title">Build Report</component>
      <BaseChip v-if="report" :tone="report.verdict.tone" class="report__verdict" data-test="report-verdict">{{ report.verdict.label }}</BaseChip>
    </header>

    <p v-if="!report && !error" class="report__note" data-test="report-loading">Loading the build report</p>
    <p v-else-if="!report" class="report__note" role="alert" data-test="report-error">
      {{ error }}
      <BaseButton @click="reports.load(build.id)">Try again</BaseButton>
    </p>

    <template v-if="report">
      <dl class="report__facts" data-test="report-facts">
        <div v-for="fact in facts" :key="fact.label" class="report__fact">
          <dt>{{ fact.label }}</dt>
          <dd data-test="report-fact">{{ fact.value }}</dd>
        </div>
      </dl>

      <section class="report__section" :aria-labelledby="`${ids}-findings`" data-test="report-findings">
        <component :is="h(1)" :id="`${ids}-findings`" class="report__heading">Findings</component>
        <section
          v-for="group in report.groups"
          :key="group.category"
          class="report__group"
          :aria-labelledby="`${ids}-group-${group.category}`"
          :data-group="group.category"
          data-test="finding-group"
        >
          <component :is="h(2)" :id="`${ids}-group-${group.category}`" class="report__group-title">
            {{ group.category }}<span class="report__count">{{ group.findings.length }}</span>
          </component>
          <p v-if="group.category === 'Boundary'" class="report__aside">Advisories: reported, never counted against the verdict.</p>
          <p v-if="!group.findings.length" class="report__none" data-test="group-none">None.</p>
          <div v-else class="report__scroll">
            <table class="report__table">
              <caption class="visually-hidden">{{ group.category }} findings</caption>
              <thead>
                <tr>
                  <th scope="col">Finding</th>
                  <th scope="col">{{ group.category === 'Boundary' ? 'File' : 'Panel' }}</th>
                  <th scope="col">Expected</th>
                  <th scope="col">Shown</th>
                  <th scope="col">Severity</th>
                  <th scope="col">Found in</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="finding in group.findings" :key="finding.id" :data-finding="finding.id" data-test="finding">
                  <th scope="row">
                    <div class="report__finding">
                      <RouterLink v-if="!finding.advisory" :to="findingLink(finding)" class="report__id" data-test="finding-link">
                        {{ finding.id }}<span class="visually-hidden">: show on the dashboard</span>
                      </RouterLink>
                      <span v-else class="report__id">{{ finding.id }}</span>
                      <span v-if="finding.message" class="report__message">{{ finding.message }}</span>
                    </div>
                  </th>
                  <td data-test="finding-where">{{ where(finding) }}</td>
                  <td class="report__value" data-test="finding-expected">{{ finding.expected }}</td>
                  <td class="report__value" data-test="finding-shown">{{ finding.shown }}</td>
                  <td>
                    <BaseChip :tone="SEVERITY[finding.severity][1]" data-test="finding-severity">{{ SEVERITY[finding.severity][0] }}</BaseChip>
                  </td>
                  <td>{{ phaseNames.get(finding.phase) ?? finding.phase }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <section class="report__section" :aria-labelledby="`${ids}-tests`" data-test="report-tests">
        <component :is="h(1)" :id="`${ids}-tests`" class="report__heading">Tests</component>
        <div class="report__scroll">
          <table class="report__table">
            <caption class="visually-hidden">Every test of the build, by phase</caption>
            <thead>
              <tr>
                <th scope="col">Test</th>
                <th scope="col">Phase</th>
                <th scope="col">Name</th>
                <th scope="col">Result</th>
                <th scope="col">Detail</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="test in report.tests" :key="test.id" :data-test-id="test.id" data-test="test-row">
                <th scope="row" class="report__id">{{ test.id }}</th>
                <td>{{ test.phase_name }}</td>
                <td>{{ test.name }}</td>
                <td>
                  <BaseChip :tone="RESULT[test.status][1]" data-test="test-result">{{ RESULT[test.status][0] }}</BaseChip>
                </td>
                <td class="report__detail">{{ test.detail }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="report__section" :aria-labelledby="`${ids}-gates`" data-test="report-gates">
        <component :is="h(1)" :id="`${ids}-gates`" class="report__heading">Auto-resolved gates</component>
        <ul class="report__gates">
          <li v-for="gate in report.gates" :key="gate.id" data-test="gate">
            <span class="report__id">{{ gate.id }}</span>
            <span class="report__gate-kind">{{ gate.kind }}, {{ gate.stage }}</span>
            <span>Resolved: {{ gate.resolution }}.</span>
            <span class="report__basis">
              <template v-if="gate.basis">Basis: {{ gate.basis.file }}, {{ gate.basis.section }}</template>
              <template v-else>No matching section in Knowledge, so it resolved on default</template>
            </span>
          </li>
        </ul>
      </section>

      <section class="report__section" :aria-labelledby="`${ids}-usage`" data-test="report-usage">
        <component :is="h(1)" :id="`${ids}-usage`" class="report__heading">Simulated usage</component>
        <dl class="report__facts">
          <div v-for="fact in usage" :key="fact.label" class="report__fact">
            <dt>{{ fact.label }}</dt>
            <dd data-test="usage-fact">{{ fact.value }}</dd>
          </div>
        </dl>
        <p class="report__small" data-test="usage-note">Simulated: no model, Seed API or sandbox was called.</p>
      </section>
    </template>

    <footer v-if="actions" class="report__actions" data-test="report-actions">
      <BaseButton data-action="dashboard" @click="viewDashboard">View Dashboard</BaseButton>
      <BaseButton
        v-if="build.iteration === 1"
        aria-disabled="true"
        :aria-describedby="`${ids}-why-rebuild`"
        data-action="rebuild"
        @click="said = WHY.rebuild"
      >
        Rebuild
      </BaseButton>
      <BaseButton variant="primary" aria-disabled="true" :aria-describedby="`${ids}-why-approve`" data-action="approve" @click="said = WHY.approve">
        Approve
      </BaseButton>
      <span :id="`${ids}-why-rebuild`" class="visually-hidden">{{ WHY.rebuild }}</span>
      <span :id="`${ids}-why-approve`" class="visually-hidden">{{ WHY.approve }}</span>
      <p class="report__said" role="status" data-test="report-status">{{ said }}</p>
    </footer>
  </section>
</template>

<style scoped>
.report {
  display: grid;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-4) 0;
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.report__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.report__title {
  font-size: var(--text-lg);
  font-weight: 600;
}

.report__verdict {
  font-size: var(--text-sm);
}

.report__note,
.report__aside,
.report__none {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.report__facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--space-3) var(--space-6);
  margin: 0;
}

.report__fact dt {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
}

.report__fact dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.report__section {
  display: grid;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}

.report__heading {
  font-size: var(--text-md);
  font-weight: 600;
}

.report__group {
  display: grid;
  gap: var(--space-2);
}

.report__group-title {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
}

.report__count {
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.report__scroll {
  overflow-x: auto;
}

.report__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.report__table th,
.report__table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
  text-align: left;
  vertical-align: top;
}

.report__table thead th {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  white-space: nowrap;
}

.report__table tbody th {
  font-weight: 400;
}

.report__finding {
  display: grid;
  gap: var(--space-1);
  min-width: 18rem;
}

.report__id {
  font-family: var(--font-mono);
  font-weight: 600;
  white-space: nowrap;
}

.report__message {
  color: var(--text-secondary);
}

.report__value {
  font-family: var(--font-mono);
}

.report__detail {
  color: var(--text-secondary);
}

.report__gates {
  display: grid;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-sm);
}

.report__gates li {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-3);
}

.report__gate-kind,
.report__basis {
  color: var(--text-secondary);
}

.report__small {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.report__actions {
  position: sticky;
  bottom: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin: 0 calc(-1 * var(--space-4));
  padding: var(--space-3) var(--space-4);
  background: var(--surface-raised);
  border-top: 1px solid var(--border-default);
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.report__said {
  flex-basis: 100%;
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}
</style>
