<script setup lang="ts">
// The demo controller (ui-spec.md section 8, FR-DC-1, FR-DC-2, D-15): a hidden operator panel,
// bottom right, toggled with Shift+O. Every action has a button that lists its shortcut, and
// the shortcuts work with the panel hidden. Shortcuts are ignored where text is typed and while
// a modal is open, unless the action belongs to that modal (D-47). Load sample on a filled
// intake, Clear and Reset ask first (OQ-17).
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseConfirm from '../components/base/BaseConfirm.vue'
import { plural, SPEEDS, useDemoStore, type Speed } from '../stores/demo'
import { useLabStore } from '../stores/lab'
import { shortcutAction, shortcutOf, type DemoAction } from './shortcuts'

const demo = useDemoStore()
const lab = useLabStore()
const route = useRoute()
const router = useRouter()
const uid = useId()

interface Row {
  action: DemoAction
  label: string
}

interface Group {
  title: string
  rows: Row[]
  speed?: boolean
  note?: string
}

const GROUPS: Group[] = [
  {
    title: 'Knowledge',
    rows: [
      { action: 'sample', label: 'Load sample Seed' },
      { action: 'clear', label: 'Clear Knowledge' },
      { action: 'start', label: 'Start Build' },
    ],
  },
  {
    title: 'Build',
    speed: true,
    rows: [
      { action: 'skipPhase', label: 'Skip phase' },
      { action: 'skipEnd', label: 'Skip to end' },
    ],
    note: 'Speed paces builds and is kept across Reset. Skip works while a build runs.',
  },
  {
    title: 'Rebuild',
    rows: [{ action: 'prefill', label: 'Prefill feedback' }],
    note: 'Fills the rebuild modal while it is open.',
  },
  {
    title: 'Lab',
    rows: [
      { action: 'reset', label: 'Reset to start' },
      { action: 'theme', label: 'Toggle theme' },
    ],
  },
]

const SPEED_ACTION: Record<Speed, DemoAction> = { 1: 'speed1', 2: 'speed2', 4: 'speed4' }

// Panel: focus moves in when it opens and goes back when it closes, if it was still inside.
const panel = ref<HTMLElement | null>(null)
let opener: HTMLElement | null = null

async function open(): Promise<void> {
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
  demo.visible = true
  await nextTick()
  panel.value?.focus()
}

function close(): void {
  const inside = panel.value?.contains(document.activeElement) ?? false
  demo.visible = false
  const target = opener
  opener = null
  if (inside && target?.isConnected) target.focus()
}

// Confirms
type Ask = 'sample' | 'clear' | 'reset'
const asking = ref<Ask | null>(null)
const askCount = ref(0)

const confirmText = computed(() => {
  const files = plural(askCount.value, 'knowledge file')
  switch (asking.value) {
    case 'sample':
      return {
        title: 'Load sample Seed?',
        body: `This replaces all ${files} with the sample Seed. Unsaved changes are lost.`,
        ok: 'Replace and load',
      }
    case 'clear':
      return { title: 'Clear Knowledge?', body: `This deletes all ${files}. It cannot be undone.`, ok: 'Delete all' }
    default:
      return {
        title: 'Reset to start?',
        body: 'This deletes all knowledge files and builds and returns to the Knowledge page. Speed and theme stay as they are.',
        ok: 'Reset',
      }
  }
})

function ask(kind: Ask): void {
  askCount.value = lab.files.length
  asking.value = kind
}

async function toKnowledge(): Promise<void> {
  if (route.name !== 'knowledge') await router.push({ name: 'knowledge' })
}

async function confirm(): Promise<void> {
  const kind = asking.value
  asking.value = null
  if (kind === 'sample' && (await demo.loadSample(true))) await toKnowledge()
  if (kind === 'clear') await demo.clearIntake()
  if (kind === 'reset' && (await demo.reset())) await router.push({ name: 'knowledge' })
}

async function run(action: DemoAction): Promise<void> {
  if (action === 'toggle') {
    if (demo.visible) close()
    else await open()
    return
  }
  const why = demo.unavailable(action)
  if (why) {
    demo.status = why
    return
  }
  switch (action) {
    case 'sample':
      if (lab.files.length) ask('sample')
      else if (await demo.loadSample(false)) await toKnowledge()
      return
    case 'clear':
      if (lab.files.length) ask('clear')
      else demo.status = 'Knowledge is already empty.'
      return
    case 'reset':
      ask('reset')
      return
    case 'start': {
      const build = await demo.startBuild()
      if (build) await router.push({ name: 'build', params: { iteration: String(build.iteration) } })
      return
    }
    case 'speed1':
    case 'speed2':
    case 'speed4':
      await demo.setSpeed(Number(action.slice(5)) as Speed)
      return
    case 'skipPhase':
      await demo.skip('phase')
      return
    case 'skipEnd':
      await demo.skip('build')
      return
    case 'prefill':
      await demo.prefill()
      return
    case 'theme':
      demo.theme()
      return
  }
}

function onKeydown(event: KeyboardEvent): void {
  const action = shortcutAction(event)
  if (!action) return
  event.preventDefault()
  void run(action)
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  void demo.loadSpeed()
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

const whyId = (action: DemoAction) => `${uid}-why-${action}`
</script>

<template>
  <aside
    v-if="demo.visible"
    ref="panel"
    class="demo"
    aria-label="Demo controller"
    tabindex="-1"
    data-test="demo-panel"
    @keydown.esc.stop="close"
  >
    <header class="demo__header">
      <h2 class="caps-label">Demo</h2>
      <button type="button" class="demo__close" aria-label="Hide demo controller" data-test="demo-close" @click="close">
        <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
          <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      </button>
    </header>

    <section v-for="group in GROUPS" :key="group.title" class="demo__group" :aria-label="group.title">
      <h3 class="demo__title">{{ group.title }}</h3>
      <div v-if="group.speed" class="demo__speeds" role="group" aria-label="Speed">
        <button
          v-for="speed in SPEEDS"
          :key="speed"
          type="button"
          class="demo__action demo__speed"
          :aria-pressed="demo.speed === speed ? 'true' : 'false'"
          :data-action="SPEED_ACTION[speed]"
          @click="run(SPEED_ACTION[speed])"
        >
          <span>{{ speed }}x</span>
          <kbd>{{ shortcutOf(SPEED_ACTION[speed]).label }}</kbd>
        </button>
      </div>
      <button
        v-for="row in group.rows"
        :key="row.action"
        type="button"
        class="demo__action"
        :aria-disabled="demo.unavailable(row.action) ? 'true' : undefined"
        :aria-describedby="demo.unavailable(row.action) ? whyId(row.action) : undefined"
        :data-action="row.action"
        @click="run(row.action)"
      >
        <span>{{ row.label }}</span>
        <kbd>{{ shortcutOf(row.action).label }}</kbd>
        <span v-if="demo.unavailable(row.action)" :id="whyId(row.action)" class="visually-hidden">
          {{ demo.unavailable(row.action) }}
        </span>
      </button>
      <p v-if="group.note" class="demo__note">{{ group.note }}</p>
    </section>

    <p class="demo__status" role="status" data-test="demo-status">{{ demo.status }}</p>
    <p class="demo__note">{{ shortcutOf('toggle').label }} shows or hides this panel.</p>
  </aside>

  <BaseConfirm
    :open="asking !== null"
    :title="confirmText.title"
    :confirm-label="confirmText.ok"
    :busy="demo.busy"
    @confirm="confirm"
    @cancel="asking = null"
  >
    <p data-test="demo-confirm">{{ confirmText.body }}</p>
  </BaseConfirm>
</template>

<style scoped>
/* An operator tool: small, quiet, out of the way, in the existing tokens only. */
.demo {
  position: fixed;
  right: var(--space-4);
  bottom: var(--space-4);
  z-index: 50;
  display: grid;
  gap: var(--space-3);
  width: 272px;
  max-height: calc(100vh - var(--top-bar-height) - var(--space-8));
  overflow: auto;
  padding: var(--space-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.demo:focus-visible {
  outline-offset: 0;
}

.demo__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.demo__close {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.demo__close:hover {
  border-color: var(--border-default);
  color: var(--text-primary);
}

.demo__group {
  display: grid;
  gap: var(--space-1);
}

.demo__title {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
}

.demo__speeds {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-1);
}

.demo__action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  min-height: 28px;
  padding: 0 var(--space-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.demo__action:hover {
  border-color: var(--border-default);
  background: var(--surface-sunken);
}

.demo__action[aria-disabled='true'] {
  color: var(--text-muted);
  cursor: not-allowed;
}

.demo__action[aria-disabled='true']:hover {
  border-color: var(--border-subtle);
  background: var(--surface-raised);
}

/* A pressed control is a neutral inversion, never a band colour (ValueWise section 1) */
.demo__speed[aria-pressed='true'],
.demo__speed[aria-pressed='true']:hover {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--text-inverse);
  font-weight: 600;
}

kbd {
  flex: none;
  padding: 0 var(--space-1);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-sunken);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 400;
}

.demo__note {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.demo__status {
  min-height: 1.5em;
  color: var(--text-primary);
  font-size: var(--text-xs);
}
</style>
