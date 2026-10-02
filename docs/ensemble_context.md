# Ensemble: Context for the Four Core MD Files

**Ensemble** is the name for this architecture. It splits AI execution into four separate knowledge layers, each written as its own markdown file. The name follows the musical metaphor in the files themselves. A performance needs a **player**, an **instrument**, a **venue**, and the **music**. When all four are right and kept distinct, together with the current data, the result is a high-quality performance.

> Source note: This context was extracted from a summary of a conversation in which Alex explained the significance of each file. The summary calls the first file `person.md`. It is also referred to as `player.md`. Both names mean the same file. This document uses `person.md (player.md)`.

---

## 1. The Core Formula

```
person.md (player.md)
  + instrument-awareness.md
  + environment.md
  + music.md
  + current data
  = high-quality outcome
```

### Why Ensemble exists

- **The problem:** Most AI solutions fail because all concerns are mixed into a single prompt. Identity, model limitations, data, UI, safety, and business logic end up tangled together.
- **The fix:** Each responsibility gets its own dedicated knowledge layer, in its own file.
- **The central idea:** The best outcomes happen when **identity**, **model-awareness**, **environment**, and **purpose** are treated as separate layers, not mixed into one large prompt.
- **Current data** is a separate input, supplied at run time. It is not one of the four files.

### The four questions

| Question | File | Role | Musical analogy |
|---|---|---|---|
| **WHO** performs the work? | `person.md` (player.md) | How the AI thinks | The player / musician |
| **WHAT** tool is being used? | `instrument-awareness.md` | How the AI uses the model | Knowing the instrument |
| **WHERE** does the work happen? | `environment.md` | Where the AI operates | The venue / stage |
| **WHY** and **HOW** is value created? | `music.md` | Why the AI exists and how value is created | The composition itself |

---

## 2. person.md (player.md)

### Key question
**"Who is performing the work?"**

### Purpose
This file defines the **identity of the AI worker**. It describes how the AI should:

- think
- reason
- evaluate information
- make decisions

Think of it as the AI's **professional persona**. It is the expert who does the work, separate from the tool used, the place it is done, and the purpose behind it.

### What belongs here
| Category | Description |
|---|---|
| Domain expertise | The field(s) in which the AI acts as an expert |
| Subject matter knowledge | What the expert knows about the domain |
| Reasoning methods | How the AI moves from information to conclusions |
| Analytical approaches | How the AI breaks down and examines a problem |
| Decision-making patterns | How the AI weighs options and commits to a choice |
| Problem-solving strategies | How the AI tackles unfamiliar or complex problems |
| Thinking frameworks | Structured mental models the AI applies |

### What does NOT belong here
| Excluded item | Where it belongs instead |
|---|---|
| Raw data | `environment.md` (Data Layer) or current data |
| UI styling | `environment.md` (Styling) |
| Security constraints | `environment.md` (Protection Layer) |
| Data mappings | `environment.md` (Data Layer) |
| Environment settings | `environment.md` |
| Technical platform limitations | `instrument-awareness.md` |

### One-line summary
**`person.md` defines how the AI thinks.**

---

## 3. instrument-awareness.md

### Key question
**"What tool am I using, and how do I use it effectively?"**

### Purpose
This file defines the AI's **understanding of the model it is running on**. Every model has its own:

- strengths
- limitations
- token constraints
- compression behaviour
- reasoning characteristics

The AI should know about these and work with them. A skilled musician knows what their instrument can and cannot do. Likewise, the AI should know the model it runs on.

### What belongs here

#### 3.1 Context Management
| Item | Description |
|---|---|
| Context window awareness | Knowing how much the model can hold at once |
| Token conservation | Using tokens economically |
| Compression strategies | How to condense information without losing what matters |
| Information prioritization | Deciding what must stay in context and what can be dropped |

#### 3.2 Model Behaviour
| Item | Description |
|---|---|
| Strengths | What this model does well |
| Weaknesses | What this model does poorly |
| Failure patterns | The typical ways this model goes wrong |
| Hallucination risks | Where and when the model tends to make things up |

#### 3.3 Execution Constraints
| Item | Description |
|---|---|
| Staying within limits | Operating inside the model's token and context limits |
| Avoiding context degradation | Keeping quality from decaying as context grows or gets compressed |
| Preserving reasoning quality | Keeping reasoning sound under the constraints above |

### What does NOT belong here
| Excluded item | Where it belongs instead |
|---|---|
| Business logic | `music.md` |
| Domain methodology | `music.md` (method) / `person.md` (expertise) |
| Opportunity generation logic | `music.md` |
| User interface definitions | `environment.md` (User Experience) |

### One-line summary
**`instrument-awareness.md` teaches the AI how to use the underlying model efficiently.**

---

## 4. environment.md

### Key question
**"Where does the AI operate?"**

### Purpose
This file defines **everything around the AI that lets it operate**.

> The environment is **not the goal itself**. It is the **supporting ecosystem**.

It is the stage, the lighting, and the house rules, not the performance.

### What belongs here: the five layers

#### 4.1 Data Layer
| Item | Description |
|---|---|
| Data sources | Where data comes from |
| Data structures | How the data is shaped |
| Data mappings | How fields and entities relate to the concepts the logic uses |
| Input formats | The formats in which data arrives |
| Storage locations | Where data lives |

> **Important principle:** The environment *contains* the data, but the **logic should work regardless of which dataset is supplied**.
>
> The logic in `music.md` must never depend on one specific dataset. Swapping the data should not require rewriting the logic. Only the environment changes.

#### 4.2 User Experience
| Item | Description |
|---|---|
| Navigation | How the user moves through the solution |
| Workflow design | The sequence of steps a user goes through |
| Interaction patterns | How the user and the system exchange input and output |
| Screen layouts | How content is arranged on screen |

#### 4.3 Styling
| Item | Description |
|---|---|
| Colors | Colour palette |
| Themes | Overall visual themes |
| Visual skins | Swappable visual treatments |
| Presentation appearance | How output looks when presented |

> **Styling and UX are intentionally separated.** UX is about how things *work* (flow, navigation, interaction). Styling is about how things *look*. You can change either one without touching the other.

#### 4.4 Adaptation Layer
| Item | Description |
|---|---|
| Account-specific adjustments | Tailoring for a particular client or account |
| Industry-specific adjustments | Tailoring for a particular industry |
| Context adaptation | Adjusting to the situation in which the solution is used |

#### 4.5 Protection Layer
| Item | Description |
|---|---|
| Guardrails | Limits on what the system may do |
| Safety rules | Rules that prevent harmful behaviour |
| Quality controls | Checks that output meets a standard |
| Validation checks | Verification of inputs and outputs |
| Security mechanisms | Protection of data and access |

### What does NOT belong here
| Excluded item | Where it belongs instead |
|---|---|
| Core business logic | `music.md` |
| Value-generation methodology | `music.md` |
| Reasoning principles | `person.md` (how to think) / `music.md` (solution's decision rules) |

### One-line summary
**`environment.md` defines the operating environment, data, UX, styling, adaptation, and protection layers.**

---

## 5. music.md

### Key question
**"Why are we doing this, and how should value be created?"**

### Purpose
**This is the most important file.**

- It contains the **actual intellectual property** of the solution.
- **If the other three files disappear, this is the one you would want to preserve first.**

The player, instrument, and venue can all be replaced. The music is what makes the performance worth having.

### What belongs here: four sections

#### 5.1 Purpose
What is the system trying to achieve? Examples:

- Generate recommendations
- Create opportunities
- Produce forecasts
- Generate action plans
- Optimize decisions

#### 5.2 Core Principles
The fundamental reasoning rules of the solution. Examples:

| Principle | Description |
|---|---|
| Prioritization logic | How items are ranked and ordered |
| Filtering rules | What is kept and what is discarded |
| Confidence assignment | How confidence levels are given to outputs |
| Opportunity qualification methods | How a candidate is judged to be a real opportunity |
| Estimation methodology | How sizes, values, or impacts are estimated |
| Value realization approaches | How projected value is turned into actual value |

#### 5.3 Value Logic
How value is created. Examples:

- What constitutes success
- How outcomes are measured
- How recommendations are evaluated
- How trade-offs are made

#### 5.4 Decision Logic
The **invariant rules** (rules that do not change across data, environment, or model) that define:

- What **should** happen
- What **should not** happen
- How choices are made

### What does NOT belong here
| Excluded item | Where it belongs instead |
|---|---|
| Raw data | `environment.md` (Data Layer) or current data |
| UI designs | `environment.md` (User Experience) |
| Styling | `environment.md` (Styling) |
| Technical constraints | `instrument-awareness.md` |
| Security controls | `environment.md` (Protection Layer) |

### One-line summary
**`music.md` contains the purpose, principles, methodology, and value-generation logic of the solution.**

---

## 6. Boundary Rules (Where Does This Go?)

Each concern has exactly one home. If you are unsure, use this table.

| If the content is about... | It goes in |
|---|---|
| Expertise, reasoning style, thinking frameworks, how to decide | `person.md` |
| Context window, tokens, compression, model strengths/weaknesses, hallucination risk | `instrument-awareness.md` |
| Data sources, structures, mappings, formats, storage | `environment.md` → Data Layer |
| Navigation, workflow, interaction, screen layout | `environment.md` → User Experience |
| Colours, themes, skins, appearance | `environment.md` → Styling |
| Per-account, per-industry, per-context tweaks | `environment.md` → Adaptation Layer |
| Guardrails, safety, quality, validation, security | `environment.md` → Protection Layer |
| Goals of the system | `music.md` → Purpose |
| Prioritization, filtering, confidence, qualification, estimation | `music.md` → Core Principles |
| Success criteria, measurement, evaluation, trade-offs | `music.md` → Value Logic |
| Invariant should / should-not rules, how choices are made | `music.md` → Decision Logic |
| The actual records being processed right now | **Current data** (not in any of the four files) |

### Commonly confused items
- **Reasoning:** *How the AI thinks in general* goes in `person.md`. *The solution's own reasoning rules* (prioritization, filtering, decisions) go in `music.md`. Neither belongs in `environment.md`.
- **Data:** Data and data mappings live **only** in `environment.md`. `person.md` and `music.md` both explicitly exclude raw data.
- **Security:** Security lives **only** in `environment.md` (Protection Layer). `person.md` and `music.md` both explicitly exclude it.
- **UI and styling:** Both live **only** in `environment.md`, as separate layers. Both `person.md` and `music.md` exclude them, and `instrument-awareness.md` excludes UI definitions.
- **Technical limits:** Model and platform limits belong in `instrument-awareness.md`. `person.md` and `music.md` both exclude them.

---

## 7. Quick Reference

```
WHO   performs the work?             → person.md (player.md)
WHAT  tool is being used?            → instrument-awareness.md
WHERE does the work happen?          → environment.md
WHY & HOW is value created?          → music.md
```

| File | Role | Protect priority |
|---|---|---|
| `person.md` (player.md) | How the AI thinks | After `music.md` |
| `instrument-awareness.md` | How the AI uses the model | After `music.md` |
| `environment.md` | Where the AI operates | After `music.md` |
| `music.md` | Why the AI exists and how value is created | **Preserve first: this is the IP** |

> **Ensemble in one sentence:** Keep the player, the instrument, the venue, and the music in separate files, feed in current data, and the performance takes care of itself.
