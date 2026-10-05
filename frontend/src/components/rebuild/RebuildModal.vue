<script setup lang="ts">
// The rebuild modal (FR-RB-1 to FR-RB-5, ui-spec.md section 6, D-19, D-70). A large modal over any
// page, opened by Reject on the current iteration's report (D-81). Its body is the Knowledge editor (Edit / Preview,
// mic) for observer-feedback-iteration-<n>.md; the header's tablist switches between the feedback alone
// and the feedback beside iteration n's report or dashboard, each pane scrolling on its own. The
// embedded report has no actions, and a finding id in it shows that finding on the embedded
// dashboard, outlined, instead of leaving the modal; the embedded dashboard holds its drill path in
// the store, so the page URL never changes. Start Rebuild stays disabled, with its reason, while the
// feedback is empty. The modal owns the keyboard (D-47): focus is trapped, Escape closes it and
// focus returns to Rebuild; a backdrop click does nothing (D-38); Shift+F (Prefill) works inside it.
import { computed, ref, useId } from 'vue'
import { useRouter } from 'vue-router'
import { DASHBOARD_ID } from '../../dashboard/api'
import { dashboardFindings } from '../../report'
import { useRebuildStore, type RebuildView } from '../../stores/rebuild'
import { useReportsStore } from '../../stores/reports'
import BaseButton from '../base/BaseButton.vue'
import BaseModal from '../base/BaseModal.vue'
import DashboardView from '../dashboard/DashboardView.vue'
import MarkdownEditor from '../intake/MarkdownEditor.vue'
import BuildReport from '../report/BuildReport.vue'

const rebuild = useRebuildStore()
const reports = useReportsStore()
const router = useRouter()
const uid = useId()

const VIEWS: { id: RebuildView; label: string }[] = [
  { id: 'feedback', label: 'Feedback' },
  { id: 'report', label: 'Feedback + Report' },
  { id: 'dashboard', label: 'Feedback + Dashboard' },
]

const next = computed(() => rebuild.rejected + 1)
const placeholder = computed(
  () =>
    `Write what iteration ${next.value} should change. Cover the data and its correctness, the style, the choice of charts, ` +
    'the latency, and anything else you noticed. Cite finding ids such as N-1 or V-3 where you can.',
)
const empty = computed(() => `Start Rebuild needs observer feedback. Write what iteration ${next.value} should change first.`)

const tabId = (view: RebuildView) => `${uid}-tab-${view}`
const panelId = `${uid}-panel`
const reasonId = `${uid}-reason`
const tabs = ref<HTMLButtonElement[]>([])

function select(view: RebuildView, focus = false): void {
  rebuild.setView(view)
  if (focus) tabs.value[VIEWS.findIndex((v) => v.id === view)]?.focus()
}

function onTabKeydown(event: KeyboardEvent, index: number): void {
  const last = VIEWS.length - 1
  const next = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: last }[event.key]
  if (next === undefined) return
  event.preventDefault()
  select(VIEWS[(next + VIEWS.length) % VIEWS.length].id, true)
}

const report = computed(() => (rebuild.buildId ? (reports.reports.get(rebuild.buildId) ?? null) : null))
const shownFinding = computed(() => {
  const id = rebuild.finding
  return id && report.value ? (dashboardFindings(report.value).find((f) => f.id === id) ?? null) : null
})
const highlight = computed(() => shownFinding.value?.panels ?? [])

const disabled = computed(() => rebuild.empty || rebuild.busy)

async function start(): Promise<void> {
  if (disabled.value) return
  const started = await rebuild.start()
  if (started) await router.push({ name: 'build', params: { iteration: String(started.iteration) } })
}
</script>

<template>
  <BaseModal :open="rebuild.open" title="Rebuild Seed: observer feedback" size="lg" name="rebuild" flush @close="rebuild.close()">
    <template #controls>
      <div class="views" role="tablist" aria-label="View" data-test="rebuild-views">
        <button
          v-for="(view, index) in VIEWS"
          :id="tabId(view.id)"
          :key="view.id"
          ref="tabs"
          type="button"
          role="tab"
          class="views__tab"
          :aria-selected="rebuild.view === view.id ? 'true' : 'false'"
          :aria-controls="panelId"
          :tabindex="rebuild.view === view.id ? 0 : -1"
          :data-view="view.id"
          @click="select(view.id)"
          @keydown="onTabKeydown($event, index)"
        >
          {{ view.label }}
        </button>
      </div>
    </template>

    <div
      :id="panelId"
      class="rebuild"
      :class="{ 'rebuild--split': rebuild.view !== 'feedback' }"
      role="tabpanel"
      :aria-labelledby="tabId(rebuild.view)"
      data-test="rebuild"
    >
      <section class="rebuild__feedback" aria-label="Observer feedback" data-test="rebuild-feedback">
        <div class="rebuild__meta">
          <span class="caps-label">Name</span>
          <span class="rebuild__name" data-test="feedback-name">{{ rebuild.name }}</span>
          <span class="rebuild__hint">Kept with the build when the rebuild starts, and routed into the initiation files.</span>
        </div>
        <MarkdownEditor :text="rebuild.draft" :label="`Content of ${rebuild.name}`" :placeholder="placeholder" @input="rebuild.draft = $event" />
      </section>

      <section v-if="rebuild.view === 'report' && rebuild.build" class="rebuild__reference" :aria-label="`Iteration ${rebuild.rejected} report`" data-test="rebuild-report">
        <BuildReport :build="rebuild.build" :heading-level="3" :actions="false" finding-links="event" @finding="rebuild.showFinding" />
      </section>

      <section v-if="rebuild.view === 'dashboard'" class="rebuild__reference" :aria-label="`Iteration ${rebuild.rejected} dashboard`" data-test="rebuild-dashboard">
        <p v-if="shownFinding" class="rebuild__finding" data-test="rebuild-finding">
          <span>
            Showing {{ shownFinding.id }} on {{ (shownFinding.panel_titles ?? []).join(', ') }}. <span class="rebuild__message">{{ shownFinding.message }}</span>
          </span>
          <BaseButton @click="rebuild.finding = null">Clear highlight</BaseButton>
        </p>
        <DashboardView
          :dashboard-id="DASHBOARD_ID"
          :iteration="rebuild.rejected"
          :drill="rebuild.drill"
          :heading-level="3"
          :highlight="highlight"
          @navigate="rebuild.navigate"
          @back="rebuild.navigate"
          @invalid-drill="rebuild.navigate('')"
        />
      </section>
    </div>

    <template #footer>
      <p class="rebuild__status" :class="{ 'rebuild__status--error': rebuild.error }" :role="rebuild.error ? 'alert' : undefined" data-test="rebuild-status">
        <span v-if="rebuild.error">{{ rebuild.error }}</span>
        <span v-else-if="rebuild.empty" :id="reasonId">{{ empty }}</span>
        <span v-else-if="rebuild.busy">Starting the rebuild</span>
      </p>
      <BaseButton data-action="cancel" @click="rebuild.close()">Cancel</BaseButton>
      <BaseButton
        variant="primary"
        :aria-disabled="disabled ? 'true' : undefined"
        :aria-describedby="rebuild.empty ? reasonId : undefined"
        data-action="start-rebuild"
        @click="start"
      >
        Start Rebuild
      </BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.views {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-sunken);
}

.views__tab {
  min-height: 28px;
  padding: 0 var(--space-3);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
}

.views__tab[aria-selected='true'] {
  background: var(--surface-raised);
  border-color: var(--border-default);
  color: var(--text-primary);
  font-weight: 600;
}

.rebuild {
  display: grid;
  flex: 1;
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
}

.rebuild--split {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.rebuild__feedback {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--surface-raised);
}

.rebuild__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2) var(--space-3);
  padding: var(--space-3) var(--space-6) var(--space-2);
}

.rebuild__name {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.rebuild__hint {
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

.rebuild__reference {
  display: grid;
  align-content: start;
  gap: var(--space-3);
  min-height: 0;
  overflow: auto;
  padding: var(--space-4);
  border-left: 1px solid var(--border-subtle);
  background: var(--surface-base);
}

.rebuild__finding {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2) var(--space-3);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  font-size: var(--text-sm);
}

.rebuild__message {
  color: var(--text-secondary);
}

.rebuild__status {
  flex: 1;
  align-self: center;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.rebuild__status--error {
  color: var(--status-negative);
}
</style>
