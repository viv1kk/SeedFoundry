# Environment: the license estate

Where this Seed operates: the data it reads, how people use what it produces, how that looks, how it adapts to this account, and the protections around it.

## Data Layer

### Sources

- **License Management System (LMS):** entitlements (seats paid for, per product), assignments (who holds which seat) and monthly usage.
- **SAP:** contract items per product, carrying the unit price per seat-month where the contract states one.

### The record: a seat

One record per entitled seat.

| Field | Meaning | Source |
|---|---|---|
| `seat_id` | `LIC-` and six digits, for example `LIC-001848` | LMS |
| `product` | Product name | LMS |
| `vendor` | Vendor of the product: a property of the product, not of the seat | LMS |
| `department` | Department of the assignee; empty when unassigned | LMS |
| `assignee` | Person holding the seat; empty when unassigned | LMS |
| `assignee_status` | `employed` or `left` | LMS, synced from the staff directory |
| `last_used` | Date of the last recorded use | LMS |
| `days_idle` | Days from `last_used` to the snapshot date | derived |
| `utilisation_class` | Active, Underused, Unused, Leaver or Unassigned, as Value.md defines them | derived |
| `unit_cost` | Price per seat-month in USD; empty when the contract states none | SAP |

### Usage

- Twelve months of monthly usage per seat: `seat_id`, `month`, `days_active` in that month.
- "The last 90 days" is read as the three most recent months.

### Mappings

- Seat to product: `seat_id` to `product` in the LMS.
- Product to price: the LMS product name matches the SAP contract item description.
- Vendor comes from the product, never from the seat.

### Formats and storage

- Both systems are read as a snapshot taken on one date, held as read-only files in the Seed's sandbox.
- Unit price is incomplete: some products have no price in SAP. Every other field is complete.
- The logic does not depend on this estate. Any dataset with these fields works the same way; swapping it changes only this layer.

## User Experience

The output is the License Optimization dashboard: one screen, read from top to bottom.

### Screen layout

Four bands, in this order:

1. **KPI row:** Entitled, Assigned, Active, Unused or underused, and Recoverable a year with the number of withheld seats beside it.
2. **Chart grid** on twelve columns: Seats by vendor and product across the full width, then Entitled, assigned and active by product; Assigned and in use, by month; Recoverable cost by product.
3. **Optimisation candidates:** one row per product with its vendor, the count in each class and the recoverable cost, and a total row.
4. **Seats:** every seat, paginated and sortable, with the class counts and the total in the footer.

### Navigation

- Drill down from all products to a vendor, a product, a utilisation class, then the seats themselves. Clicking a treemap cell or a bar drills; a treemap leaf drills vendor, product and class in one step.
- A drill bar above the bands holds Back and a breadcrumb: All products, then each level reached.
- The drill path is in the address, so a reload and the browser's Back both keep it.

### Interaction patterns

- Every panel follows the current drill.
- Hovering a chart element shows its exact value.
- Seats table columns sort on click.

### Workflow

- Read the KPI row, find the largest block in the treemap, drill into it, and end at the seats behind it.

## Styling

### Colours

- Every colour comes from the design system's chart roles. No other colour appears.
- Each utilisation class keeps one colour everywhere: Active `positive` (green), Underused `warning` (amber), Unused `anomaly` (orange), Leaver `negative` (red), Unassigned `muted` (grey).
- Red is kept for faults. Only Leaver seats use it; a normal series never does.
- Entitled seats use `baseline`, assigned seats `series-1`, seats in use `positive`.

### Number formats

- Counts carry thousands separators: 1,200, never 1200 or 1.2k.
- Money is in US dollars with the $ sign, in one style per measure: $45k on charts and KPIs, whole dollars in tables.
- Percentages have one decimal place.

### Charts

- Bars for comparisons between categories. A pie only for six slices or fewer.
- Every axis has a name and, where it has one, a unit.

### Type, grid and themes

- Inter for text and figures, JetBrains Mono for ids such as `LIC-001848`. One family per role on every panel.
- Cards sit on the twelve-column grid with equal gutters. Nothing overflows its card and no table is cut off.
- Light and dark themes. All text, muted text included, meets WCAG AA contrast in both.

## Adaptation Layer

### Account

- A professional services firm working in several countries. Spend is reported in US dollars, and the fiscal year starts in April.
- Departments are named as the firm names them: Consulting, Engineering, Finance, Legal, Marketing, Operations, People and Sales.

### Industry

- In professional services, staff time is the main cost, so tools used in client work count as part of delivery, not overhead.
- Use dips in August and late December are normal across the estate.

### Situation

- The analysis runs ahead of each vendor renewal, so that seats can be returned within the renewal window.
- Readers are budget holders and the procurement team, not license specialists: plain words, no internal codes.

## Protection Layer

### Guardrails

- Read only. The Seed reports; it never removes, reassigns or changes a seat in any system.
- A cost figure is shown only where a unit price exists. An unpriced product shows as withheld, never as zero.

### Validation checks

- Every figure is recomputed from the seat records, never typed in or carried over.
- Parts sum to their totals: product bars to the Entitled KPI, table rows to their total row, footer class counts to the seat total.
- Each set of percentages sums to 100% within 0.1.
- A derived figure equals its formula: Recoverable a year equals the sum of recoverable cost by product.
- The same measure agrees on every panel where it appears.

### Quality controls

- Each panel renders within 1.0 s. A slower panel is a finding.
- The Styling rules are checked on every build: palette, red for faults only, number formats, axis names and units, grid and fonts, contrast.

### Security mechanisms

- Assignee names appear only at the seat level, never in exports or in summaries above it.
- The dataset stays inside the sandbox. Nothing is sent outside it.
