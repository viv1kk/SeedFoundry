# Observer feedback on iteration 1

- N-1 to N-5: the totals do not add up. The product bars sum to more than the Entitled KPI, the class shares sum to 112%, the Recoverable KPI is not the sum of recoverable cost by product, the Seats footer total is wrong, and the Optimisation candidates total counts one product twice. Every total must equal the sum of the seat records behind it.

- V-1: Recoverable cost by product is a pie of twelve slices. A bar chart reads better for more than six products.

- V-2, V-3, V-7 and V-8: red is used for a normal series, two colours are off the palette, one title is in a serif font, and some muted text is too faint to read. Keep to the design system's colours and fonts, with AA contrast in both themes.

- V-4 and V-5: number formats are mixed (13050, 13,050 and 13.1k), money is missing its $ sign, and two charts have no axis names. Use thousands separators, the $ sign, and a named axis with its unit.

- V-6: cards are misaligned, the treemap overflows its card, and the last two Seats columns are cut off. Keep every card on the grid.

- L-1: Seats by vendor and product shows a spinner for about 4.5 seconds before it draws, while every other panel appears at once. No panel should keep the reader waiting more than a second.

- Hallucination risks: the saving in N-3 reads like a number the language model made up. Never accept a figure from the model alone.

- When two panels disagree (N-1, N-3), the reasoning should stop there: name each assumption, gather the evidence, and only then draw a conclusion.

- A saving only has value once a budget holder can trace it to its seats, so success is a smaller figure everyone believes over a larger one nobody can check.

Otherwise the build was easy to follow.
