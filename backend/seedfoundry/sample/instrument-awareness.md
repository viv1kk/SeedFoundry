# Instrument Awareness: general-purpose large language model

This Seed runs on a general-purpose large language model. It is strong with language and structure and weak with arithmetic over many numbers. Work with both facts.

## Context Management

- **Context window awareness.** A full license inventory, thousands of seats with twelve months of use each, does not fit in one request and should not be sent as one. Plan what goes into the context window before starting.
- **Token conservation.** Send summaries, not inventories: counts and costs per vendor, per product and per utilisation class. Bring individual seats in only when a question is about them.
- **Compression strategies.** Compress a product to one line: entitled, assigned, active, the count in each class and its recoverable cost. Keep numbers exact when compressing; drop prose, never figures.
- **Information prioritisation.** Keep in context the method, the current totals and the product under discussion. Drop products already summarised and closed, and the text of earlier drafts.

## Model Behaviour

### Strengths

- Explaining a finding in plain language for a budget holder.
- Grouping and comparing products, vendors and departments.
- Following a written method step by step when it is stated explicitly.

### Weaknesses

- Adding up long lists of numbers. Totals the model produces are unreliable past a handful of terms.
- Keeping two figures for the same measure consistent across a long answer.
- Telling a missing value apart from a zero.

### Failure patterns

- Rounding silently, so that parts no longer sum to their total.
- Carrying a figure forward from an earlier step after the numbers under it changed.
- Filling a gap with a plausible number instead of saying it is unknown.

### Hallucination risks

- **Figures.** The model may state a total, a percentage or a saving that no computation produced. Never accept a figure from the model alone: recompute every total, share and saving and use the recomputed value.
- **Prices.** Where a unit price is missing, the model may supply a typical market price. Treat any price the inventory does not give as unknown.
- **Names.** Product and vendor names can be blended or invented. Use names exactly as the inventory gives them.

## Execution Constraints

- **Staying within limits.** Work vendor by vendor when the estate is large; never ask for the whole estate in one pass.
- **Avoiding context degradation.** Restate the method and the current totals at the start of each long step rather than relying on text far back in the conversation.
- **Preserving reasoning quality.** Do arithmetic outside the model and pass the results in; ask the model to explain and compare, not to add up. Always recompute totals before they are reported.
