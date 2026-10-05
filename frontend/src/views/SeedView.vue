<script setup lang="ts">
// The Seed page, /seed (FR-F-1 to FR-F-5, AC-4, AC-5, ui-spec.md section 7, D-75). Before approval it
// says there is no approved Seed yet and points the way. Once a build is approved: the hero (Seed name,
// Approved, the iteration and the date), what this Seed does (its purpose), the tests conducted by
// phase, the iteration history, the known issues (only when the approved build has open findings:
// iteration 1, FR-F-4) and the three files with Preview and Download, and the zip (a "download" link
// beside Secure and Lock in Secure Repository, D-93). Everything comes from GET /api/seed, which the server assembles from the approved build; nothing on the page
// says which Knowledge file fed which Seed file (D-9).
import { computed, watch } from 'vue'
import BaseChip, { type ChipTone } from '../components/base/BaseChip.vue'
import HumanTag from '../components/base/HumanTag.vue'
import MarkdownPreview from '../components/intake/MarkdownPreview.vue'
import SeedFiles from '../components/seed/SeedFiles.vue'
import SeedHistory from '../components/seed/SeedHistory.vue'
import type { Severity, TestStatus } from '../report'
import { approvedOn, type SeedPhase } from '../seed'
import { useLabStore } from '../stores/lab'
import { useSeedStore } from '../stores/seed'

const lab = useLabStore()
const store = useSeedStore()

const approvedBuild = computed(() => lab.snapshot?.approval?.build_id ?? null)

watch(
  approvedBuild,
  (id) => {
    if (!id) store.clear()
    else if (store.seed?.approval.build_id !== id) void store.load()
  },
  { immediate: true },
)

const seed = computed(() => (approvedBuild.value && store.seed?.approval.build_id === approvedBuild.value ? store.seed : null))

/** Where to go before approval, by what the lab holds now. */
const nextStep = computed(() => {
  const snapshot = lab.snapshot
  const current = snapshot?.builds.find((b) => b.iteration === snapshot.iteration) ?? null
  if (current?.status === 'completed') {
    return { text: `Iteration ${current.iteration}'s report is ready: approve it there to make it the Seed.`, to: `/review/${current.iteration}`, label: `Go to the iteration ${current.iteration} report` }
  }
  if (current?.status === 'running') {
    return { text: `Iteration ${current.iteration} is still building. Approve it from its report once it completes.`, to: `/build/${current.iteration}`, label: 'Go to the build' }
  }
  return { text: 'Build the Seed from Knowledge first, then approve it from its report.', to: '/knowledge', label: 'Go to Knowledge' }
})

const date = computed(() => approvedOn(seed.value?.approval.approved_at ?? null))

const RESULT: Record<SeedPhase['result'], ChipTone> = { passed: 'positive', findings: 'warning', failed: 'negative', incomplete: 'neutral' }
const STATUS: Record<TestStatus, string> = { pass: 'passed', warn: 'warned', fail: 'failed', not_run: 'not run' }
const SEVERITY: Record<Severity, [string, ChipTone]> = {
  high: ['High', 'negative'],
  medium: ['Medium', 'warning'],
  low: ['Low', 'neutral'],
  advisory: ['Advisory', 'neutral'],
}

function resultLabel(phase: SeedPhase): string {
  if (phase.result === 'findings') return `Findings: ${phase.findings.length}`
  if (phase.result === 'failed') return 'Failed'
  if (phase.result === 'incomplete') return 'Incomplete'
  return 'Passed'
}

const testsLine = computed(() => {
  const c = seed.value?.counts
  if (!c) return ''
  const parts = [`${c.pass} passed`]
  if (c.warn) parts.push(`${c.warn} warned`)
  if (c.fail) parts.push(`${c.fail} failed`)
  if (c.not_run) parts.push(`${c.not_run} not run`)
  return `${c.tests} tests in ${c.phases} phases: ${parts.join(', ')}.`
})

const issuesLine = computed(() => {
  const s = seed.value
  if (!s) return ''
  const n = s.known_issues.length
  return `Approved at iteration ${s.approval.iteration} with ${n} open ${n === 1 ? 'finding' : 'findings'}. Each is also listed under Known issues in every Seed file.`
})
</script>

<template>
  <div class="seed" data-test="seed">
    <p v-if="!lab.snapshot || (approvedBuild && !seed && store.loading)" class="seed__note" data-test="seed-loading">Loading the Seed</p>

    <section v-else-if="!approvedBuild" class="seed__empty" data-test="seed-empty">
      <h1>Seed</h1>
      <p class="seed__note" data-test="seed-empty-reason">No Seed is approved yet, so there are no Seed files to show.</p>
      <p class="seed__note" data-test="seed-next">{{ nextStep.text }}</p>
      <RouterLink :to="nextStep.to" class="seed__link" data-test="seed-next-link">{{ nextStep.label }}</RouterLink>
    </section>

    <section v-else-if="!seed" class="seed__empty">
      <h1>Seed</h1>
      <p class="seed__note" role="alert" data-test="seed-error">{{ store.error || 'The approved Seed could not be loaded.' }}</p>
      <button type="button" class="seed__retry" @click="store.load()">Try again</button>
    </section>

    <template v-else>
      <header class="seed__hero" data-test="seed-hero">
        <div class="seed__title-row">
          <h1 data-test="seed-name">{{ seed.seed_name }}</h1>
          <BaseChip tone="positive" class="seed__approved" data-test="seed-approved">Approved</BaseChip>
        </div>
        <p class="seed__meta" data-test="seed-approval">
          <span>Approved at iteration {{ seed.approval.iteration }}<HumanTag :iteration="seed.approval.iteration" /><template v-if="date">, on {{ date }}</template>.</span>
          <span class="seed__fingerprint">Intake fingerprint {{ seed.fingerprint }}</span>
        </p>
      </header>

      <section class="seed__section" aria-labelledby="seed-purpose" data-test="seed-purpose">
        <h2 id="seed-purpose">What this Seed does</h2>
        <MarkdownPreview v-if="seed.purpose.text" compact :text="seed.purpose.text" label="What this Seed does" />
        <p v-else class="seed__note">No purpose is stated for this Seed.</p>
      </section>

      <section class="seed__section" aria-labelledby="seed-tests" data-test="seed-tests">
        <h2 id="seed-tests">Tests conducted</h2>
        <p class="seed__lead">
          {{ testsLine }} Verdict <BaseChip :tone="seed.verdict.tone" data-test="seed-verdict">{{ seed.verdict.label }}</BaseChip>
          <RouterLink :to="`/review/${seed.approval.iteration}`" class="seed__inline-link">Read the full report</RouterLink>
        </p>
        <div class="seed__scroll">
          <table class="seed__table">
            <caption class="visually-hidden">Tests conducted, by phase, with their results</caption>
            <thead>
              <tr>
                <th scope="col">Phase</th>
                <th scope="col">Tests</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="phase in seed.phases" :key="phase.id" :data-phase="phase.id" data-test="seed-phase">
                <th scope="row">{{ phase.index }}. {{ phase.name }}</th>
                <td>
                  <ul class="seed__tests">
                    <li v-for="test in phase.tests" :key="test.id" :data-status="test.status">
                      <span class="seed__id">{{ test.id }}</span> {{ test.name }}<span v-if="test.status !== 'pass'" class="seed__status">, {{ STATUS[test.status] }}</span>
                    </li>
                  </ul>
                </td>
                <td>
                  <BaseChip :tone="RESULT[phase.result]" data-test="seed-phase-result">{{ resultLabel(phase) }}</BaseChip>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="seed__section" aria-labelledby="seed-history" data-test="seed-history-section">
        <h2 id="seed-history">Iteration history</h2>
        <SeedHistory :items="seed.history" />
      </section>

      <section v-if="seed.known_issues.length" class="seed__section" aria-labelledby="seed-issues" data-test="seed-known-issues">
        <h2 id="seed-issues">Known issues</h2>
        <p class="seed__lead">{{ issuesLine }}</p>
        <div class="seed__scroll">
          <table class="seed__table">
            <caption class="visually-hidden">Known issues: the open findings of the approved build</caption>
            <thead>
              <tr>
                <th scope="col">Finding</th>
                <th scope="col">Category</th>
                <th scope="col">Severity</th>
                <th scope="col">Expected</th>
                <th scope="col">Shown</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="issue in seed.known_issues" :key="issue.id" :data-issue="issue.id" data-test="known-issue">
                <th scope="row">
                  <span class="seed__id">{{ issue.id }}</span>
                  <span class="seed__message">{{ issue.message }}</span>
                </th>
                <td>{{ issue.category }}</td>
                <td>
                  <BaseChip :tone="SEVERITY[issue.severity][1]">{{ SEVERITY[issue.severity][0] }}</BaseChip>
                </td>
                <td class="seed__value">{{ issue.expected }}</td>
                <td class="seed__value">{{ issue.shown }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="seed__section" aria-labelledby="seed-files" data-test="seed-files-section">
        <h2 id="seed-files">Seed files</h2>
        <SeedFiles :seed="seed" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.seed {
  display: grid;
  gap: var(--space-6);
  max-width: 1200px;
  padding: var(--space-10) var(--space-8) var(--space-12);
}

.seed__empty {
  display: grid;
  gap: var(--space-3);
  justify-items: start;
}

h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
}

h2 {
  font-size: var(--text-lg);
  font-weight: 600;
}

.seed__note {
  max-width: 60ch;
  color: var(--text-secondary);
}

.seed__link,
.seed__inline-link {
  font-size: var(--text-sm);
  font-weight: 600;
}

.seed__retry {
  padding: 0;
  border: 0;
  background: none;
  color: var(--link);
  font: inherit;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

.seed__hero {
  display: grid;
  gap: var(--space-2);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-default);
}

.seed__title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.seed__approved {
  font-size: var(--text-sm);
}

.seed__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1) var(--space-4);
  color: var(--text-secondary);
}

.seed__fingerprint {
  color: var(--text-secondary);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
}

.seed__section {
  display: grid;
  gap: var(--space-3);
}

.seed__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1) var(--space-2);
  font-size: var(--text-sm);
}

.seed__scroll {
  overflow-x: auto;
}

.seed__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.seed__table th,
.seed__table td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
  text-align: left;
  vertical-align: top;
}

.seed__table thead th {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  white-space: nowrap;
}

.seed__table tbody th {
  font-weight: 400;
  white-space: nowrap;
}

.seed__tests {
  display: grid;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.seed__id {
  font-family: var(--font-sans);
  font-weight: 600;
  white-space: nowrap;
}

.seed__status {
  color: var(--text-secondary);
}

.seed__message {
  display: block;
  min-width: 18rem;
  color: var(--text-secondary);
  white-space: normal;
}

.seed__value {
  font-family: var(--font-sans);
}
</style>
