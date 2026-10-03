# License Optimization

Reduce what the organisation spends on software licenses without taking away tools people need.

## Purpose

- Find the seats the organisation pays for but does not need, product by product, and size what returning them would save in a year.
- Give budget holders a short, checked list of seats to reclaim, with the evidence for each.
- Make plain where the estimate is incomplete, so nobody acts on a number that is not there.

## Core Principles

### Prioritisation

- Work through products by recoverable cost a year, largest first. Where cost is withheld, order by recoverable seats instead.
- Within a product, take Leaver seats first (paid for, held by nobody), then Unassigned, then Unused.

### Filtering

- A seat is a candidate only in a recoverable class: Unused, Leaver or Unassigned.
- Underused seats are reported, never recovered: someone still uses them.

### Confidence assignment

- **High:** the product has a unit price and the seat has three full months of usage.
- **Withheld:** the product has no unit price. Its seats still count; their cost is not stated.
- The estimate as a whole is graded High when at least 95% of entitled seats are on priced products, and Partial below that.

### Opportunity qualification

Every seat falls in exactly one utilisation class, tested in this order:

1. **Unassigned:** entitled, with no assignee.
2. **Leaver:** assigned to someone who has left the organisation, whatever the usage.
3. **Unused:** assigned, with no days active in the last 90 days.
4. **Underused:** assigned, active on 1 to 11 days in the last 90 days, less than about once a week.
5. **Active:** assigned, active on 12 days or more in the last 90 days.

### Estimation methodology

- Recoverable cost a year for one seat is its unit cost per seat-month times 12.
- Only priced products are costed. An unpriced product is withheld, never estimated, and the number of withheld seats is stated with the total.
- Totals are sums over seats, never scaled up from a sample.

### Value realisation

- A saving is realised when the seat is returned at the vendor's next renewal or true-up, not when it is found.
- Reclaimed seats go back to a pool for 30 days before they are cancelled, so a mistaken reclaim costs a day, not a contract.

## Value Logic

- **Success** is recovered annual spend with no rise in requests for the reclaimed products over the following 90 days.
- **Measured by** recoverable cost a year (priced products), recoverable seats (all products) and the share of entitled seats that are Active.
- **A recommendation is good** when every seat in it can be traced to its class and every dollar to a unit price.
- **Trade-offs:** savings against disruption. Many seats nobody uses beat a few seats somebody uses rarely. A Leaver seat is always worth reclaiming; an Underused seat never is.

## Decision Logic

These rules hold whatever the data, the setting or the tool.

- **Should:** state cost for priced products only, and say how many seats are withheld.
- **Should:** report Underused seats beside the candidates, so the reader sees the whole estate.
- **Should:** trace every recommended seat to its class and every saving to the seats it counts.
- **Should not:** recover a seat in the Active or Underused class.
- **Should not:** estimate a price the inventory does not give.
- **Should not:** count a seat in more than one class, or a product under more than one vendor.
- **How choices are made:** when two candidates save the same, take the one that disrupts fewer people. When the evidence for a seat is incomplete, report it with lower confidence rather than drop it.
