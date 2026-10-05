<script setup lang="ts">
// The build report (FR-R-1, FR-R-2, FR-R-4, ui-spec.md section 4, D-64, D-65): verdict and counts,
// findings grouped Numeric, Visual, Latency and Boundary, every test, the auto-resolved gates and
// the simulated usage, with View Agentic Solution (the dashboard, D-91), Reject, Approve and Initiate
// QUAD SI Review Protocol (shown only, D-92). Everything comes from the report
// the server assembles from the build's kept events. Embeddable: the Build page, the Review page
// and the rebuild modal's "Feedback + Report" view each place it, with their own heading level, and
// may leave the actions out. A dashboard finding's id links to the dashboard at All products with
// that finding's panels highlighted (`finding=<id>` in the URL); with `finding-links="event"` (the
// rebuild modal) it is a button that emits the id instead, so the page URL never changes (D-70).
// Reject (every iteration, passed or not, D-81) opens the rebuild modal for observer feedback, whose
// Start Rebuild starts the next iteration; once that has started, the report keeps Reject, unavailable,
// and says so with a link to it (D-67). Approve (FR-R-4, D-73, D-75) approves the build
// and opens the Seed page; it is offered on the current iteration's completed build, once, with no
// build running, and says why not otherwise. Once the Seed is approved, the footer says so and links
// to the Seed page instead.
// From iteration 2 on the report adds "Changes since iteration n - 1" (FR-R-3, D-69, D-81), the
// feedback quoted through the Preview's sanitising renderer (D-40). Every report shows the Seed files'
// context footprint when planted, against the 20% budget (D-82). An iteration after the first carries
// the Human tag beside its Iteration fact (D-90).
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DASHBOARD_ID } from '../../dashboard/api'
import type { Finding, Report, Severity, TestStatus } from '../../report'
import { clock } from '../../stepper'
import { useReportsStore } from '../../stores/reports'
import { rebuiltFrom, useRebuildStore } from '../../stores/rebuild'
import { useSeedStore } from '../../stores/seed'
import { useLabStore, type Build } from '../../stores/lab'
import BaseButton from '../base/BaseButton.vue'
import BaseChip, { type ChipTone } from '../base/BaseChip.vue'
import HumanTag from '../base/HumanTag.vue'
import MarkdownPreview from '../intake/MarkdownPreview.vue'

const props = withDefaults(defineProps<{ build: Build; headingLevel?: 1 | 2 | 3; actions?: boolean; findingLinks?: 'route' | 'event' }>(), {
  headingLevel: 2,
  actions: true,
  findingLinks: 'route',
})
const emit = defineEmits<{ finding: [id: string] }>()

const reports = useReportsStore()
const rebuild = useRebuildStore()
const seedStore = useSeedStore()
const lab = useLabStore()
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
    { label: 'Iteration', value: String(r.iteration) },
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

const said = ref('')

/** Why Reject cannot open now, or null (D-81). */
const rebuildWhy = computed(() => rebuild.unavailable(props.build))
/** The next iteration was rebuilt from this report, and no Seed is approved yet. */
const rebuilt = computed(() => !lab.snapshot?.approval && (lab.snapshot?.builds.some((b) => b.iteration > props.build.iteration) ?? false))
const previous = computed(() => props.build.iteration - 1)

function openRebuild(): void {
  if (rebuildWhy.value) said.value = rebuildWhy.value
  else rebuild.show(props.build)
}

const changes = computed(() => report.value?.changes ?? null)
const STATUS: Record<'resolved' | 'open', [string, ChipTone]> = { resolved: ['Resolved', 'positive'], open: ['Open', 'warning'] }
const segmentList = (numbers: number[]) => `${numbers.length === 1 ? 'segment' : 'segments'} ${numbers.join(', ')}`

const changesSummary = computed(() => {
  const c = changes.value
  if (!c) return ''
  if (!c.findings.length) return `Iteration ${previous.value} had no findings, so there were none to resolve.`
  const open = c.open ? `, ${c.open} still open` : ''
  return `${c.resolved} of ${c.findings.length} iteration ${previous.value} findings resolved${open}.`
})

const context = computed(() => report.value?.context ?? null)
const percent = (share: number) => `${share.toFixed(1)}%`
const LAYER_TITLE: Record<string, string> = { core: 'Core', adaptation: 'Adaptation', protection: 'Protection' }
const contextSummary = computed(() => {
  const c = context.value
  if (!c) return ''
  const taken = `Planted together, the three Seed files take ${percent(c.share)} of the model's context window`
  return c.within
    ? `${taken}, within the ${c.budget}% budget, so ${percent(100 - c.share)} stays free for the work.`
    : `${taken}, over the ${c.budget}% budget.`
})
const contextLabel = computed(() => {
  const c = context.value
  if (!c) return ''
  const parts = c.layers.map((layer) => `${layer.name} ${percent(layer.share)}`).join(', ')
  return `Context window: ${parts}; ${percent(c.share)} in all, against a ${c.budget}% budget.`
})

function updateLine(update: NonNullable<Report['changes']>['updates'][number]): string {
  const lines = `${update.lines_added} ${update.lines_added === 1 ? 'line' : 'lines'}`
  const created = update.created ? ' (a new section)' : ''
  return `${update.file}, ${update.section}${created}: +${lines} (${segmentList(update.segments)})`
}

const keptLine = computed(() => {
  const c = changes.value
  if (!c || !c.kept.length) return ''
  const fits = c.kept.length === 1 ? 'it fits' : 'they fit'
  const list = segmentList(c.kept)
  return `${list[0].toUpperCase()}${list.slice(1)} stayed in ${c.feedback?.name ?? 'the feedback file'} only: ${fits} no Ensemble file.`
})

const approval = computed(() => lab.snapshot?.approval ?? null)
/** Why Approve cannot act now, or null; asked only before the Seed is approved. */
const approveWhy = computed(() => (approval.value ? null : seedStore.unavailable(props.build)))
const approvedLine = computed(() => {
  const a = approval.value
  if (!a) return ''
  return a.build_id === props.build.id ? 'This build is the approved Seed.' : `The Seed was approved at iteration ${a.iteration}.`
})

async function approve(): Promise<void> {
  if (approveWhy.value) {
    said.value = approveWhy.value
    return
  }
  said.value = ''
  const refused = await seedStore.approve(props.build)
  if (refused) said.value = refused
  else await router.push({ name: 'seed' })
}

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
          <dd data-test="report-fact">{{ fact.value }}<HumanTag v-if="fact.label === 'Iteration'" :iteration="build.iteration" /></dd>
        </div>
      </dl>

      <section v-if="changes" class="report__section" :aria-labelledby="`${ids}-changes`" data-test="report-changes">
        <component :is="h(1)" :id="`${ids}-changes`" class="report__heading">Changes since iteration {{ previous }}</component>
        <p class="report__lead" data-test="changes-summary">{{ changesSummary }}</p>
        <div v-if="changes.findings.length" class="report__scroll">
          <table class="report__table">
            <caption class="visually-hidden">Iteration {{ previous }} findings and whether iteration {{ build.iteration }} resolved them</caption>
            <thead>
              <tr>
                <th scope="col">Finding</th>
                <th scope="col">Panel</th>
                <th scope="col">Category</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="change in changes.findings" :key="change.id" :data-finding="change.id" data-test="change">
                <th scope="row">
                  <div class="report__finding">
                    <span class="report__id">{{ change.id }}</span>
                    <span v-if="change.message" class="report__message">{{ change.message }}</span>
                  </div>
                </th>
                <td>{{ change.panel_titles.join(', ') }}</td>
                <td>{{ change.category }}</td>
                <td>
                  <BaseChip :tone="STATUS[change.status][1]" data-test="change-status">{{ STATUS[change.status][0] }}</BaseChip>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <template v-if="changes.feedback">
          <component :is="h(2)" class="report__group-title">Observer feedback</component>
          <blockquote class="report__quote" data-test="changes-feedback">
            <MarkdownPreview compact :text="changes.feedback.content" :label="`Observer feedback, ${changes.feedback.name}`" />
          </blockquote>
          <p class="report__aside">From {{ changes.feedback.name }}, kept with the build.</p>
        </template>
        <template v-if="changes.updates.length || changes.kept.length">
          <component :is="h(2)" class="report__group-title">Knowledge files updated from the feedback</component>
          <ul class="report__updates" data-test="changes-updates">
            <li v-for="update in changes.updates" :key="`${update.file}-${update.section}`">{{ updateLine(update) }}</li>
            <li v-if="changes.kept.length">{{ keptLine }}</li>
          </ul>
        </template>
      </section>

      <section v-if="context" class="report__section" :aria-labelledby="`${ids}-context`" data-test="report-context">
        <component :is="h(1)" :id="`${ids}-context`" class="report__heading">Context footprint when planted</component>
        <p class="report__lead" data-test="context-summary">
          {{ contextSummary }}
          <BaseChip :tone="context.within ? 'positive' : 'warning'" data-test="context-verdict">{{ context.within ? 'Within budget' : 'Over budget' }}</BaseChip>
        </p>
        <div class="context" role="img" :aria-label="contextLabel" data-test="context-bar">
          <div class="context__bar">
            <span
              v-for="layer in context.layers"
              :key="layer.name"
              class="context__part"
              :class="`context__part--${layer.role}`"
              :style="{ width: `${layer.share}%` }"
            />
            <span class="context__budget" :style="{ left: `${context.budget}%` }" />
          </div>
          <div class="context__scale" aria-hidden="true">
            <span>0%</span>
            <span class="context__budget-label" :style="{ left: `${context.budget}%` }">Budget {{ context.budget }}%</span>
            <span>100% of the context window</span>
          </div>
        </div>
        <div class="report__scroll">
          <table class="report__table context__table">
            <caption class="visually-hidden">Each Seed file's share of the context window</caption>
            <thead>
              <tr>
                <th scope="col">Seed file</th>
                <th scope="col">Tokens</th>
                <th scope="col">Share of the window</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="layer in context.layers" :key="layer.name" data-test="context-layer">
                <th scope="row">
                  <span class="context__swatch" :class="`context__part--${layer.role}`" aria-hidden="true" />
                  <span class="report__id">{{ layer.name }}</span>
                  <span class="report__message">{{ LAYER_TITLE[layer.role] ?? layer.role }}</span>
                </th>
                <td class="report__value">{{ count(layer.tokens) }}</td>
                <td class="report__value" data-test="context-share">{{ percent(layer.share) }}</td>
              </tr>
              <tr class="context__total">
                <th scope="row">All three, planted together</th>
                <td class="report__value">{{ count(context.tokens) }}</td>
                <td class="report__value" data-test="context-total">{{ percent(context.share) }} of {{ context.budget }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="report__small" data-test="context-note">
          Simulated: a {{ count(context.window) }}-token context window (assuming limited one thread build for demonstration purposes), at about four bytes a token.
        </p>
      </section>

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
                      <button
                        v-if="!finding.advisory && findingLinks === 'event'"
                        type="button"
                        class="report__id report__link"
                        data-test="finding-link"
                        @click="emit('finding', finding.id)"
                      >
                        {{ finding.id }}<span class="visually-hidden">: show on the dashboard beside the feedback</span>
                      </button>
                      <RouterLink v-else-if="!finding.advisory" :to="findingLink(finding)" class="report__id" data-test="finding-link">
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
      <BaseButton data-action="dashboard" @click="viewDashboard">View Agentic Solution</BaseButton>
      <BaseButton
        :aria-disabled="rebuildWhy ? 'true' : undefined"
        :aria-describedby="rebuildWhy ? `${ids}-why-rebuild` : undefined"
        data-action="rebuild"
        @click="openRebuild"
      >
        Reject
      </BaseButton>
      <BaseButton
        v-if="!approval"
        variant="primary"
        :aria-disabled="approveWhy || seedStore.approving ? 'true' : undefined"
        :aria-describedby="approveWhy ? `${ids}-why-approve` : undefined"
        data-action="approve"
        @click="approve"
      >
        Approve
      </BaseButton>
      <!-- Shown only: pressing it does nothing (D-92). -->
      <BaseButton data-action="quad-si">Initiate QUAD SI Review Protocol</BaseButton>
      <span class="report__footnote" data-test="quad-si-note">* Assuming default 10 cycles</span>
      <span v-if="rebuildWhy" :id="`${ids}-why-rebuild`" class="visually-hidden">{{ rebuildWhy }}</span>
      <span v-if="approveWhy" :id="`${ids}-why-approve`" class="visually-hidden">{{ approveWhy }}</span>
      <p v-if="approval" class="report__rebuilt" data-test="report-approved">
        {{ approvedLine }} <RouterLink to="/seed">Go to the Seed</RouterLink>
      </p>
      <p v-if="rebuilt" class="report__rebuilt" data-test="report-rebuilt">
        {{ rebuiltFrom(build) }} <RouterLink :to="`/build/${build.iteration + 1}`">Go to iteration {{ build.iteration + 1 }}</RouterLink>
      </p>
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
  font-family: var(--font-sans);
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
  font-family: var(--font-sans);
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
  font-family: var(--font-sans);
  font-weight: 600;
  white-space: nowrap;
}

.report__message {
  color: var(--text-secondary);
}

.report__value {
  font-family: var(--font-sans);
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

.report__footnote {
  color: var(--text-muted);
  font-size: calc(var(--text-xs) - 1px);
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

.report__lead {
  font-size: var(--text-sm);
}

.report__link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--link);
  font-size: inherit;
  text-align: left;
  text-decoration: underline;
  cursor: pointer;
}

.report__quote {
  margin: 0;
  padding: var(--space-2) var(--space-4);
  border-left: 3px solid var(--border-strong);
  background: var(--surface-sunken);
}

.report__updates {
  display: grid;
  gap: var(--space-1);
  margin: 0;
  padding-left: var(--space-5);
  font-size: var(--text-sm);
}

.report__rebuilt {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.context {
  display: grid;
  gap: var(--space-1);
}

.context__bar {
  position: relative;
  display: flex;
  height: 20px;
  overflow: visible;
  background: var(--surface-sunken);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
}

.context__part {
  display: block;
  height: 100%;
}

.context__part--core {
  background: var(--chart-series-1);
}

.context__part--adaptation {
  background: var(--chart-series-2);
}

.context__part--protection {
  background: var(--chart-series-3);
}

.context__budget {
  position: absolute;
  top: -4px;
  bottom: -4px;
  border-left: 2px dashed var(--text-secondary);
}

.context__scale {
  position: relative;
  display: flex;
  justify-content: space-between;
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

.context__budget-label {
  position: absolute;
  transform: translateX(-50%);
  font-weight: 600;
  white-space: nowrap;
}

.context__swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: var(--space-2);
  border-radius: 0;
  vertical-align: baseline;
}

.context__table tbody th {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-1) var(--space-2);
}

.context__total th,
.context__total td {
  font-weight: 600;
}

.report__said {
  flex-basis: 100%;
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}
</style>
