<script setup lang="ts">
// A table panel from its descriptor: Optimisation candidates (one row per product, a total row,
// a product cell that drills) and Seats (paginated, sortable, with the class counts and the total
// in its footer). Figures are in the figures' face, right-aligned; a class is a chip in its role.
// Sorting and paging ask the server for the rows (D-56); this component only renders.
import { computed } from 'vue'
import { format } from '../../dashboard/format'
import type { ClassInfo, Column, Panel, PanelData, Row, SortDirection, Step } from '../../dashboard/types'
import BaseButton from '../base/BaseButton.vue'

const props = defineProps<{ panel: Panel; data: PanelData; classes: ClassInfo[]; busy?: boolean }>()
const emit = defineEmits<{
  drill: [step: Step]
  page: [page: number]
  sort: [column: string, direction: SortDirection]
}>()

const columns = computed(() => props.panel.columns ?? [])
const rows = computed(() => props.data.rows ?? [])
const classById = computed(() => new Map(props.classes.map((c) => [c.id, c])))
const total = computed(() => (props.panel.total_row && typeof props.data.total === 'object' ? (props.data.total as Row) : null))
const footer = computed(() => (props.panel.footer === 'class_counts' ? props.data.footer ?? null : null))
const paged = computed(() => Boolean(props.panel.page_size))
const page = computed(() => props.data.page ?? 1)
const pages = computed(() => props.data.pages ?? 1)

function text(row: Row, column: Column): string {
  const value = row[column.id]
  if (value === null || value === undefined || value === '') return column.null ?? ''
  if (column.format === 'class') return classById.value.get(String(value))?.label ?? String(value)
  return format(value, column.format)
}

function isEmpty(row: Row, column: Column): boolean {
  const value = row[column.id]
  return value === null || value === undefined || value === ''
}

function sortState(column: Column): 'ascending' | 'descending' | 'none' {
  if (props.data.sort !== column.id) return 'none'
  return props.data.direction === 'desc' ? 'descending' : 'ascending'
}

function sortBy(column: Column): void {
  const direction: SortDirection = props.data.sort === column.id && props.data.direction === 'asc' ? 'desc' : 'asc'
  emit('sort', column.id, direction)
}

function drillStep(row: Row): Step | null {
  return Array.isArray(row.step) && row.step.length ? (row.step as Step) : null
}
</script>

<template>
  <article class="table-panel" :data-panel="panel.id" data-test="table-panel" :aria-busy="busy ? 'true' : undefined">
    <header class="table-panel__head">
      <h3 class="table-panel__title">{{ panel.title }}</h3>
      <p v-if="panel.caption" class="table-panel__caption" :style="{ color: `var(--${panel.caption_role ?? 'text-secondary'})` }" data-test="table-caption">
        {{ panel.caption }}
      </p>
    </header>
    <div class="table-panel__scroll" data-test="table-scroll">
      <table class="table-panel__table">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.id"
              scope="col"
              :class="{ 'is-end': column.align === 'end' }"
              :aria-sort="panel.sortable ? sortState(column) : undefined"
            >
              <button v-if="panel.sortable" type="button" class="table-panel__sort" data-test="sort" :data-column="column.id" @click="sortBy(column)">
                {{ column.label }}
                <span class="table-panel__arrow" aria-hidden="true">{{ sortState(column) === 'ascending' ? '↑' : sortState(column) === 'descending' ? '↓' : '' }}</span>
              </button>
              <span v-else class="table-panel__label">
                <span
                  v-if="column.class"
                  class="table-panel__swatch"
                  :style="{ background: `var(--chart-${classById.get(column.class)?.role})` }"
                  aria-hidden="true"
                ></span>
                {{ column.label }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="String(row[panel.row_key ?? 'id'])" data-test="row">
            <td
              v-for="column in columns"
              :key="column.id"
              :class="{
                'is-end': column.align === 'end',
                'is-figure': column.measure || column.font === 'id' || column.format === 'date',
                'is-empty': isEmpty(row, column),
              }"
            >
              <button
                v-if="column.drill && drillStep(row)"
                type="button"
                class="table-panel__drill"
                data-test="drill-row"
                @click="emit('drill', drillStep(row)!)"
              >
                {{ text(row, column) }}
              </button>
              <span v-else-if="column.format === 'class' && !isEmpty(row, column)" class="table-panel__class">
                <span
                  class="table-panel__swatch"
                  :style="{ background: `var(--chart-${classById.get(String(row[column.id]))?.role})` }"
                  aria-hidden="true"
                ></span>
                {{ text(row, column) }}
              </span>
              <template v-else>{{ text(row, column) }}</template>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="columns.length" class="table-panel__none">No seats at this level.</td>
          </tr>
        </tbody>
        <tfoot v-if="total">
          <tr data-test="total-row">
            <template v-for="(column, i) in columns" :key="column.id">
              <th v-if="i === 0" scope="row">{{ total[column.id] }}</th>
              <td v-else :class="{ 'is-end': column.align === 'end', 'is-figure': column.measure }">{{ text(total, column) }}</td>
            </template>
          </tr>
        </tfoot>
      </table>
    </div>
    <footer v-if="footer" class="table-panel__footer" data-test="class-footer">
      <ul class="table-panel__counts" aria-label="Seats by class">
        <li v-for="cls in classes" :key="cls.id" class="table-panel__count">
          <span class="table-panel__swatch" :style="{ background: `var(--chart-${cls.role})` }" aria-hidden="true"></span>
          {{ cls.label }} <span class="table-panel__figure">{{ format(footer[cls.id] ?? 0, 'count') }}</span>
        </li>
      </ul>
      <p class="table-panel__total">Total <span class="table-panel__figure" data-test="footer-total">{{ format(footer.total ?? 0, 'count') }}</span></p>
    </footer>
    <nav v-if="paged" class="table-panel__pages" :aria-label="`${panel.title} pages`" data-test="pagination">
      <BaseButton :disabled="page <= 1" explain-disabled data-test="page-first" @click="emit('page', 1)">First</BaseButton>
      <BaseButton :disabled="page <= 1" explain-disabled data-test="page-previous" @click="emit('page', page - 1)">Previous</BaseButton>
      <p class="table-panel__range" aria-live="polite" data-test="page-range">
        {{ panel.title }} <span class="table-panel__figure">{{ format(data.first ?? 0, 'count') }}</span> to
        <span class="table-panel__figure">{{ format(data.last ?? 0, 'count') }}</span> of
        <span class="table-panel__figure">{{ format(data.total as number, 'count') }}</span>, page
        <span class="table-panel__figure">{{ format(page, 'count') }}</span> of <span class="table-panel__figure">{{ format(pages, 'count') }}</span>
      </p>
      <BaseButton :disabled="page >= pages" explain-disabled data-test="page-next" @click="emit('page', page + 1)">Next</BaseButton>
      <BaseButton :disabled="page >= pages" explain-disabled data-test="page-last" @click="emit('page', pages)">Last</BaseButton>
    </nav>
  </article>
</template>

<style scoped>
.table-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  min-width: 0;
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.table-panel[aria-busy='true'] .table-panel__table {
  color: var(--text-muted);
}

.table-panel__title {
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: 1.3;
}

.table-panel__caption {
  font-size: var(--text-sm);
}

.table-panel__scroll {
  overflow-x: auto;
}

.table-panel__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

th,
td {
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
  text-align: left;
  white-space: nowrap;
}

thead th {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  border-bottom-color: var(--border-default);
}

.is-end {
  text-align: right;
}

.is-figure {
  font-family: var(--font-mono);
}

.is-empty {
  color: var(--text-muted);
}

tfoot th,
tfoot td {
  border-top: 1px solid var(--border-strong);
  border-bottom: 0;
  font-weight: 600;
}

.table-panel__sort {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  cursor: pointer;
}

.table-panel__sort:hover {
  color: var(--text-primary);
}

.table-panel__arrow {
  display: inline-block;
  min-width: 1ch;
}

.table-panel__label,
.table-panel__class {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.table-panel__swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex: none;
}

.table-panel__drill {
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  text-align: left;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.table-panel__none {
  color: var(--text-muted);
}

.table-panel__footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.table-panel__counts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-5);
  margin: 0;
  padding: 0;
  list-style: none;
}

.table-panel__count {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.table-panel__figure {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-weight: 600;
}

.table-panel__total {
  font-weight: 600;
}

.table-panel__pages {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.table-panel__range {
  margin: 0 var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}
</style>
