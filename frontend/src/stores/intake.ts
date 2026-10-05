// The Knowledge page's working state (D-41): categories from the server, drafts and
// autosave, and the file actions. The server's copy of every file lives in the lab store;
// a draft exists only while a file has text the server may not have, so an event can never
// overwrite what the user typed. Saving is automatic after a pause, on file switch, on
// leaving the page, and before Start Build (FR-IN-6).

import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'
import { ApiError, messageOf } from '../api'
import { buildsApi } from '../builds'
import { hintedCategory, intakeApi, isFilled, utf8Size, type CategoryInfo, type IntakeFile } from '../intake'
import { useLabStore, type Build } from './lab'

/** Quiet time after the last keystroke before an autosave. */
export const AUTOSAVE_MS = 800

/** A PATCH sent with keepalive while the page unloads must stay under the browser's 64 KiB. */
export const KEEPALIVE_MAX_BYTES = 60_000

interface Draft {
  text: string
  saving: boolean
  error: string | null
}

export const useIntakeStore = defineStore('intake', () => {
  const lab = useLabStore()

  // Categories (GET /api/intake/categories): the only copy the frontend has.
  const categories = ref<CategoryInfo[]>([])
  const filenameHints = ref<Record<string, string>>({})
  const maxFileBytes = ref(0)
  const categoriesError = ref<string | null>(null)
  let categoriesRequest: Promise<void> | null = null

  function loadCategories(): Promise<void> {
    if (categories.value.length) return Promise.resolve()
    categoriesRequest ??= intakeApi
      .categories()
      .then((body) => {
        categories.value = body.categories
        filenameHints.value = body.filename_hints
        maxFileBytes.value = body.max_file_bytes
        categoriesError.value = null
      })
      .catch((error) => {
        categoriesError.value = messageOf(error)
      })
      .finally(() => {
        categoriesRequest = null
      })
    return categoriesRequest
  }

  const coreCategories = computed(() => categories.value.filter((c) => c.core))
  /** Where a file goes when nothing else says: the first initiation file not yet added, else the
   * first category. Knowledge offers no other category (D-84). */
  const defaultCategory = computed(
    () => categories.value.find((c) => !lab.files.some((f) => f.category === c.id))?.id ?? categories.value[0]?.id ?? '',
  )

  function category(id: string): CategoryInfo | undefined {
    return categories.value.find((c) => c.id === id)
  }

  function isCore(id: string): boolean {
    return category(id)?.core ?? false
  }

  function labelOf(id: string): string {
    return category(id)?.label ?? id
  }

  /** Files in Ensemble order (category order, then creation order). Only the categories Knowledge
   * offers: the observer feedback is kept with the builds, not listed (D-84). */
  const orderedFiles = computed<IntakeFile[]>(() => {
    const order = new Map(categories.value.map((c, index) => [c.id, index]))
    return lab.files
      .map((file, index) => ({ file, index }))
      .filter(({ file }) => order.has(file.category))
      .sort((a, b) => (order.get(a.file.category) ?? 99) - (order.get(b.file.category) ?? 99) || a.index - b.index)
      .map(({ file }) => file)
  })

  /** The file holding a core slot, other than `except`. */
  function slotHolder(categoryId: string, except?: string): IntakeFile | undefined {
    if (!isCore(categoryId)) return undefined
    return lab.files.find((f) => f.category === categoryId && f.id !== except)
  }

  /** A file's category from its name; with no hint, the first initiation file neither added nor
   * in `taken` (the rows before it in one import), else the default (D-84). */
  function hasHint(filename: string): boolean {
    return hintedCategory(filename, filenameHints.value, '') !== ''
  }

  function hintFor(filename: string, taken: readonly string[] = []): string {
    const open = categories.value.find((c) => !taken.includes(c.id) && !lab.files.some((f) => f.category === c.id))
    return hintedCategory(filename, filenameHints.value, open?.id ?? defaultCategory.value)
  }

  /** The name a file gets when it is added to a category (D-85): Environment_01.md for
   * Environment.md. A category the server did not name falls back to its first filename hint. */
  function suggestedName(categoryId: string): string {
    const named = category(categoryId)?.file_name
    if (named) return named
    const hinted = Object.entries(filenameHints.value).find(([, c]) => c === categoryId)
    return hinted ? hinted[0] : 'notes.md'
  }

  // Drafts and autosave.
  const drafts = reactive<Record<string, Draft>>({})
  const timers = new Map<string, ReturnType<typeof setTimeout>>()
  const inflight = new Map<string, Promise<void>>()

  /** What the editor shows: the draft, else the server's copy. */
  function text(id: string): string {
    return drafts[id]?.text ?? lab.file(id)?.content ?? ''
  }

  function isDirty(id: string): boolean {
    const draft = drafts[id]
    return !!draft && draft.text !== (lab.file(id)?.content ?? '')
  }

  function isSaving(id: string): boolean {
    return drafts[id]?.saving ?? false
  }

  function saveError(id: string): string | null {
    return drafts[id]?.error ?? null
  }

  const anyDirty = computed(() => Object.keys(drafts).some((id) => isDirty(id)))

  function edit(id: string, value: string): void {
    const draft = drafts[id]
    if (draft) draft.text = value
    else drafts[id] = { text: value, saving: false, error: null }
    schedule(id)
  }

  function schedule(id: string): void {
    clearTimeout(timers.get(id))
    timers.set(
      id,
      setTimeout(() => {
        timers.delete(id)
        void save(id)
      }, AUTOSAVE_MS),
    )
  }

  function dropDraft(id: string): void {
    clearTimeout(timers.get(id))
    timers.delete(id)
    delete drafts[id]
  }

  /** Drop a draft the server already has, unless an autosave is still due. */
  function settle(id: string): void {
    const draft = drafts[id]
    if (draft && !draft.saving && !draft.error && !timers.has(id) && !isDirty(id)) delete drafts[id]
  }

  /** Save a file's draft now. Resolves when the server has it, or the save failed. */
  function save(id: string): Promise<void> {
    const running = inflight.get(id)
    if (running) return running.then(() => save(id))
    const draft = drafts[id]
    if (!draft) return Promise.resolve()
    if (!lab.file(id)) {
      dropDraft(id)
      return Promise.resolve()
    }
    if (!isDirty(id)) {
      draft.error = null
      settle(id)
      return Promise.resolve()
    }
    const content = draft.text
    draft.saving = true
    lab.expectEcho(id, content)
    const request = intakeApi
      .update(id, { content })
      .then((file) => {
        lab.upsertFile(file)
        if (drafts[id]) drafts[id].error = null
      })
      .catch((error: unknown) => {
        lab.forgetEcho(id, content)
        if (error instanceof ApiError && error.code === 'file_not_found') {
          lab.removeFile(id)
          dropDraft(id)
        } else if (drafts[id]) {
          drafts[id].error = messageOf(error)
        }
      })
      .finally(() => {
        inflight.delete(id)
        if (drafts[id]) drafts[id].saving = false
        settle(id)
      })
    inflight.set(id, request)
    return request
  }

  /** Save now instead of after the pause. */
  function flush(id: string | null | undefined): Promise<void> {
    if (!id) return Promise.resolve()
    clearTimeout(timers.get(id))
    timers.delete(id)
    return save(id)
  }

  function flushAll(): Promise<void> {
    return Promise.all(Object.keys(drafts).map((id) => flush(id))).then(() => undefined)
  }

  /**
   * The page is going away. Small drafts go out with keepalive, which the browser finishes
   * after the page has gone. True when a draft is too large for that, so the page should
   * ask the browser to confirm leaving.
   */
  function flushOnUnload(): boolean {
    let unsent = false
    for (const id of Object.keys(drafts)) {
      if (!isDirty(id) || lab.runningBuild) continue
      const content = drafts[id].text
      if (utf8Size(content) > KEEPALIVE_MAX_BYTES) {
        unsent = true
        continue
      }
      clearTimeout(timers.get(id))
      timers.delete(id)
      void intakeApi.update(id, { content }, true).catch(() => undefined)
    }
    return unsent
  }

  // A save refused while a build ran keeps its draft; send it once the build is over.
  watch(
    () => lab.runningBuild,
    (running) => {
      if (running) return
      for (const id of Object.keys(drafts)) if (isDirty(id)) void flush(id)
    },
  )

  // Core checklist (FR-IN-8): what the user sees, so a slot follows typing before the save.
  const coreSlots = computed(() =>
    coreCategories.value.map((c) => {
      const holder = lab.files.find((f) => f.category === c.id)
      return { category: c, file: holder ?? null, complete: !!holder && isFilled(text(holder.id)) }
    }),
  )
  const missing = computed(() => coreSlots.value.filter((slot) => !slot.complete).map((slot) => slot.category.label))
  const ready = computed(() => coreSlots.value.length > 0 && missing.value.length === 0)

  // Start Build (FR-B-1): save every draft, then ask the server for a build of the current
  // iteration. The build is returned so the caller can open its page; a refusal is shown as
  // the server wrote it. The demo controller's Shift+Enter runs the same action (D-47).
  const buildNote = ref<string | null>(null)

  async function startBuild(): Promise<Build | null> {
    if (!ready.value || lab.runningBuild) return null
    await flushAll()
    if (anyDirty.value) {
      buildNote.value = 'Some changes are not saved yet.'
      return null
    }
    try {
      const build = await buildsApi.start()
      lab.upsertBuild(build)
      buildNote.value = null
      return build
    } catch (error) {
      buildNote.value = messageOf(error)
      return null
    }
  }

  watch(ready, () => {
    buildNote.value = null
  })

  /** Drop the drafts of files that no longer exist, after Load sample, Clear or Reset. */
  function discardMissing(): void {
    for (const id of Object.keys(drafts)) if (!lab.file(id)) dropDraft(id)
  }

  // File actions. Each applies the server's answer at once; the matching event then finds
  // the snapshot already up to date.

  /** After a replace, the old file is gone; its delete event may come later. */
  function applyReplaced(file: IntakeFile): void {
    const old = slotHolder(file.category, file.id)
    if (old) {
      lab.removeFile(old.id)
      dropDraft(old.id)
    }
  }

  async function create(name: string, categoryId: string, replace: boolean): Promise<IntakeFile> {
    const file = await intakeApi.create({ name, category: categoryId, content: '', replace })
    if (replace) applyReplaced(file)
    lab.upsertFile(file)
    return file
  }

  /** Import a file into a category. It takes the category's name (D-85), whatever it was called. */
  async function importFile(upload: Blob, filename: string, categoryId: string, replace: boolean): Promise<IntakeFile> {
    const file = await intakeApi.import(filename, upload, categoryId, replace, isCore(categoryId) ? suggestedName(categoryId) : undefined)
    if (replace) applyReplaced(file)
    lab.upsertFile(file)
    return file
  }

  // A rename or category change takes only the name and category from the answer: content
  // follows saves and events, so an autosave on its way is not undone here.
  function applyMeta(file: IntakeFile): void {
    const known = lab.file(file.id)
    if (known) Object.assign(known, { name: file.name, category: file.category })
  }

  async function rename(id: string, name: string): Promise<IntakeFile> {
    const file = await intakeApi.update(id, { name })
    applyMeta(file)
    return file
  }

  /** Move a file to another category. It takes that category's name, as an added file does (D-85). */
  async function recategorise(id: string, categoryId: string, replace: boolean): Promise<IntakeFile> {
    const changes = isCore(categoryId) ? { category: categoryId, name: suggestedName(categoryId), replace } : { category: categoryId, replace }
    const file = await intakeApi.update(id, changes)
    if (replace) applyReplaced(file)
    applyMeta(file)
    return file
  }

  async function remove(id: string): Promise<void> {
    await intakeApi.remove(id)
    lab.removeFile(id)
    dropDraft(id)
  }

  return {
    categories,
    categoriesError,
    coreCategories,
    defaultCategory,
    maxFileBytes,
    loadCategories,
    category,
    isCore,
    labelOf,
    orderedFiles,
    slotHolder,
    hintFor,
    hasHint,
    suggestedName,
    text,
    isDirty,
    isSaving,
    saveError,
    anyDirty,
    edit,
    flush,
    flushAll,
    flushOnUnload,
    coreSlots,
    missing,
    ready,
    buildNote,
    startBuild,
    discardMissing,
    create,
    importFile,
    rename,
    recategorise,
    remove,
  }
})
