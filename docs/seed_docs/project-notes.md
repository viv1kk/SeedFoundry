# Systems --- Autonomous Analytical System

## Extended Project Context, Product Vision, Architecture and Demo Specification

> **Purpose of this document:**\
> This document is the detailed context/specification to give Claude
> Code before beginning implementation planning. It explains the
> conceptual system, methodology, lifecycle, demo behavior, UI intent,
> architecture principles, and MVP boundaries.
>
> **Important:** This is a planning/specification document, not an
> instruction to immediately generate the entire application. Claude
> Code should first understand the system, identify architectural
> decisions, surface ambiguities, and propose an implementation plan.
>
> **Status, 2026-10-02:** planning is long done and the build is complete
> through M22. Sections 1--82 remain the product vision, which V1 does
> not fully build. Section 83 was the first V1 specification and is
> superseded in detail by `requirements.md`. Section 84 records the
> Seeding and Life rework and, in §84.5, the build log of every
> milestone since M11. See `README.md` for how the documents relate.

------------------------------------------------------------------------

# 1. Executive Summary

The project is a simulation of an **autonomous enterprise analytical
system**.

The fundamental idea is that the system is not simply an AI chatbot, an
agent framework, or a dashboard generator.

Instead, the system contains a **problem-solving methodology** as its
internal "intelligence". This methodology can be planted into a client
environment, where autonomous agents discover the available enterprise
systems and data, assess whether the methodology can be applied, build
analytical solutions, and eventually expose those solutions through
interactive dashboards.

The conceptual lifecycle is:

``` text
             SEED
               │
               ▼
             INIT
               │
               ▼
          DISCOVERY
               │
               ▼
        ASSESSMENT / GROWTH
               │
          HUMAN APPROVAL
               │
               ▼
         IMPLEMENTATION
               │
          HUMAN CONFIRMATION
               │
               ▼
       DEPLOYMENT / RUN
               │
               ▼
           ANALYTICS
```

For the initial demo, the entire enterprise environment and agent
execution can be **simulated**.

The goal is to demonstrate the *behavior and architecture of the
eventual system* without first having to implement real
ServiceNow/SAP/network discovery, production credentials, autonomous
code generation, or cloud deployment.

------------------------------------------------------------------------

# 2. The Problem This System Is Trying to Solve

The organization has methodologies for solving enterprise problems such
as:

-   Application Portfolio Rationalization
-   Ticket Anomaly Detection
-   License Optimization

These exercises are not merely collections of predefined reports.

They follow a common underlying approach to problem solving:

1.  Start from first principles.
2.  Remove irrelevant noise.
3.  Understand the actual problem.
4.  Identify the relevant data.
5.  Assess data quality and sufficiency.
6.  Establish measurable baselines.
7.  Form hypotheses.
8.  Test hypotheses against evidence.
9.  Use mathematics/statistics where appropriate.
10. Use machine learning where it provides value.
11. Validate conclusions.
12. Derive recommendations from evidence.
13. Make assumptions explicit.
14. Escalate ambiguity to a human when necessary.

The proposed system attempts to **encode this methodology into a
reusable autonomous system**.

Instead of a consulting/analytical team manually repeating the same
methodology for every client, the system should eventually be able to
take the methodology, understand a new environment, discover available
evidence, adapt the methodology to that environment, and construct the
appropriate analytical solution.

------------------------------------------------------------------------

# 3. The Seed Analogy

The system is intentionally modeled around a **seed** analogy.

The seed contains the conceptual intelligence needed for the system to
operate.

The seed is planted into an unknown client environment.

The system then:

``` text
Seed
 │
 ├── Understand itself
 │
 ├── Understand the environment
 │
 ├── Determine what can grow
 │
 ├── Build the appropriate solution
 │
 └── Produce useful analytical output
```

This is not intended merely as a visual metaphor.

It should influence the architecture:

-   The Core should remain largely environment-independent.
-   The Adaptation layer should learn how to connect the Core to a
    particular environment.
-   The Protection layer should constrain what the system is allowed to
    do.
-   The system should progressively accumulate knowledge about its
    environment.
-   Solutions should emerge from the interaction between methodology and
    environment.

------------------------------------------------------------------------

# 4. Three Persistent Layers

There are three conceptual layers.

They are **not lifecycle stages**.

They persist throughout the lifecycle and have different
responsibilities.

``` text
                    ┌───────────────────────────┐
                    │     PROTECTION LAYER       │
                    │                           │
                    │ Security / Governance     │
                    │ Agent permissions         │
                    │ Data integrity            │
                    │ Human approvals           │
                    │ Policy enforcement        │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │      ADAPTATION LAYER     │
                    │                           │
                    │ Environment discovery     │
                    │ Connectors                │
                    │ Schema understanding      │
                    │ Data mapping              │
                    │ Source assessment         │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │         CORE LAYER        │
                    │                           │
                    │ Methodology               │
                    │ Domain knowledge          │
                    │ Mathematics               │
                    │ Statistics                │
                    │ ML approaches             │
                    │ Hypothesis testing        │
                    │ Evidence requirements     │
                    └───────────────────────────┘
```

------------------------------------------------------------------------

# 5. Core Layer

## 5.1 Purpose

The Core is the intellectual foundation of the system.

It answers:

> **"How should this problem be thought about and solved?"**

It should contain the methodology independent of a particular client.

For example, the Core may know:

-   What Application Portfolio Rationalization means.
-   What evidence is required to determine whether an application is a
    candidate for retirement.
-   How to establish usage baselines.
-   How to identify dependencies.
-   What assumptions invalidate a conclusion.
-   What statistical methods are appropriate for a particular question.
-   When ML is justified.
-   How anomalies should be validated.
-   What constitutes sufficient evidence.

------------------------------------------------------------------------

## 5.2 The Core is NOT simply a document repository

For the demo, Markdown can be the input format.

For example:

``` text
core.md
```

However, the conceptual architecture should not assume:

``` text
Markdown → RAG → LLM → answer
```

That would make the system little more than a chatbot with
documentation.

Instead, think of the Core as containing several types of knowledge:

``` text
CORE
│
├── Concepts
│
├── Methodologies
│
├── Procedures
│
├── Mathematical methods
│
├── Statistical methods
│
├── ML methods
│
├── Hypothesis templates
│
├── Evidence requirements
│
├── Assumptions
│
├── Validation rules
│
├── Failure modes
│
└── Decision frameworks
```

Eventually, the human-authored knowledge may be compiled into structured
representations.

For example:

``` text
Human-authored Markdown/YAML
            │
            ▼
      Knowledge Loader
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
    Rules  Methods Concepts
      │     │     │
      └─────┼─────┘
            ▼
     Runtime Knowledge
```

The MVP does not need to implement a sophisticated knowledge compiler.

------------------------------------------------------------------------

# 6. Adaptation Layer

The Adaptation layer answers:

> **"How do I apply the methodology to this specific client
> environment?"**

The Core may say:

> "License optimization requires entitlement, assignment, usage and cost
> information."

The Adaptation layer determines:

``` text
Where is entitlement information?

Where is assignment information?

Where is usage information?

Where is cost information?

How do I retrieve each dataset?

What fields correspond to the concepts expected by the Core?

Are those fields complete and trustworthy?
```

This is what makes the methodology reusable across different client
environments.

------------------------------------------------------------------------

# 7. Discovery

The Adaptation layer initially acts like a scouting mechanism.

The system starts with incomplete knowledge.

The Discovery Agent explores the environment and builds an Environment
Registry.

Potential discovery mechanisms include:

-   Network discovery
-   Endpoint discovery
-   API discovery
-   Database discovery
-   Service identification
-   Configuration inspection
-   Data-source discovery
-   Admin-provided information

Example:

``` text
Unknown Client Environment

        ↓

ServiceNow discovered
SAP discovered
SQL Server discovered
License Management System discovered
Legacy system reported by Admin

        ↓

Environment Registry
```

------------------------------------------------------------------------

# 8. Admin-Provided Discovery Information

Not everything can be automatically discovered.

Some systems may:

-   Be isolated.
-   Require special procedures.
-   Be legacy systems.
-   Not expose discoverable endpoints.
-   Require explicit administrator knowledge.
-   Exist behind special network boundaries.

Therefore, Discovery must support human input.

Example:

``` text
AGENT:

I have discovered an application registry but cannot
determine whether it is authoritative.

Please provide information.

[ Application Registry is authoritative ]

[ SAP inventory is authoritative ]

[ Both are required ]
```

Another example:

``` text
AGENT:

A legacy license database was reported by the administrator.

Please provide:

Connection method
Credentials
Read-only access

[ Configure ]
```

------------------------------------------------------------------------

# 9. Protection Layer

The Protection Layer is cross-cutting.

It exists throughout:

``` text
INIT
DISCOVERY
ASSESSMENT
IMPLEMENTATION
DEPLOYMENT
RUN
```

It should govern:

-   Identity
-   Authentication
-   Authorization
-   Credentials
-   Tool access
-   Data access
-   Data movement
-   Agent capabilities
-   Human approvals
-   Destructive operations
-   Evidence integrity
-   Hypothesis validation
-   Auditability

The key philosophy is:

> **The system can be autonomous, but autonomy exists inside hard
> boundaries.**

------------------------------------------------------------------------

# 10. Protection Should Not Be Prompt-Only

A critical architectural principle:

Do not rely entirely on an LLM instruction such as:

``` text
"Do not delete production data."
```

Instead:

``` text
Agent
  ↓
Tool request
  ↓
Policy engine
  ↓
Allowed / Denied / Human approval
  ↓
Tool execution
```

For example:

``` text
Read approved ServiceNow API
        ↓
Allowed

Create temporary analytical dataset
        ↓
Allowed

Deploy production service
        ↓
Human approval

Delete source records
        ↓
Denied
```

For the MVP these can be simulated, but the architecture should leave
room for real enforcement later.

------------------------------------------------------------------------

# 11. Lifecycle

The demo lifecycle is:

``` text
INIT
 ↓
DISCOVERY
 ↓
ASSESSMENT / GROWTH
 ↓
HUMAN APPROVAL
 ↓
IMPLEMENTATION
 ↓
DEPLOYMENT / RUN
 ↓
ANALYTICS
```

Evolution is intentionally excluded from V1.

------------------------------------------------------------------------

# 12. INIT Phase

The first screen should be minimal.

The user provides three Seed files:

``` text
Core
Adaptation
Protection
```

For example:

``` text
core.md
adaptation.md
protection.md
```

The UI should communicate:

> **Plant the Seed**

rather than looking like a generic file uploader.

Possible conceptual layout:

``` text
                    PLANT SYSTEMS

              Give the system its foundation.

       ┌──────────┐  ┌──────────────┐  ┌────────────┐
       │   CORE   │  │  ADAPTATION  │  │ PROTECTION │
       │    ✓     │  │      ✓       │  │     ✓      │
       └──────────┘  └──────────────┘  └────────────┘

                    [ Initialize ]
```

Once initialized, the system transitions into Discovery.

------------------------------------------------------------------------

# 13. Main UI Philosophy

After initialization, the user should enter a **persistent system
workspace**.

The page should not completely change between Discovery, Assessment and
Implementation.

Instead:

``` text
Same Workspace
      │
      ├── Lifecycle changes
      ├── Visualization changes
      ├── Activity changes
      ├── State changes
      └── Human input appears when needed
```

This gives the impression that a single system is operating continuously
underneath the UI.

------------------------------------------------------------------------

# 14. Lifecycle Visualization

A persistent lifecycle indicator should be visible.

Conceptually:

``` text
INIT ───── DISCOVERY ───── ASSESSMENT ───── IMPLEMENT ───── DEPLOY
                    ●
                 CURRENT
```

Completed phases should appear complete.

The current phase should have a subtle active state.

Future phases should remain inactive.

Avoid excessive animation.

The visualization should feel like an operating system, not a marketing
animation.

------------------------------------------------------------------------

# 15. Discovery Visualization

During Discovery, the environment should visually grow.

For example:

``` text
                   CLIENT ENVIRONMENT

                          SYSTEM
                         /      \
                  ServiceNow    SAP
                       |
                   SQL Server
                       |
               License Database
```

As the agent discovers systems, nodes can appear progressively.

Potential states:

``` text
Unknown
  ↓
Detected
  ↓
Reachability Testing
  ↓
Validated
  ↓
Understanding Data
  ↓
Registered
```

This is an important visual representation because the user should be
able to see that the agent is building an understanding of an initially
unknown environment.

------------------------------------------------------------------------

# 16. Agent Activity Log

The log is important but should not look like a raw developer terminal.

It should look like an **auditable activity stream**.

Example:

``` text
02:41:07  DISCOVERY
Scanning known enterprise endpoints...

02:41:12  DISCOVERY
ServiceNow endpoint detected

02:41:13  VALIDATION
Testing endpoint reachability...

02:41:14  SUCCESS
Endpoint reachable

02:41:15  DISCOVERY
Identified incident management API

02:41:18  ANALYSIS
Evaluating available incident fields...

02:41:21  WARNING
Authentication required

02:41:21  HUMAN INPUT REQUIRED
ServiceNow credentials are required
```

Potential categories:

``` text
DISCOVERY
ANALYSIS
VALIDATION
DECISION
WARNING
SUCCESS
HUMAN INPUT
```

The log should communicate what the system is doing without exposing
meaningless internal chain-of-thought.

Important distinction:

> Show **operational events and decision-relevant reasons**, not hidden
> model reasoning.

------------------------------------------------------------------------

# 17. Human-in-the-Loop Interaction

The human input interface should only appear when needed.

Do not permanently occupy screen space with an empty input panel.

Example:

``` text
────────────────────────────────────────

             HUMAN INPUT REQUIRED

ServiceNow requires authentication.

Required access:
Read-only Incident API

Reason:
Historical incident data is required for
Ticket Anomaly Detection.

              [ Configure ]

────────────────────────────────────────
```

After submission:

``` text
✓ Credentials configured

Agent continuing...
```

The panel disappears.

------------------------------------------------------------------------

# 18. Human Decision States

The system can encounter several types of human interaction.

## Credentials

``` text
Credentials required
```

## Ambiguity

``` text
Two sources appear to represent the same concept.
Which should be authoritative?
```

## Missing information

``` text
Application ownership information is unavailable.
Provide source or continue with reduced feasibility.
```

## Solution approval

``` text
Solution is ready for implementation.
Approve?
```

## Deployment confirmation

``` text
Solution has been built and validated.
Confirm run?
```

Human involvement should therefore be treated as an **escalation
mechanism**.

------------------------------------------------------------------------

# 19. Discovery Completion

When Discovery completes, the system should transition into an
assessment/reporting state.

Example:

``` text
DISCOVERY COMPLETE

7 Systems
14 Data Sources
31 Relevant Datasets
3 Applicable Methodologies
```

Then show the discovered environment:

``` text
ServiceNow              ✓ Connected
SAP                     ✓ Connected
SQL Server              ✓ Connected
License Database        ✓ Connected
Legacy Application DB   ⚠ Admin supplied
```

The system should then show which methodologies appear feasible.

------------------------------------------------------------------------

# 20. Assessment / Growth Phase

The Growth phase is the analytical heart of the demo.

The system evaluates:

``` text
Environment
    ↓
Available Data
    ↓
Data Quality
    ↓
Methodology Requirements
    ↓
Feasibility
    ↓
Potential Solution
```

The system should not assume that because a methodology exists, it can
automatically be executed.

Example:

``` text
License Optimization

Core requires:
- Entitlement
- Assignment
- Usage
- Cost

Available:
✓ Entitlement
✓ Assignment
✓ Usage
⚠ Cost information incomplete

Result:
Partial feasibility
```

The system can then recommend what would improve feasibility.

------------------------------------------------------------------------

# 21. Feasibility

Every proposed solution should have a clear assessment.

Potential attributes:

``` text
Feasibility
Data Sufficiency
Data Quality
Coverage
Methodology Match
Known Limitations
Missing Information
Expected Analytical Value
```

Example:

``` text
Ticket Anomaly Detection

Feasibility: HIGH

Data sufficiency: HIGH

Available:
✓ Historical tickets
✓ Resolution timestamps
✓ Assignment groups
✓ Priority
✓ Categories

Limitations:
• 8% of records have incomplete categorization

Recommendation:
Proceed
```

The exact numerical feasibility score can be simulated for the demo.

Do not imply that these values are real enterprise measurements.

------------------------------------------------------------------------

# 22. First-Principles Reasoning

The demo should demonstrate the methodology rather than merely state
that AI was used.

For example:

``` text
Question:
Are there anomalous ticket behaviors?

        ↓

Establish baseline

        ↓

Characterize normal behavior

        ↓

Identify deviations

        ↓

Form hypothesis

        ↓

Test against historical data

        ↓

Validate anomaly

        ↓

Quantify impact
```

The same principle should conceptually apply to the other methodologies.

------------------------------------------------------------------------

# 23. Evidence Chain

The system should maintain an evidence chain for conclusions.

Example:

``` text
CONCLUSION

Application X has retirement potential.

        │
        ├── Evidence
        │   ├── No production transactions in 180 days
        │   ├── No active users
        │   ├── Infrastructure cost
        │   └── No detected dependencies
        │
        ├── Hypothesis
        │   └── Application is no longer operationally required
        │
        ├── Validation
        │   ├── Usage analysis ✓
        │   ├── Dependency analysis ✓
        │   └── Owner verification ✓
        │
        ├── Assumption
        │   └── Monitoring coverage is complete
        │
        └── Recommendation
            Human approval required
```

This concept should be visible in the assessment/report experience.

------------------------------------------------------------------------

# 24. Solution List

After Discovery and Assessment, the system should list potential
solutions.

Initial methodologies:

``` text
1. Ticket Anomaly Detection
2. License Optimization
3. Application Portfolio Rationalization
```

Example solution card:

``` text
┌───────────────────────────────────────────┐
│ Ticket Anomaly Detection                  │
│                                           │
│ Feasibility                        High   │
│ Data Sufficiency                   High   │
│                                           │
│ Evidence available: 6 / 6               │
│                                           │
│ Detect anomalous ticket patterns and      │
│ identify operational risk.                │
│                                           │
│ [ Review ]       [ Approve ]              │
└───────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 25. Assessment Report

Clicking Review should expose the detailed assessment.

It does not necessarily need to navigate away from the main workspace.

A drawer/modal/detail panel is appropriate.

Example structure:

``` text
TICKET ANOMALY DETECTION

Why is this feasible?

✓ Historical ticket data
✓ Resolution timestamps
✓ Assignment groups
✓ Priority information
✓ Incident categories
✓ Sufficient historical volume

────────────────────────

Methodology

Baseline
   ↓
Statistical characterization
   ↓
Pattern detection
   ↓
Anomaly identification
   ↓
ML validation

────────────────────────

Limitations

• Historical data begins in 2023
• 8% of tickets lack categorization
• Some SAP-linked tickets cannot be correlated

────────────────────────

[ Approve Solution ]
```

------------------------------------------------------------------------

# 26. Approval

A solution cannot automatically move to implementation.

The Admin explicitly approves it.

Possible state transition:

``` text
PROPOSED
   ↓
AWAITING_APPROVAL
   ↓
APPROVED
   ↓
IMPLEMENTATION
```

If rejected:

``` text
PROPOSED
   ↓
REJECTED
```

The system should preserve the decision in System State.

------------------------------------------------------------------------

# 27. Implementation Phase

After approval, the same main workspace remains.

The lifecycle changes:

``` text
INIT → DISCOVERY → ASSESSMENT → IMPLEMENTATION → DEPLOYMENT
```

The visualization can change from an environment graph into a solution
architecture/build graph.

Example:

``` text
ServiceNow
     ↓
Data Ingestion
     ↓
Normalization
     ↓
Feature Pipeline
     ↓
┌──────────────────────┐
│ Analytical Engine    │
│                      │
│ Statistical Analysis │
│ + ML                  │
└──────────┬───────────┘
           ↓
      Analytics API
           ↓
       Dashboard
```

------------------------------------------------------------------------

# 28. Implementation Activity

The activity stream should show realistic progress.

Example:

``` text
BUILD

Generated data ingestion service
Generated schema validation
Generated normalization pipeline
Generated feature pipeline
Generated anomaly detection engine
Generated analytical APIs
Generated dashboard
Running unit tests
Running integration tests
Validating analytical output
```

For V1, these are simulated operations.

------------------------------------------------------------------------

# 29. Technical Stack

Preferred stack:

## Backend

-   Python
-   FastAPI

## Frontend

-   Vue.js
-   Or another frontend framework if there is a strong reason

## Visualization

-   Plotly or another mature interactive visualization library

## Packaging

-   Docker

The eventual system should have a preferred stack but not an absolute
restriction.

Conceptually:

``` text
Preferred Stack
      ↓
Can deviate if justified
      ↓
Compatibility + Security + Maintainability
```

------------------------------------------------------------------------

# 30. Deployment Phase

Actual infrastructure deployment is outside V1.

The demo focuses on the logical deployment/run lifecycle.

At the end of implementation:

``` text
SYSTEM READY

3 solutions implemented.

Ticket Anomaly Detection
Status: Ready
[ Run ]

License Optimization
Status: Ready
[ Run ]

Application Portfolio Rationalization
Status: Ready
[ Run ]
```

The Admin can select a solution and run it.

------------------------------------------------------------------------

# 31. Analytics Dashboard

The final output should be a real analytical application, not a static
report.

The dashboard should feel like a high-performance enterprise analytics
product.

For V1, Ticket Anomaly Detection can be the primary fully polished
dashboard.

Potential dashboard:

``` text
Ticket Intelligence

Total Tickets     Anomalies     Avg Resolution     Risk
184,392           1,842         6.4h               3.8%
```

Then interactive charts.

------------------------------------------------------------------------

# 32. Interactive Charts

This is a hard requirement.

Charts must support actual interaction.

Examples:

-   Hover tooltips
-   Click selection
-   Cross-filtering
-   Time-range filtering
-   Category filtering
-   Entity filtering
-   Drill-down
-   Breadcrumb navigation
-   Table views
-   Detail panels

The dashboard should not contain charts that are merely decorative.

------------------------------------------------------------------------

# 33. Drill-Down Model

A user should be able to move from high-level analytics to underlying
evidence.

Example:

``` text
All Tickets
    ↓
Anomalous Tickets
    ↓
Reassignment Anomalies
    ↓
Assignment Group: Network Operations
    ↓
Ticket Cluster
    ↓
Individual Tickets
    ↓
Evidence
```

Another example:

``` text
Application Portfolio
       ↓
Business Unit
       ↓
Application
       ↓
Usage Pattern
       ↓
Dependency
       ↓
Underlying Records
```

The exact drill-down structure depends on the methodology.

------------------------------------------------------------------------

# 34. Dashboard Cross-Filtering

Interactions should propagate.

Example:

User clicks:

``` text
Network Operations
```

Then the rest of the dashboard automatically updates:

``` text
Ticket count
Anomaly count
Resolution trend
Priority distribution
Application distribution
Top anomaly patterns
```

This should feel like a real analytical workspace.

------------------------------------------------------------------------

# 35. Evidence From Dashboard

A user should be able to ask "why?" through interaction.

For example:

``` text
1,842 anomalous tickets
        ↓ click
614 reassignment anomalies
        ↓ click
Network Operations
        ↓ click
Cluster #27
```

Then:

``` text
WHY WAS THIS FLAGGED?

Pattern:
Repeated reassignment

Observed:
7.2 average assignments

Baseline:
2.1 average assignments

Deviation:
+242%

Evidence:
• Comparable historical tickets
• Statistical baseline
• Model result
• Source records

[ View underlying records ]
```

This is critical to the philosophy.

The dashboard should connect:

``` text
Result
 ↓
Pattern
 ↓
Data
 ↓
Evidence
 ↓
Methodology
```

------------------------------------------------------------------------

# 36. Analytics Philosophy

The dashboard should demonstrate that the system is not just producing
an answer.

It is producing:

``` text
Answer
+
Evidence
+
Context
+
Drill-down
+
Traceability
```

The user should be able to investigate the result.

------------------------------------------------------------------------

# 37. System State

Agents should not be the source of truth.

The system should maintain a persistent conceptual state.

Example:

``` text
SYSTEM STATE

Environment
├── Systems
├── Services
├── Data Sources
├── Schemas
└── Credential References

Knowledge
├── Methodologies
├── Concepts
├── Rules
└── Procedures

Assessments
├── Data Quality
├── Feasibility
├── Hypotheses
└── Evidence

Solutions
├── Proposed
├── Approved
├── Building
├── Ready
├── Running
└── Failed

Human Decisions
├── Inputs
├── Approvals
└── Rejections

History
└── Events
```

This is important for resilience.

If an agent stops:

``` text
Agent fails
   ↓
System State remains
   ↓
Another agent/process can resume
   ↓
Continue from last valid state
```

------------------------------------------------------------------------

# 38. Event-Driven Model

The UI should ideally react to events rather than directly knowing how
agents work.

Example event:

``` json
{
  "type": "RESOURCE_DISCOVERED",
  "phase": "DISCOVERY",
  "resource": "ServiceNow",
  "status": "detected"
}
```

Another:

``` json
{
  "type": "HUMAN_INPUT_REQUIRED",
  "inputType": "credentials",
  "resource": "ServiceNow",
  "requiredScope": "read-only"
}
```

Another:

``` json
{
  "type": "SOLUTION_PROPOSED",
  "solutionId": "ticket-anomaly",
  "feasibility": "high"
}
```

The UI consumes the event stream and updates itself.

------------------------------------------------------------------------

# 39. Suggested Event Types

``` text
SYSTEM_INITIALIZED

PHASE_STARTED
PHASE_COMPLETED

AGENT_STARTED
AGENT_COMPLETED

DISCOVERY_STARTED
RESOURCE_DISCOVERED
RESOURCE_VALIDATED
DATA_SOURCE_IDENTIFIED
SCHEMA_DISCOVERED

HUMAN_INPUT_REQUIRED
HUMAN_INPUT_RECEIVED

ASSESSMENT_STARTED
DATA_QUALITY_ASSESSED
HYPOTHESIS_FORMED
HYPOTHESIS_VALIDATED
SOLUTION_PROPOSED

APPROVAL_REQUIRED
SOLUTION_APPROVED
SOLUTION_REJECTED

IMPLEMENTATION_STARTED
COMPONENT_BUILD_STARTED
COMPONENT_BUILD_COMPLETED
TEST_STARTED
TEST_COMPLETED

DEPLOYMENT_READY
SOLUTION_STARTED
SOLUTION_COMPLETED

WARNING
ERROR
```

------------------------------------------------------------------------

# 40. Agent Simulation

For the MVP, do not implement a fully autonomous LLM agent system.

Create an **Agent Simulation Engine**.

The simulation should behave like an agent.

For example:

``` text
DiscoveryAgent

1. Start discovery
2. Scan environment
3. Detect ServiceNow
4. Test reachability
5. Request credentials
6. Pause
7. Receive credentials
8. Continue
9. Discover SAP
10. Discover SQL Server
11. Discover License DB
12. Complete discovery
```

The important part is the event sequence and state transitions.

The eventual real agent runtime can replace the simulator.

------------------------------------------------------------------------

# 41. Replaceability

Architect the simulation so that later:

``` text
                 Event Interface
                       ▲
                       │
          ┌────────────┴────────────┐
          │                         │
   Simulation Engine          Real Agent Runtime
          │                         │
          └────────────┬────────────┘
                       ▼
                      UI
```

The frontend should not care whether an event came from:

-   A simulator
-   An LLM agent
-   A deterministic worker
-   A real connector
-   A future orchestration engine

This is one of the most important architectural goals for V1.

------------------------------------------------------------------------

# 42. Mock Client Environment

Use one fictional client environment.

Example:

``` text
Client: ACME Enterprise

Systems:

ServiceNow
SAP
SQL Server
License Management System
Legacy Application Registry
```

The simulated environment should contain enough data to make the demo
believable.

------------------------------------------------------------------------

# 43. Initial Methodologies

Use three methodologies in the demo:

## Ticket Anomaly Detection

Inputs:

-   Ticket history
-   Priority
-   Assignment groups
-   Resolution time
-   Categories
-   Reassignment history

Outputs:

-   Anomalous tickets
-   Anomaly patterns
-   Risk categories
-   Trends
-   Root patterns
-   Interactive drill-down

------------------------------------------------------------------------

## License Optimization

Inputs:

-   License entitlements
-   Assignments
-   Usage
-   Costs

Outputs:

-   Unused licenses
-   Underutilized licenses
-   Potential optimization
-   Cost impact

The implementation can initially be simplified.

------------------------------------------------------------------------

## Application Portfolio Rationalization

Inputs:

-   Application inventory
-   Usage
-   Ownership
-   Cost
-   Dependencies
-   Business metadata

Outputs:

-   Candidate applications
-   Rationalization categories
-   Dependency analysis
-   Cost/usage insights

Again, this can initially be simulated.

------------------------------------------------------------------------

# 44. V1 Recommendation

Do not fully implement three complex analytical products.

Instead:

``` text
Ticket Anomaly Detection
        ↓
Fully polished end-to-end dashboard

License Optimization
        ↓
Functional simulated solution

Application Portfolio Rationalization
        ↓
Functional simulated solution
```

This gives the demo breadth without sacrificing quality.

------------------------------------------------------------------------

# 45. Data Strategy for Demo

Use deterministic mock data.

Avoid random data that changes on every run unless randomness is
explicitly useful.

Deterministic data makes:

-   Testing easier
-   Screenshots reproducible
-   Demo behavior predictable
-   Drill-down relationships reliable
-   Agent simulation easier to debug

The mock data should contain deliberate patterns.

For example:

``` text
Ticket population
    ↓
Normal tickets
    ↓
Several intentionally anomalous clusters
```

Then the analytical result can be deterministic.

------------------------------------------------------------------------

# 46. Simulation Timing

The system should progress progressively rather than instantly.

Example:

``` text
Scanning...
      1 sec

ServiceNow detected
      0.8 sec

Testing reachability...
      1 sec

Reachability confirmed
      0.7 sec

Inspecting schema...
      1.5 sec
```

The exact timing is not important.

The purpose is to create the perception of an active system.

However:

-   Do not make the demo unnecessarily slow.
-   Provide a sensible fast/demo mode if useful.
-   Avoid fake animations that do not correspond to state changes.

------------------------------------------------------------------------

# 47. UI Design Direction

The interface should be:

-   Minimal
-   Beautiful
-   Technical
-   Premium
-   Calm
-   Information-dense without being cluttered
-   Dark/light theme can be evaluated during implementation
-   Strong typography
-   Subtle animation
-   Clear hierarchy

Avoid:

-   Excessive gradients
-   Generic "AI" glowing effects
-   Robot/agent illustrations
-   Excessive cards
-   Fake futuristic styling
-   Too many colors
-   Excessive motion

The visual language should communicate:

> serious analytical infrastructure

rather than:

> AI toy / chatbot.

------------------------------------------------------------------------

# 48. The Seed Screen

The first screen can be intentionally sparse.

Concept:

``` text
                         SYSTEMS

                  Plant the methodology.

       Core           Adaptation           Protection
       ┌───┐          ┌─────┐              ┌───┐
       │ + │          │  +  │              │ + │
       └───┘          └─────┘              └───┘

                 [ Plant Seed ]
```

After upload:

``` text
Core          ✓
Adaptation    ✓
Protection    ✓

              [ Initialize ]
```

The actual visual implementation can be determined later.

------------------------------------------------------------------------

# 49. Main Workspace

Conceptual structure:

``` text
┌───────────────────────────────────────────────────────────────┐
│ SYSTEMS                                      DISCOVERY ●       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│              INIT ─ DISCOVERY ─ ASSESS ─ BUILD ─ DEPLOY       │
│                          ●                                    │
│                                                               │
├──────────────────────────────────┬────────────────────────────┤
│                                  │                            │
│        ENVIRONMENT               │        ACTIVITY            │
│                                  │                            │
│      ServiceNow                 │  Detecting ServiceNow      │
│           │                      │  Testing endpoint          │
│      ┌────┴────┐                 │  API identified            │
│      SAP     SQL Server          │  Credentials required      │
│                                  │                            │
├──────────────────────────────────┴────────────────────────────┤
│                                                               │
│                   HUMAN INPUT / STATUS                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

This is conceptual, not a final UI requirement.

------------------------------------------------------------------------

# 50. Discovery Visualization

The environment visualization can be graph-like.

Nodes:

``` text
Client
System
Service
API
Database
Dataset
```

Edges:

``` text
contains
connects to
provides
depends on
```

As the agent discovers resources, nodes become visible.

Potential statuses:

``` text
discovering
detected
testing
validated
requires-input
connected
error
```

------------------------------------------------------------------------

# 51. Assessment Visualization

After Discovery, the environment graph may transition into a
methodology/solution view.

Conceptually:

``` text
Discovered Data
      │
      ├───────────────┐
      ▼               ▼
Ticket Method     License Method
      │               │
      ▼               ▼
High Feasibility  Medium Feasibility
      │               │
      ▼               ▼
Approved?         Needs data
```

This is where the system demonstrates that it is **reasoning about what
can actually be done**.

------------------------------------------------------------------------

# 52. Implementation Visualization

During build:

``` text
Data Source
     ↓
Ingestion
     ↓
Normalization
     ↓
Analysis
     ↓
API
     ↓
Dashboard
```

Nodes can progress through:

``` text
Pending
Building
Testing
Validated
Complete
```

------------------------------------------------------------------------

# 53. Deployment/Run

At deployment/run:

``` text
Implemented Solutions

┌───────────────────────────────────────────┐
│ Ticket Anomaly Detection                  │
│ Ready                                     │
│ [ Run ]                                   │
└───────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│ License Optimization                      │
│ Ready                                     │
│ [ Run ]                                   │
└───────────────────────────────────────────┘
```

Clicking Run should transition to the corresponding analytical
dashboard.

------------------------------------------------------------------------

# 54. Dashboard: Ticket Anomaly Detection

Potential top-level metrics:

``` text
Total Tickets
Anomalies
Average Resolution Time
Anomaly Rate
```

Potential charts:

``` text
Ticket volume over time
Anomaly trend
Anomaly category distribution
Anomaly by priority
Anomaly by assignment group
Resolution time distribution
Top anomaly patterns
```

Every meaningful chart should be interactive.

------------------------------------------------------------------------

# 55. Dashboard Drill-Down

Example:

``` text
Anomaly Trend
       ↓ click month
June
       ↓
Anomaly Categories
       ↓ click category
Reassignment
       ↓
Assignment Groups
       ↓ click group
Network Operations
       ↓
Ticket Clusters
       ↓
Underlying Tickets
       ↓
Evidence
```

The dashboard should maintain a breadcrumb:

``` text
All Tickets
 / June 2026
 / Reassignment
 / Network Operations
 / Cluster 27
```

The user should be able to go backward.

------------------------------------------------------------------------

# 56. Drill-Down Data Model

The data model should support relationships such as:

``` text
Dashboard Metric
      ↓
Chart Point
      ↓
Filter Context
      ↓
Entity
      ↓
Record
      ↓
Evidence
```

Do not implement drill-down merely as hardcoded UI navigation.

The eventual architecture should allow different methodologies to define
different analytical hierarchies.

------------------------------------------------------------------------

# 57. Dashboard Evidence Panel

A detail panel can expose:

``` text
Finding

Repeated reassignment anomaly

Observed:
7.2 assignments

Baseline:
2.1 assignments

Deviation:
+242%

Comparable population:
1,284 tickets

Evidence:
- Historical ticket data
- Assignment history
- Resolution data

Methodology:
Ticket Anomaly Detection

Validation:
Statistical baseline
ML anomaly model
```

Again, the numbers can be deterministic mock values.

------------------------------------------------------------------------

# 58. Backend State Model

Possible high-level state:

``` text
System
│
├── seed
│
├── lifecycle
│
├── environment
│
├── assessments
│
├── solutions
│
├── approvals
│
├── implementations
│
├── runtime
│
└── events
```

Example lifecycle:

``` text
INITIALIZED
DISCOVERING
DISCOVERY_BLOCKED
DISCOVERY_COMPLETE
ASSESSING
AWAITING_APPROVAL
IMPLEMENTING
IMPLEMENTATION_COMPLETE
READY_TO_RUN
RUNNING
COMPLETED
```

------------------------------------------------------------------------

# 59. State Machine

A formal state machine is preferable to scattered boolean flags.

Example:

``` text
INIT
 ↓
DISCOVERY
 ↓
ASSESSMENT
 ↓
AWAITING_APPROVAL
 ↓
IMPLEMENTATION
 ↓
READY
 ↓
RUNNING
 ↓
COMPLETED
```

With human-intervention substates:

``` text
DISCOVERY
   ↓
WAITING_FOR_HUMAN
   ↓
DISCOVERY
```

This will make the simulator and UI easier to reason about.

------------------------------------------------------------------------

# 60. Error Handling

The demo should include meaningful failure states.

Examples:

``` text
Endpoint unreachable
Schema mismatch
Insufficient data
Credential missing
Hypothesis rejected
Implementation test failed
```

The system should not simply pretend everything always works.

A believable autonomous system needs to demonstrate that it can
encounter uncertainty and recover or escalate.

For example:

``` text
ServiceNow API reachable
        ↓
Schema inspection
        ↓
Required field missing
        ↓
Assessment degraded
        ↓
Human input requested
```

------------------------------------------------------------------------

# 61. Human Decision vs Error

Do not confuse these.

### Error

Something went wrong technically.

Example:

``` text
Connection failed
```

### Human decision

The system has multiple legitimate choices.

Example:

``` text
Two authoritative data sources detected.
Which one should be used?
```

### Insufficient evidence

The system cannot responsibly conclude something.

Example:

``` text
Application retirement cannot be recommended
because ownership information is missing.
```

These should have different UI states.

------------------------------------------------------------------------

# 62. Security Simulation

For V1, security can be simulated.

However, the demo should conceptually show:

``` text
Agent requests action
        ↓
Protection Layer evaluates
        ↓
Allowed
OR
Human approval
OR
Denied
```

This is enough to demonstrate the architectural principle.

Do not build real credential storage or enterprise security
infrastructure for V1 unless required by implementation constraints.

------------------------------------------------------------------------

# 63. What Should Be Real vs Simulated

## Real

-   UI
-   State machine
-   Event streaming
-   File upload
-   Seed parsing/validation
-   Human interaction
-   Solution lifecycle
-   Dashboard rendering
-   Chart interaction
-   Drill-down
-   Backend/frontend communication
-   Deterministic data model

## Simulated

-   Enterprise discovery
-   ServiceNow connection
-   SAP connection
-   Network scanning
-   Credential validation
-   Agent reasoning
-   Code generation
-   ML training
-   Production deployment

This boundary should remain clear in the architecture.

------------------------------------------------------------------------

# 64. Suggested Demo Backend

Initial architecture:

``` text
Vue.js
   │
   │ SSE/WebSocket
   ▼
FastAPI
   │
   ├── Lifecycle Manager
   │
   ├── Event Manager
   │
   ├── Simulation Engine
   │
   ├── State Manager
   │
   ├── Seed Loader
   │
   └── Mock Data
```

Potentially:

``` text
SQLite
```

for persistence if useful.

Do not introduce Kafka, Redis, Kubernetes, or other distributed
infrastructure simply because the eventual production system might use
them.

The demo should remain simple.

------------------------------------------------------------------------

# 65. Why Event Streaming Matters

The system should feel alive.

A traditional request/response flow:

``` text
POST /discover
     ↓
wait 30 seconds
     ↓
return everything
```

does not convey the intended experience.

Instead:

``` text
Start discovery
     ↓
Event stream

DISCOVERY_STARTED
RESOURCE_DISCOVERED
RESOURCE_VALIDATED
HUMAN_INPUT_REQUIRED
HUMAN_INPUT_RECEIVED
RESOURCE_DISCOVERED
...
DISCOVERY_COMPLETED
```

This gives the UI a continuous stream of system activity.

SSE may be sufficient for V1.

WebSockets can be used if bidirectional communication becomes useful.

------------------------------------------------------------------------

# 66. Seed File Format

For V1, Markdown is preferred because it is:

-   Human-readable
-   Easy to edit
-   Easy to demo
-   Easy to version-control

Potential structure:

``` markdown
# Methodology

## Purpose

...

## Principles

...

## Required Evidence

...

## Analysis Process

...

## Validation Rules

...
```

The exact structure should be determined during implementation planning.

Do not over-engineer the knowledge representation before understanding
what the demo actually needs.

------------------------------------------------------------------------

# 67. Seed Loading

When the user uploads the Seed:

``` text
Upload
 ↓
Validate
 ↓
Parse
 ↓
Register
 ↓
Initialize System State
 ↓
Start Lifecycle
```

The system should show that the Seed has actually been loaded.

Potential UI:

``` text
CORE
✓ Loaded
✓ Parsed

ADAPTATION
✓ Loaded
✓ Parsed

PROTECTION
✓ Loaded
✓ Parsed

SYSTEM READY
```

------------------------------------------------------------------------

# 68. Demo Script

The demo should be possible to run as a controlled narrative.

Recommended sequence:

### Step 1

Upload Seed.

### Step 2

Plant Seed.

### Step 3

Discovery starts.

### Step 4

ServiceNow is detected.

### Step 5

ServiceNow reachability is tested.

### Step 6

Credentials are requested.

### Step 7

Admin provides credentials.

### Step 8

Discovery continues.

### Step 9

SAP, SQL Server and other sources are discovered.

### Step 10

Discovery completes.

### Step 11

System evaluates methodologies.

### Step 12

Assessment reports appear.

### Step 13

Admin reviews and approves Ticket Anomaly Detection.

### Step 14

Implementation begins.

### Step 15

Backend, analytical engine and dashboard are "built".

### Step 16

Tests run.

### Step 17

Solution becomes ready.

### Step 18

Admin runs solution.

### Step 19

Interactive dashboard opens.

### Step 20

User drills down from an anomaly to evidence.

This should be a smooth, impressive end-to-end story.

------------------------------------------------------------------------

# 69. What the Demo Should Communicate

By the end, a viewer should understand:

### The system has methodology.

It is not simply prompting an LLM.

### The system understands environments.

It discovers and maps client systems.

### The system adapts.

The same methodology can operate against different environments.

### The system is governed.

Agents cannot arbitrarily do anything.

### Humans remain decision authorities.

Humans intervene at meaningful boundaries.

### Conclusions are evidence-driven.

The system can trace findings back to data.

### Solutions are constructed.

The system moves beyond analysis into implementation.

### The result is useful.

The final product is an interactive analytical application.

------------------------------------------------------------------------

# 70. What the Project Is NOT

Do not turn V1 into:

-   A generic chatbot
-   A ChatGPT clone
-   A generic RAG application
-   A static BI dashboard
-   A CRUD application
-   A collection of fake AI agents
-   A generic LangChain demo
-   A dashboard with random generated logs
-   A complicated microservice architecture
-   A real enterprise integration platform

The core concept is:

> **Methodology-driven autonomous analytical execution.**

------------------------------------------------------------------------

# 71. Architecture Principle: Methodology Over Model

The LLM is not the product.

The methodology is the product.

An LLM may help:

-   Interpret ambiguous data
-   Map concepts
-   Generate hypotheses
-   Choose analytical methods
-   Generate implementation code
-   Explain findings

But the system should maintain deterministic structure around it:

``` text
Methodology
     ↓
Constraints
     ↓
Data
     ↓
Analysis
     ↓
Evidence
     ↓
Conclusion
```

The LLM should operate within that system.

------------------------------------------------------------------------

# 72. Architecture Principle: Evidence Over Assertions

The system should not allow:

``` text
LLM says X
      ↓
X becomes truth
```

Instead:

``` text
Hypothesis
     ↓
Required evidence
     ↓
Data acquisition
     ↓
Validation
     ↓
Analysis
     ↓
Conclusion
```

This should influence the System State model.

------------------------------------------------------------------------

# 73. Architecture Principle: State Over Conversations

Agents should not maintain the entire system state only inside their
context window.

Instead:

``` text
System State
     ▲
     │
 Agent reads
     │
 Agent performs work
     │
 Agent writes
     ▼
System State
```

This provides:

-   Recovery
-   Auditing
-   Observability
-   Reproducibility
-   Multi-agent coordination later

------------------------------------------------------------------------

# 74. Architecture Principle: Human Escalation

Humans should not have to approve every action.

Instead:

``` text
Agent knows what to do
        ↓
Proceed

Agent lacks information
        ↓
Ask human

Agent reaches high-impact action
        ↓
Require approval

Policy prohibits action
        ↓
Deny
```

This gives the system meaningful autonomy.

------------------------------------------------------------------------

# 75. Architecture Principle: Progressive Replacement

The demo should be designed so that each simulated subsystem can later
be replaced.

Example:

``` text
Mock Discovery
     ↓
Real Discovery Agent

Mock ServiceNow
     ↓
Real ServiceNow Connector

Mock Assessment
     ↓
Real Methodology Engine

Mock Build
     ↓
Real Code-generation workflow

Mock Run
     ↓
Real Deployment/runtime
```

The UI should not need to be rewritten when this happens.

------------------------------------------------------------------------

# 76. V1 Scope

## Must Have

-   Seed upload
-   Seed validation
-   Three-layer Seed
-   Lifecycle state machine
-   Simulated Discovery
-   Mock client environment
-   Environment registry
-   Live event stream
-   Human input
-   Assessment
-   Feasibility
-   Solution proposal
-   Approval
-   Implementation simulation
-   Run flow
-   Interactive analytics dashboard
-   Drill-down
-   Evidence view

## Nice to Have

-   Persistent local state
-   Pause/resume
-   Restart from state
-   Failure/retry
-   Multiple solution runs
-   Rich environment graph
-   Detailed methodology viewer

## Explicitly Out of Scope

-   Evolution phase
-   Real ServiceNow integration
-   Real SAP integration
-   Real network scanning
-   Production credentials
-   Real cloud deployment
-   Real autonomous infrastructure modification
-   Full enterprise authentication
-   Multi-client production deployment
-   Complex distributed infrastructure

------------------------------------------------------------------------

# 77. Recommended Implementation Order

Do not start by building the dashboard.

Recommended sequence:

``` text
1. Define domain/state model
2. Define lifecycle state machine
3. Define event schema
4. Define Seed format
5. Implement Seed loader
6. Implement simulation engine
7. Implement human-input mechanism
8. Implement SSE/WebSocket event stream
9. Implement lifecycle UI
10. Implement Discovery visualization
11. Implement Assessment/report
12. Implement approval flow
13. Implement Implementation simulation
14. Implement Run lifecycle
15. Build analytical data model
16. Build interactive dashboard
17. Implement drill-down
18. Implement evidence views
19. Polish visual design
20. Add failure/recovery paths
```

This order prevents the UI from becoming tightly coupled to arbitrary
backend behavior.

------------------------------------------------------------------------

# 78. Questions Claude Code Should Answer Before Coding

Before substantial implementation, Claude Code should analyze and
propose answers for:

### Architecture

-   What should the repository structure be?
-   What belongs in frontend vs backend?
-   What is the domain model?
-   What is the state machine?
-   How should events be represented?

### Seed

-   What should the three Markdown files contain?
-   How should they be parsed?
-   Which information should be structured vs free-form?

### Agent Simulation

-   How should deterministic agent workflows be represented?
-   How should pauses for human input work?
-   How should simulation timing work?
-   How should failures/retries work?

### Backend

-   FastAPI structure?
-   State management?
-   SSE vs WebSocket?
-   Persistence?
-   Mock environment representation?

### Frontend

-   Vue architecture?
-   State management?
-   Visualization architecture?
-   Lifecycle rendering?
-   Human-input components?
-   Dashboard routing?

### Analytics

-   How should analytical entities be modeled?
-   How should drill-down relationships work?
-   How should cross-filtering work?
-   How should evidence be linked to findings?

### Future Evolution

-   How can simulated agents later be replaced by real agents?
-   How can real connectors later replace mocks?
-   How can methodologies be added without rewriting the engine?

------------------------------------------------------------------------

# 79. Important Implementation Constraint

Do not over-engineer the demo.

There is a temptation to immediately introduce:

``` text
Kafka
Redis
PostgreSQL
Kubernetes
Multiple microservices
Vector databases
LLM orchestration frameworks
Agent frameworks
Cloud infrastructure
```

Do not do this unless there is a concrete requirement.

The demo should prove the **concept and interaction model** first.

A simple architecture such as:

``` text
Vue
  ↓
FastAPI
  ↓
State + Simulation
  ↓
Mock Data
```

is completely acceptable.

Architectural boundaries matter more than infrastructure complexity.

------------------------------------------------------------------------

# 80. Potential Future Architecture

The eventual production system may evolve toward:

``` text
                         ┌───────────────────────┐
                         │     PROTECTION        │
                         │                       │
                         │ Policy Engine         │
                         │ Identity              │
                         │ Authorization         │
                         │ Audit                 │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    AGENT RUNTIME      │
                         │                       │
                         │ Discovery             │
                         │ Assessment            │
                         │ Analysis              │
                         │ Builder               │
                         │ Validator             │
                         │ Operator              │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │     SYSTEM STATE      │
                         │                       │
                         │ Environment           │
                         │ Evidence              │
                         │ Hypotheses            │
                         │ Solutions             │
                         │ Decisions             │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │        CORE           │
                         │                       │
                         │ Methodologies         │
                         │ Knowledge             │
                         │ Methods               │
                         │ Rules                 │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      ADAPTATION       │
                         │                       │
                         │ Connectors            │
                         │ Discovery             │
                         │ Mapping               │
                         │ Data acquisition      │
                         └───────────┬───────────┘
                                     │
                                     ▼
                              CLIENT SYSTEMS
```

V1 does not need to implement this full architecture.

------------------------------------------------------------------------

# 81. Final Product Definition

The V1 demo should be understood as:

> **A visually polished simulation of a methodology-driven autonomous
> enterprise analytical system that can be planted into a simulated
> client environment, discover available systems and data, assess
> analytical feasibility, escalate decisions to a human, build approved
> solutions, and expose the resulting analysis through interactive
> drill-down dashboards.**

The central flow is:

``` text
          PLANT
            ↓
          DISCOVER
            ↓
          UNDERSTAND
            ↓
          ASSESS
            ↓
          DECIDE
            ↓
          BUILD
            ↓
          RUN
            ↓
          EXPLORE
            ↓
          TRACE TO EVIDENCE
```

The three persistent layers are:

``` text
CORE
"How should the problem be solved?"

ADAPTATION
"How does this methodology apply to this environment?"

PROTECTION
"What is the system allowed to do?"
```

The lifecycle is:

``` text
INIT
→ DISCOVERY
→ ASSESSMENT
→ IMPLEMENTATION
→ DEPLOYMENT/RUN
→ ANALYTICS
```

And the key design philosophy is:

> **The system should appear autonomous, but never uncontrolled;
> analytical, but never a black box; and intelligent, but grounded in an
> explicit methodology and evidence.**

------------------------------------------------------------------------

# 82. Immediate Next Step

Claude Code should **not immediately begin writing the complete
application**.

First:

1.  Read and understand this document.
2.  Identify the core domain entities.
3.  Propose the System State model.
4.  Propose the lifecycle state machine.
5.  Propose the event model.
6.  Propose the repository structure.
7.  Propose the Seed format.
8.  Propose the simulation architecture.
9.  Propose the frontend/backend boundary.
10. Propose how interactive analytics and drill-down should be modeled.
11. Identify architectural risks or ambiguities.
12. Present the proposed implementation plan for review.

Only after that planning step should implementation begin.

------------------------------------------------------------------------

# 83. Resolved Requirements (V1)

> **Status:** Agreed. Sections 1--82 remain the vision document and
> describe the eventual system. This section is the binding specification
> for V1 and takes precedence wherever the two disagree.
>
> **Superseded in detail by `requirements.md` (2026-10-02).** This section
> was written before the requirements and the decision record, and is
> kept as written. Where they differ, `requirements.md` wins. The places
> that differ from the system as built:
>
> - **83.1** "A byte-identical run every time": two runs match **modulo
>   timestamps and durations** (A-2, NFR-D4).
> - **83.3** "§31's headline figures are the dataset's true counts": the
>   true counts **of the data collected so far**, which are the full
>   counts once Life is caught up (A-9, FR-AN10). The ticket dataset has
>   184,392 rows.
> - **83.6** The run has two *interruptions* as written, the credential
>   request and the timeout, but it also **waits on a person three more
>   times**: the approvals, answered card by card, and the confirmation
>   that closes seeding (FR-C1). The pipeline's states include
>   **Validated** between Testing and Complete (FR-I2). The screen calls
>   solutions **Agent Components** and feasibility **Potential** (D-11).
> - **83.7** The rule ids are illustrations. The rule set as built is
>   `PR-000` to `PR-096` in ten groups (`seeds/protection.md`). The
>   narrative's ALLOW, DENY and ESCALATE examples are, for instance,
>   PR-030 (reading a mapped dataset), PR-033 (ServiceNow's security
>   log, denied) and PR-053 (deployment, escalated).
> - **83.8** The controls are reachable by keyboard shortcut **or a
>   hidden panel** (FR-O2). The shortcuts are in `operator-guide.md` §3.
> - **83.4** "Single-command launcher": `run.py`, and `run.ps1` where uv
>   is blocked (D-21).

## 83.1 Intelligence model

**No LLM anywhere in V1.**

There is no API key, no network dependency, and no inference at any point
in the lifecycle. The system runs fully offline and produces a
byte-identical run every time.

What §40 calls the Agent Simulation Engine is a deterministic scripted
workflow runner that emits events. It is not an agent and does not
pretend to reason.

§71's LLM seams (concept mapping, hypothesis generation, finding
explanation) are recorded as future work. They are not built.

## 83.2 Seed

The repository ships three genuine seed files:

``` text
core.md
adaptation.md
protection.md
```

These contain real methodology content and are themselves a deliverable
--- they are what you show someone who asks "what is actually in the
seed?".

At INIT, the presenter supplies all three. The loader:

``` text
Validate all three present and parseable as Markdown
        ↓
Parse heading structure
        ↓
Display a real "knowledge loaded" summary from those headings
        ↓
Initialize System State
```

**Seed content does not branch system behavior in V1.** The heading
summary shown to the user is real; the methodologies, feasibility results
and policy rules are fixed. §2's seed-driven adaptation and §5's
knowledge compiler are deferred.

## 83.3 Analytics data

A committed generator module with a hardcoded RNG seed builds the ticket
dataset into memory at backend startup.

``` text
Generator (fixed seed)
        ↓
~184,000 tickets, in memory
        ↓
Planted anomaly clusters, labels and scores baked in
        ↓
Backend aggregates per filter context at request time
```

Consequences:

-   Nothing large enters version control.
-   §31's headline figures are the dataset's true counts, not decoration.
-   No statistics or ML run at request time --- anomaly labels and scores
    are produced by the generator.
-   Any cross-filter combination works, because aggregates are computed
    from records rather than read from precomputed fixtures. This
    resolves the conflict between §34 and a fixture-based approach.
-   Drill-down terminates at genuine records, so §35's trace-to-evidence
    is real rather than staged.

## 83.4 Technical stack

``` text
Frontend      Vue 3 + TypeScript + Pinia + Vite
Backend       FastAPI
Transport     SSE
Charts        Apache ECharts
Graphs        Hand-built SVG (discovery graph, build pipeline)
Theme         Light and dark, both from design tokens
State         In-memory, single run, explicit Reset
Packaging     Single-command launcher
```

Docker is **not** part of V1, superseding §29.

## 83.5 Mock environment

The ACME environment contains exactly the five systems named in §42:

``` text
ServiceNow
SAP
SQL Server
License Management System
Legacy Application Registry
```

§19's "7 Systems / 14 Data Sources / 31 Relevant Datasets" is
**discarded**. The discovery-completion summary reports the environment's
actual totals.

## 83.6 Demo narrative

The main run contains two interruptions:

1.  The scripted credential request of §68 (human input).
2.  One endpoint timeout that the runner retries and recovers from
    (technical error).

The Implementation phase shows the pipeline graph with nodes progressing
Pending → Building → Testing → Complete. The test stage expands into a
detailed result view --- named test cases, pass/fail, timings. **No
generated source code is displayed**, because none is generated.

All three solutions reach runnable dashboards:

``` text
Ticket Anomaly Detection        Deep, fully polished
License Optimization            3-4 interactive charts, one drill-down path
Application Portfolio Rat.      3-4 interactive charts, one drill-down path
```

License Optimization retains §20's partial feasibility (incomplete cost
data) as a **stated limitation on an approvable solution**, not as a
blocker. Feasibility is graded, not binary.

## 83.7 Protection layer surface

Policy decisions are first-class events in the activity stream:

``` text
Tool request: read ServiceNow incident API   →  ALLOWED   (rule R-04)
Tool request: create analytical dataset      →  ALLOWED   (rule R-11)
Tool request: deploy production service      →  ESCALATED (rule R-19)
Tool request: delete source records          →  DENIED    (rule R-02)
```

In addition, a dedicated Protection panel exposes:

-   The active rule set
-   Running counts of allowed / denied / escalated requests
-   A filterable audit log

This keeps the layer visibly cross-cutting per §9, rather than appearing
only when it interrupts.

## 83.8 Operator controls

Speed (1x / 2x / instant), skip-phase and reset exist, reachable by
keyboard shortcut only. The audience sees no transport bar.

## 83.9 Explicitly deferred

These appear in §§1--82 as aspiration and are **not** V1 work:

``` text
Seed content driving system behavior
Knowledge compilation into structured representations
Any LLM involvement
Evolution phase
Real connectors of any kind
Persistence, pause/resume, resume-after-restart
Docker packaging
Failure-injection mode beyond the single scripted timeout
Generated source-code artifacts
```

------------------------------------------------------------------------

# 84. Stakeholder Rework --- Alex Prigojine Session (2026-09-23)

> **Status:** Incorporated into `decisions.md` §7, `requirements.md` and
> `implementation-plan.md` (Phase R, M11 to M19). Every question it
> raised was answered on the same day. The Life pane is **Option B**
> (§84.3, D-17). Visual continuity with Agent One is deferred.

## 84.1 What the session asked for

Feedback received after M10 was built. It asked to reorganise the
existing interface into two views, **Seeding** (build time) and **Life**
(run time), under new names, without removing any functionality.

1.  **Renaming**, as display copy only. Solution becomes Agent Component
    (also called "Agent One VW"). Systems, and the methodology label,
    become Seed. Runtime becomes Life. Initiation becomes Planting, which
    should also show the tech stack being planted into. Feasibility
    becomes Potential: high means strong value, partial means needs
    deeper modelling, and a "routing problem" flag is possible.
2.  **Two panes** with a top toggle for both, left only or right only.
    Seeding on the left: Planting, Discovery, Assessment and
    Implementation, with the activity and protection panels. Life on the
    right: empty until the build completes, then the live system.
3.  **A growth tree** replaces the progress bar in the Seeding pane. It
    grows segment by segment, and each API or gen-AI call triggers a
    watering step.
4.  **Run / Clean up: close the seeding phase**, after Implementation.
    Merge leftover MD files, clear scratch disk space, upgrade APIs to
    their final versions, then collapse Seeding and maximise Life.
5.  **Life pane behaviour:** the model actively running, collecting
    data, dashboards, and self-improving, consistent with the earlier
    Agent One demo and reusing its visual style.

## 84.2 How it was incorporated

| Item | Ruling | Milestone | Tag |
| ---- | ------ | --------- | --- |
| 1, renames | D-11: display-only; identifiers keep their names | M11 | RENAME |
| 1, Feasibility | D-12: Potential semantics and the routing-problem flag | M12 audit, M13 copy, M16 flag | RENAME, NEW |
| 1, Planting stack | D-13: show the declared stack, marked unverified | M15 | NEW |
| 2, panes | D-14: Seeding and Life, both mounted | M14 | MOVE |
| 3, tree | D-15: replaces the lifecycle strip; protection decisions water it | M17 | NEW |
| 4, closing | D-16: a new lifecycle state, a confirmation, three gated operations | M18 | NEW |
| 5, Life | D-17: time-revealed operation, Option B of §84.3 | M19 | NEW |

**What it reworks among built milestones.** M4's single workspace
becomes the Seeding pane. M7's grade is presented as Potential and gains
the flag. M8's transition from Implementation to Run gains the closing
step. M3 and M10 are relabelled and relocated without functional change.
No requirement was deleted. Four were superseded with successors (A-3 to
A-6).

**Two items were not pure relabelling,** despite the feedback's framing.
The routing-problem flag is a new state, and the clean-up action is a
new lifecycle state. Both are scheduled as NEW milestones after the
renames and the move, not folded into them.

**Two items were adjusted to fit fixed requirements.** The tree cannot
be watered by gen-AI calls, because none exist (NFR-D1). It is watered
by the tool requests the protection engine evaluates, which are this
system's API calls. The clean-up's three operations are simulated; none
touches a disk, a file or the network, and the seed files are never
merged into anything.

**Follow-up questions, all answered on 2026-09-23:**

- **Agent One VW (OQ-8)** is what comes out of a seed. It is the
  framework through which the methodology of building and maintaining
  the pipeline is implemented. See §84.4.
- **Methodology naming (OQ-9):** rename only if a seed-themed name is
  coherent. None was, so methodologies keep their name. Systems becomes
  Seed, as Alex proposed.
- **Routing problem (OQ-10):** evidence that exists but cannot reach the
  analysis. The wording for MEDIUM and LOW is accepted.
- **Progress bar (OQ-11):** the lifecycle strip.
- **Life (OQ-12):** Option B.
- **Agent One demo (OQ-13):** skipped for now. It is a separate demo
  that displays the detailed agentic steps of an analysis.

**Milestones renumbered.** The rework inserts M11 to M19 after M10. The
three milestones not yet built move from M11, M12 and M13 to M20, M21
and M22.

## 84.3 Life pane: the options considered (OQ-12)

> **Chosen, 2026-09-23: Option B**, without Option C's additions.
> Specified as D-17 and FR-LF4 to FR-LF11. Built at M19. The options are
> kept here as the record of what was weighed.

The feedback's least-specified item. Every option respects what V1
already fixes: no LLM (NFR-D1), determinism modulo timing (A-2), no
statistics at request time (FR-AN3), descriptor-driven dashboards (D-1)
and the motion budget (NFR-V4). The Evolution phase is excluded (§83.9,
`requirements.md` §4.1), so "self-improving" has to mean something
narrower than Evolution or be left out.

### Option A --- Life hosts what was built

**The viewer sees:** the Life pane opens on the list of Agent
Components. Run opens each one's dashboard inside the pane, and a short
Life activity stream records runs and evidence opened.

**Collection:** none shown. Dashboards present the generated dataset
whole. **Self-improvement:** none.

**Requirement cost:** none beyond FR-LF1 and FR-LF2. §4.1 is untouched.
**Build:** almost nothing past M14. M19 becomes an empty-state and copy
pass.

**Trade-off:** no risk and no new claims. But it delivers neither
"actively running" nor "self-improving". Life is the old Runtime stage
under a new name, which the stakeholder may reasonably read as the
feedback not having been acted on.

### Option B --- Time-revealed operation *(recommended)*

**The viewer sees:** each Agent Component collecting. A deterministic
clock advances through the last stretch of the generated data in steps,
for example one simulated week every few seconds. Each step is a
collection event: *"Collected 3,412 tickets from ServiceNow, week 34."*
KPIs and charts update as the cursor advances. At intervals a
recalibration event recomputes the baseline over the revealed window and
re-scores the findings: *"Resolution-stall baseline recalibrated on 12
more weeks: 41.2 h to 39.8 h. Three clusters newly confirmed, one
withdrawn."*

**How it stays honest.** The records already exist in the generator.
Collection reveals them, and the stream labels this as simulated
collection. The cursor is one more term in the filter context (FR-EV1),
so every dashboard follows it with no per-dashboard code (D-1). The
generator precomputes the baselines and scores for every step, which
keeps FR-AN3 intact. Every figure still comes from real rows, and fixed
steps keep A-2.

**Requirement cost:** an amendment to §4.1 stating that recalibrating
baselines within a run is not Evolution, where Evolution means new
methodologies, components or code. FR-AN4's "true counts" becomes "true
counts of the revealed data". New requirements for the cursor, collection
events and recalibration. Operator speed applies to the clock (FR-O3).

**Build:** medium. The generator produces per-step baselines and scores;
the arithmetic already exists for one step. The query engine gains the
cursor term. The Life stream and clock are new. The evidence panel names
the calibration a finding was made under.

**Trade-offs:** the most "alive" option that stays truthful, and it
reuses existing machinery. Two UX risks come with it. Findings could
shift under a viewer mid-drill; this is mitigated by freezing the cursor
while the viewer interacts with a dashboard and resuming it on return.
And a finding that changes between steps looks unstable unless the
evidence panel says which calibration step produced it.

### Option C --- Agent operations console

**The viewer sees:** Life as a console with one card per running Agent
Component. Each card shows its state (collecting, analysing or idle),
cycle count, records ingested, findings emitted and model version. A
version timeline per component, v1.0 to v1.1 to v1.2, carries a measured
quality figure: **precision and recall against the planted ground
truth.** The generator knows which records it planted as anomalous, so
these figures are arithmetic, not claims. Dashboards open from the
cards.

**Requirement cost:** needs Option B's mechanics underneath. Without
them, the cards animate over nothing, which NFR-V5 and the §70 non-goal
of "a collection of fake AI agents" both forbid. It needs the same §4.1
amendment as B and pushes further: model versions within a run sit
closer to Evolution. It also adds new interface surface to take through
M21.

**Build:** the largest. Option B, plus the console and the timeline.

**Trade-offs:** the most agent-flavoured, and possibly the closest to
the Agent One demo, if that demo was agent-centred (unknown; OQ-13). It
carries the highest risk of reading as fake agents, and the most new
interface to get through the design pass.

### Comparison

|                         | A --- Host what was built | B --- Time-revealed | C --- Operations console |
| ----------------------- | ------------------------- | ------------------- | ------------------------ |
| Actively running        | No                        | Yes                 | Yes                      |
| Collecting data         | No                        | Yes, revealed       | Yes, revealed            |
| Self-improving          | No                        | Recalibration       | Versions with measured precision |
| Every figure real       | Yes                       | Yes                 | Yes, only with B beneath |
| Amends §4.1             | No                        | Narrowly            | Further                  |
| Build size              | Small                     | Medium              | Large                    |
| Main risk               | Feedback reads as ignored | Findings shift mid-drill | Reads as fake agents |

### Recommendation

**Option B.** It is the smallest option that delivers both halves of
the request, running and improving, while every number stays traceable
to a row. Two parts of Option C are cheap and worth borrowing:

- **Precision and recall against planted ground truth** as the measure
  of each recalibration. It makes "self-improving" checkable rather than
  asserted.
- **A thin per-component status strip** at the top of the Life pane, in
  place of the full console, if the stakeholder wants the agent framing.

### On reusing the Agent One demo's style

**Deferred** at the stakeholder's direction (OQ-13). Agent One is a
separate demo that shows the detailed agentic steps of an analysis. None
of the three options depended on visual style, which lands in M21.

If continuity is revived, its **visual style** can be borrowed freely.
Its **step-by-step agentic narration** conflicts with FR-E9, which
forbids showing simulated internal reasoning, and with NFR-D1, unless
those are amended first (`decisions.md` §7.3).

## 84.4 Naming, as confirmed

The seed analogy names the **lifecycle**. The analysis keeps its own
names.

```
Seed                        the product; what is planted
 ├── Core · Adaptation · Protection      its three layers
 │    └── methodologies                   carried in Core; name unchanged
 │
Planting → Seeding          build time: Discovery, Assessment, Implementation
 │                          the growth tree shows it happening
 ▼
Agent One VW (ValueWise™)   what grows out of the Seed: the framework that
 │                          implements building and maintaining the pipeline
 └── Agent Components       its parts, one per approved methodology
 │
Life                        run time: Agent One VW collecting, recalibrating,
                            and answering questions through its dashboards
```

Seeding shows Agent One VW being **built**. Life shows it being
**maintained**. Together they make up the whole of what the name claims.

## 84.5 Phase R build log

One entry per Phase R milestone, in build order. Each records what
changed, the files touched, and what needs checking by hand. The commit
hash for each milestone is in the Status table of
`implementation-plan.md` §3.

### M11 · Display vocabulary

**What changed.** The screen now uses D-11's display vocabulary, apart
from Feasibility, which M12 and M13 handle.

- The product name is **Seed**: the page title, the seed screen's
  heading and the workspace identity.
- The phase labels are **Planting** and **Life**. The INIT stage's
  heading "Seed" is now "Planting".
- Display copy says **Agent Component** instead of "solution": the
  approval note on the human-input surface, the review drawer's approve
  button, the ready list's summary, and the stream messages from the
  assessment and implementation workflows. That includes the approval
  request's prompt ("3 of 3 Agent Components await a decision").
- The Implementation stage is headed **Building Agent One VW**, and its
  note calls each lane an Agent Component that is part of Agent One VW
  (FR-N6, in part).

One gap in the plan was closed. The activity stream's phase dividers
printed the raw phase value, so `INIT` and `RUNTIME` still reached the
screen. The labels now live in one table, `PHASE_LABELS` in
`design/presentation.ts`. The lifecycle strip and the stream dividers
both read it. M17's growth tree can read the same table.

**Deliberately unchanged.** Nothing in M11's load-bearing table was
touched: types, payload keys, `/api/solutions`, the `solution.*` event
types, the `'solution-approval'` request id, the `INIT` and `RUNTIME`
values, and the component file names. Also left alone:

- The `## Systems` heading in `seeds/adaptation.md`. It lists the
  client's systems, the same case as FR-N4, so no seed file changed.
- API error strings that mention a solution. The frontend never shows
  API error detail.
- The FastAPI title `Systems V1` (`backend/app/main.py`). It appears only
  on the `/docs` page.
- The raw lifecycle state in the header, such as `INITIALIZED`. It is a
  state value, not the phase label.
- "Workspace" in the ready-list note and on the dashboard's back button.
  M14 revisits both.
- The word "feasible" in the deployment request's purpose. M13 changes
  it.

**Files.** `frontend/index.html`; `views/SeedView.vue`,
`views/WorkspaceView.vue`; `components/LifecycleStrip.vue`,
`ActivityStream.vue`, `StagePane.vue`, `HumanRequest.vue`,
`ReviewDrawer.vue`, `ImplementationStage.vue`, `RuntimeStage.vue`;
`design/presentation.ts`; `backend/app/simulation/workflows/assessment.py`
and `implementation.py`.

**Gates.** `pytest` gives 417 passed with no test edited. Typecheck and
build pass. Live: the bundled seed was planted and the narrative run to
the end. All three approvals were made through the interface, one from
the review drawer and two from the cards, which exercises the
`'solution-approval'` id across the boundary (R-13). Run then opened the
Ticket Anomaly dashboard. The text on screen at the Life stage has no
"Solution", "Runtime", "Init" or product-name "Systems". Two words
remain, both expected: "feasibility", which M13 changes, and "systems"
as the count of client systems (FR-N4).

**Check by hand.**

1. Read the renamed copy in context, especially the Implementation
   stage's new note and the stream messages "Three Agent Components
   proposed…" and "Every Agent Component decided…".
2. Approve one component from the drawer and one from its card, and
   confirm both register.
3. Look at the lifecycle strip and the stream dividers in the light
   theme as well as the dark one.

**Carried forward to M14.** The live run confirmed that the lifecycle
passes from `IMPLEMENTATION_COMPLETE` to `READY_TO_RUN` in the same
beat. Until M18 adds closing, FR-W3's Both default at
`IMPLEMENTATION_COMPLETE` would only flash before Life only takes over.

### M12 · Feasibility references, classified

**What changed.** No code. The preliminary inventory in M12's block of
`implementation-plan.md` was re-verified against the code after M11 and
replaced. `feasib` occurs on 65 lines across `backend/app`,
`backend/tests`, `frontend/src` and `seeds/`. Each line is classified
once, as contract, logic, tested, silent failure, display or comment.
The grade references that do not contain the word are classified too.

The audit found five differences from the preliminary inventory:

- A new **tested** class. `test_assessment.py:201` asserts the regrade
  format "License Optimization PARTIAL to HIGH", so that format is kept.
- Two more contract items: `Approval.feasibility` in the store, and the
  `recommendation` key, whose non-empty value a test asserts.
- One more display string: the deployment request's purpose.
- `ReviewDrawer.vue` has no MEDIUM selector. MEDIUM inherits
  `--text-primary`, the same colour the card sets, so the two agree.
  The grade-colour follow-up below later gave MEDIUM its own colour on
  every surface.
- The `Grade` type sits one line earlier than the plan said.

**Agreed for M13.** The display wording table, the four recommendation
drafts, and two findings:

- The seed's `## Feasibility` table becomes a Potential column showing
  the computed grades, HIGH, PARTIAL and MEDIUM, with limiting factors
  matching what assessment reports. Today it says "Yes, Yes, Partially",
  and its limiting factors are not the ones the computation finds.
- The deployment purpose drops "found feasible" and reads "…the Agent
  Components the assessment proposed."

**Files.** `docs/implementation-plan.md` (M12's inventory, and the
Status table, which also gains M11's hash) and this log.

**Gate.** Your review of the audit, given 2026-09-23. No code changed,
so the test suite and the build were not rerun.

**Check by hand.** Nothing further. M13 carries the colour check for
all four grades in both themes.

### M13 · Feasibility displayed as Potential

**What changed.** Exactly the display list M12 agreed, and nothing M12
classified as load-bearing.

- Labels. "Feasibility" becomes "Potential" on the card, in the drawer,
  in the ready list and in the assessment and discovery notes. The
  drawer's section "Why this is feasible" becomes "Why the value is
  within reach". The discovery verdict "Appears feasible" becomes
  "Evidence located".
- Stream messages. "{name}: potential {grade}", "approved …, on
  potential {grade}", "Potential moved:" and "No potential grade
  changed." The regrade format "{name} {from} to {to}" is kept, because
  `test_assessment.py:201` asserts it.
- The deployment request's purpose reads "…the Agent Components the
  assessment proposed."
- The four `RECOMMENDATIONS` values are rewritten to D-12's meanings. The
  keys are unchanged.
- `seeds/adaptation.md`: `## Feasibility` becomes `## Potential`, and
  the table now shows the computed grades, HIGH, PARTIAL and MEDIUM, with
  the limiting factors assessment reports. It previously said "Yes, Yes,
  Partially". The heading count FR-S5 displays is unchanged.
- One comment, `ReviewDrawer.vue:21`, which names the section title.

**Kept.** The `feasibility`, `appearsFeasible` and `recommendation`
keys, the `Grade` values, `grade_of`, the `[data-grade]` and
`data-feasible` selectors, the module name, and every other comment.

**Files.** `backend/app/knowledge/feasibility.py`,
`knowledge/solutions.py`, `simulation/workflows/assessment.py`;
`frontend/src/components/SolutionCard.vue`, `ReviewDrawer.vue`,
`RuntimeStage.vue`, `AssessmentStage.vue`, `EnvironmentStage.vue`;
`seeds/adaptation.md`.

**Gates.** `pytest` gives 417 passed with no test edited. Typecheck and
build pass. Live checks:

- Discovery's summary shows "Evidence located" for all three
  methodologies.
- The full event log of the run has 115 events and none mentions
  "feasib". The screen showed none at the discovery summary, at
  assessment with the drawer open, in the protection panel, or at the
  Life stage.
- For the silent-failure check (R-13), Application Portfolio
  Rationalization was driven to LOW by revising four fields to 40%, then
  restored to MEDIUM. All four grades were read with their computed
  colours on the card and in the drawer, in both themes. The two surfaces
  agree:
  - dark: HIGH `rgb(63,178,122)`, MEDIUM `rgb(232,235,240)`, PARTIAL
    `rgb(215,154,58)`, LOW `rgb(111,120,133)`;
  - light: HIGH `rgb(27,127,75)`, MEDIUM `rgb(18,21,27)`, PARTIAL
    `rgb(169,106,0)`, LOW `rgb(90,97,114)`.
  - These MEDIUM values are the plain text colour. The grade-colour
    follow-up below replaces them with olive: `rgb(138,171,76)` in dark
    and `rgb(95,127,26)` in light.
- All three approvals were made through the interface. The drawer then
  reads "Approved on potential HIGH, under PR-053."

**Check by hand.**

1. Read the four recommendation texts in the drawer as content, as the
   plan asks. Note that the drawer's section title, "Why the value is
   within reach", also heads a LOW assessment, where the value is not
   within reach. M21 may want a grade-aware title.
2. Read the rewritten `## Potential` section of `seeds/adaptation.md`.
3. The discovery verdict for missing evidence ("Evidence missing",
   `data-feasible='false'`) is unchanged, but the scripted run never
   shows it. The selector was not edited.

### M14 · Seeding and Life panes

**What changed.** The workspace is now two panes under one top bar
(D-14). Both panes stay mounted for the whole run, and a layout change
only hides one (NFR-A7).

- **Top bar** (`App.vue`): the identity, the layout control (Both,
  Seeding, Life) and the raw lifecycle state. It replaces the full-screen
  dashboard overlay. `SeedView` still takes the whole screen until the
  seed is planted (FR-W7).
- **Seeding pane** (`WorkspaceView.vue`): unchanged in content. It keeps
  the lifecycle strip in its own bar, then the stage, the Activity and
  Protection rail, and the human-input surface. `StagePane` no longer
  shows the ready list. At `RUNTIME` it keeps the finished build on
  screen, as the record of what was built.
- **Life pane** (`views/LifeView.vue`, new): headed "Agent One VW
  (ValueWise™)". It shows an empty state until the build is done (FR-W4).
  From `RUNTIME` it shows the ready list (`RuntimeStage`, moved). Run
  opens the dashboard inside the pane, over the list, which stays
  mounted. The dashboard is still loaded lazily.
- **Layout rules** (`stores/layout.ts`, new):
  - The lifecycle sets the default: Seeding until
    `IMPLEMENTATION_COMPLETE`, Both at `IMPLEMENTATION_COMPLETE`, then
    Life at `READY_TO_RUN` and `RUNNING`.
  - A manual choice holds until the default next changes. I read "the
    next lifecycle-driven change" in FR-W3 that way, so a transition
    that keeps the same default does not override the choice.
  - A pending request turns Life only into Both, and disables Life only
    until it is answered (FR-W5).
  - A rehearsal link sets Life only (FR-W6). Closing the rehearsal hands
    the layout back to the lifecycle default. Before planting, the
    rehearsal is shown in the pane shell with the control disabled.
- **Copy.** The dashboard's back button reads "← Agent Components". The
  ready list's note says to return to this list, not the workspace
  (FR-L10).
- **One layout fix.** The dashboard was built for the full screen. In
  the Both layout it overflowed the pane's right edge, so its grid is now
  held to the pane's width.

**Files.** `frontend/src/App.vue`; `views/LifeView.vue` (new),
`views/WorkspaceView.vue`, `views/DashboardView.vue`;
`components/LayoutControl.vue` (new), `components/StagePane.vue`,
`components/RuntimeStage.vue`; `stores/layout.ts` (new). No backend
change.

**Gates.** `pytest` gives 417 passed with no test edited. Typecheck and
build pass. Live: one headless-Chrome session drove the full narrative
through the interface with 31 checks. 29 passed. The 2 failures are
described under "Found, pre-existing" below.

- The layout rules: all three layouts reachable; Life's empty state; a
  credential request forcing Seeding visible from Life only; Life only
  after the build; a rehearsal link opening Life only, both before and
  after planting; and a reload at `READY_TO_RUN` opening Life only.
- Neither pane was unmounted across the run, checked by element
  identity.
- The stream kept its scroll position across a hide and show (700 to
  700).
- A drilled dashboard kept its element, its URL filter and its figures
  across Seeding only and back.
- Re-verified from M3 to M10 (FR-W8):
  - M3: the seed screen summarises each dropped layer.
  - M5: DENY PR-033 and ESCALATE PR-053 appear in both the stream and
    the panel.
  - M6: one credential pause, answered through the form; the timeout
    recovered; and counts derived from the graph.
  - M7: a completeness edit moves a grade on the card, and reverting it
    moves it back.
  - M8: approval through the interface, the build, and Run.
  - M10: headline, then cluster, then ticket, with consistent figures,
    and the browser's Back popped exactly one step.
  - M9's backend is untouched, and its suite passes.

**Found, pre-existing.** Both were confirmed by running the same steps
against the M13 code with the M14 changes stashed. Neither was fixed,
because neither is in M14's rework list.

1. **After a live plant, the Planting stage shows no layer summary.**
   `StagePane` reads the layers from the snapshot, and planting from the
   interface never refreshes the snapshot. The summary appears only
   after a reload. Fixed before M15; see the follow-up below.
2. **Back, then closing a running dashboard, leaves it open as a
   rehearsal.** The dashboard store's `popstate` handler sets
   `rehearsal` from the URL, so after the browser's Back the closed run
   falls through to a rehearsal of the same dashboard. A second click on
   back closes it. Fixed before M15; see the follow-up below.

**Check by hand.**

1. The Both layout is cramped at 1600 px. The Seeding stage's column is
   about 320 px wide beside the rail, and the build lanes shrink. M21
   owns this, but judge whether it is acceptable until then.
2. The top bar still shows the raw lifecycle state, such as
   `READY_TO_RUN`, as before.
3. Before M18, Both at `IMPLEMENTATION_COMPLETE` lasts one beat, so in
   practice the layout goes from Seeding straight to Life.

### Follow-up · Potential grade colours (requested after M14)

**What changed.** MEDIUM used to render in plain text colour, so the
four grades did not read as one scale. Potential now has its own tokens
in `design/tokens.css`, forming an ordered scale: `--grade-high` (green),
`--grade-medium` (olive, new), `--grade-partial` (amber) and `--grade-low`
(grey). HIGH, PARTIAL and LOW alias the existing status tokens, so their
colours are unchanged. PARTIAL stays the caution colour and never the
fault colour (FR-H4).

- The card, the drawer and the Life ready list all read the grade
  tokens. The drawer gains the MEDIUM rule it never had. The ready list
  now colours its grade, where before it was plain text.
- The `[data-grade]` selectors are unchanged (M12's silent-failure
  class). Only the colours they apply changed, at your request.

**Contrast.** Measured against the card surface:

| Theme | HIGH | MEDIUM | PARTIAL | LOW |
| ----- | ---- | ------ | ------- | --- |
| Light | 5.0:1 | 4.6:1 (`#5f7f1a`) | 4.4:1 | 6.2:1 |
| Dark | 6.5:1 | 6.6:1 (`#8aab4c`) | 7.1:1 | 3.9:1 |

The dark MEDIUM was first tried as a brighter lime (9:1). It was toned
down so MEDIUM does not outshine HIGH.

**Files.** `frontend/src/design/tokens.css`,
`components/SolutionCard.vue`, `components/ReviewDrawer.vue`,
`components/RuntimeStage.vue`.

**Gates.** Typecheck and build pass. No backend change. Live: all three
surfaces show the four grade colours, read as computed styles, in both
themes.

**Check by hand.** In light theme, confirm that HIGH (dark green) and
MEDIUM (olive) are distinct enough at a glance. M21 tunes the palette.

### Follow-up · the two pre-existing bugs M14 found

Fixed before M15, at your direction.

**1. The Planting stage showed no layer summary after a live plant.**
`StagePane` read the layers from the snapshot, and planting from the
interface never refreshed the snapshot. The fix follows the store's own
rule, that state is folded from events (FR-E5):

- `seed.loaded` already carried each layer's title, heading count and
  section count. It now also carries `topics`, an additive payload key.
- The system store gains a `seed` field. It is adopted from a snapshot
  and folded from `seed.loaded`, and `StagePane` reads it. Every
  connected client now shows the plant without a reload, not only the
  one that planted.
- New test: `test_the_plant_event_carries_the_summary_the_planting_stage_shows`
  in `test_seed.py` holds the event's per-layer figures equal to the
  snapshot's. No existing assertion was edited.

**2. Closing a running dashboard after the browser's Back left it open
as a rehearsal.** The dashboard store's `popstate` handler set
`rehearsal` from the URL. A running dashboard's URL names it too, so a
Back during a run marked it as a rehearsal, and closing the run then
fell through to that rehearsal. The handler now changes `rehearsal` only
when one is already open or when no dashboard is open. Back and Forward
still open and close a real rehearsal.

**Files.** `backend/app/api/seed.py`, `backend/tests/test_seed.py`;
`frontend/src/stores/system.ts`, `stores/dashboard.ts`,
`components/StagePane.vue`.

**Gates.**

- `pytest` gives 418 passed. The first run after the change reported one
  failure and printed only the count. Four reruns passed, so it did not
  reproduce. The suite has timing-sensitive tests in
  `test_analytics.py`, `test_discovery.py`, `test_engine.py` and
  `test_presentation.py`. Watch for a recurrence.
- Typecheck and build pass.
- Live: the M14 driver now passes 31 of 31, including both checks that
  failed before.
- Rehearsal history still works. A rehearsal opened from the operator
  panel drilled one step; Back popped the step; a second Back closed the
  rehearsal; and Forward reopened it.

**Check by hand.** Plant from the seed screen and confirm the Planting
stage lists the three layers at once. Run a component, drill in, press
the browser's Back, then press "← Agent Components". The list should
appear at the first click.

### M15 · Declared stack at Planting

**What changed.** The Planting stage now shows the systems the
Adaptation layer declares, each marked declared and not yet verified
(D-13, FR-N5).

- `environment/acme.py` gains `declared_inventory()`: the five systems of
  `SYSTEM_ORDER`, with their labels. Discovery's first beat already
  reveals `SYSTEM_ORDER`, so the two read one source.
- System State gains `declared`, an additive snapshot field. The plant
  sets it at `INITIALIZED` and Reset clears it. The environment graph
  stays empty until Discovery runs, so the declaration gives nothing of
  Discovery's work away (G-2).
- `seed.loaded` carries `declared` as an additive payload key, so a
  watching client shows the stack without a reload. It is not a new
  event, because `test_seed.py` pins the plant to exactly two events.
- The frontend store adopts `declared` from the snapshot and folds it
  from `seed.loaded`. The Planting stage lists each system with
  "Declared" and a standing. The standing is "Not yet verified" until the
  system's node leaves `unknown` in the graph, and from then on it is the
  graph's status. Unverified is shown muted, never in the warning colour,
  because it is a state of knowledge, not a fault.

**Files.** `backend/app/environment/acme.py`, `domain/state.py`,
`api/seed.py`; `backend/tests/test_declared.py` (new);
`frontend/src/stores/system.ts`, `components/StagePane.vue`.

**Gates.**

- `pytest` gives 423 tests, 422 passing: 418 existing plus 5 new, with no
  existing test edited. The one failure is the performance test below.
- Typecheck and build pass.
- Live:
  - After a plant from the interface, the five systems appear at once,
    each "Declared, Not yet verified", and the graph is still empty.
  - A reload shows the same list from the snapshot.
  - `seed.loaded` and Discovery's first beat (`discovery.inventory.loaded`)
    name the same five systems in the same order.
  - The M14 walkthrough still passes 31 of 31.

**Flagged: a performance test at its limit.**
`test_any_filter_answers_every_view_inside_200_ms[ticket-anomaly-detection]`
fails in the full suite with a worst case of 204 to 234 ms against its
200 ms budget. It passes on its own and passed twice with the new test
file excluded. It also failed once before M15 (see the previous entry).
M15 touches no analytics code, and suite runtimes rose from about 23 s
to 33 s over the session, so this reads as machine load near a tight
threshold. Changing the test is an assertion edit before M18, so it is
left for a ruling. The options are to measure the median rather than
the worst case, to warm up more, or to take the timing on its own rather
than in the suite.

**Check by hand.** Plant, and read the Declared stack section's copy.
Confirm that "Not yet verified" in muted italic reads as intended beside
the "Declared" label.

**Ruling on the performance test, 2026-09-24.** Leave the test as it
is. Background processes on the machine vary the load, so a marginal
timing failure is expected noise, not a defect.

### M16 · Routing-problem flag

**What changed.** Each assessment now carries a routing-problem flag
beside its grade (D-12, FR-A12, FR-A13).

- `knowledge/routing.py` (new) computes it. A required concept is
  flagged when a dataset that carries it has been found in the graph
  but cannot reach the analysis, for one of three reasons:
  - the dataset was refused by policy (`excludedBy`, with its rule);
  - it, or the surface or system above it, is in error;
  - it, or the surface or system above it, is waiting on input.

  Which concepts a dataset carries comes from the Adaptation concept
  mapping in the environment definition. The state of each node comes
  from System State. A dataset nobody has found yet is not counted,
  because it is not yet known to exist (G-2).
- `assess` adds `routing`, a list of the blocked dataset and concept
  pairs, as an additive field on every assessment. An empty list means
  no routing problem. The grade and its computation are untouched, and
  a test holds that the flag never moves the grade.
- The card shows "Routing problem: N sources out of reach". The drawer
  shows a banner under the headline and a "Routing problem" section.
  Each entry there names the concept, the dataset and the reason:
  "Refused under PR-…", "Unreachable at …" or "Awaiting input at …".
  The treatment is a dashed outline in secondary text, never the fault
  or the caution colour, which keeps FR-H4's distinctions.

**Recorded for D-12: the scripted run raises no routing problem.**
PR-033, the candidate D-12 named, refuses ServiceNow's
`sys_security_log`. That dataset is outside the concept mapping, so it
carries nothing any methodology requires, and its refusal does not flag
anything. By the end of Discovery no node is in error or awaiting
input. So the flag is computed and tested, but it never appears in the
narrative. D-12 calls this a narrative choice for the stakeholder, not
something to fake. It is raised for a ruling.

**Files.** `backend/app/knowledge/routing.py` (new),
`knowledge/feasibility.py`; `backend/tests/test_routing.py` (new);
`frontend/src/stores/system.ts`, `design/presentation.ts`,
`components/SolutionCard.vue`, `components/ReviewDrawer.vue`.

**Gates.**

- `pytest` gives 431 passed: 8 new tests and no existing test edited.
  The new tests are in M7's style, where changing the fact moves the
  flag:
  - a carrier in error;
  - a surface awaiting input, which blocks every dataset behind it;
  - a policy refusal, citing its rule;
  - restoring the fact clears the flag;
  - an unfound dataset is not counted;
  - the grade never moves;
  - a regrade carries the flag into System State.
- Typecheck and build pass.
- Live: the scripted run's assessments all carry an empty `routing`. The
  scripted run raises nothing to see, so the frontend treatment was
  checked by injecting two routing problems into the browser's store.
  Ticket Anomaly Detection then showed HIGH in green beside a dashed,
  neutral "Routing problem: 2 sources out of reach". The drawer listed
  "Unreachable at Incident API" and "Refused under PR-032", in both
  themes.
- The M14 walkthrough still passes 31 of 31.

**Check by hand.** Judge the treatment in the screenshots or by
injection. It is a dashed outline with a ⤳ mark, and it is deliberately
neither a grade colour nor the fault colour. M21 designs it properly
(R-14 is about the tree, but the same restraint applies).

### Follow-up · the routing problem made visible (D-12 ruling, option 2)

**Ruling, 2026-09-24.** Make PR-033's refusal a real routing problem
rather than leaving the flag invisible in the narrative.

**What changed.**

- `environment/acme.py`: ServiceNow's `sys_security_log` now declares
  what its fields hold: `application` and `sys_created_on`, both
  carrying `application-usage`. That is Application Portfolio
  Rationalization's usage signal.
  - I chose APR rather than License Optimization's `product-usage`
    because OQ-6's refused request reads "sign-in counts per
    application, application identifier and timestamp". That is an
    application usage signal, not licence consumption.
  - The table stays unmapped and a security table, so the request
    facts, PR-033's DENY and the PR-031 overrule are all unchanged.
- `seeds/adaptation.md`: one paragraph after the application concepts
  table says the security log carries a usage signal that PR-033
  refuses. No heading was added, so FR-S5's counts are unchanged.
- `knowledge/routing.py`: the docstring now says concepts are read from
  the dataset's field profile, which is wider than what is mapped for
  reading.

**What does not move.** The security log is never profiled, because
Discovery profiles mapped datasets only. So no grade, sufficiency or
Discovery count changes. The narrative still reads "Discovery complete:
5 systems, 6 data sources, 17 datasets (16 profiled, 1 excluded by
policy). Evidence located for 3 of 3 methodologies". The grades are
still HIGH, PARTIAL and MEDIUM.

**What does.** Application Portfolio Rationalization now carries one
routing problem: `application-usage` from `sys_security_log`, refused
under PR-033. Its card reads "Routing problem: 1 source out of reach",
and its drawer lists "Usage signals per application, with distinct
actors · sys_security_log · Refused under PR-033". It is MEDIUM
potential with a blocked path to part of its evidence, which is exactly
D-12's point.

**Tests.** Three assertions in `test_routing.py`, all written in M16,
assumed that the scripted run had no routing problem. That fact changed
with this ruling:

- `test_the_scripted_run_raises_no_routing_problem` is replaced by
  `test_the_scripted_run_flags_the_refused_usage_signal`. It asserts
  APR's single PR-033 entry, none for the other two, and unchanged
  grades.
- Two other tests now compare against that baseline, or filter to the
  dataset they change.

No test from before Phase R changed. `pytest`: 431 passed.

**Live.** Confirmed on a fresh server: the API, the card and the drawer
all show APR's PR-033 routing problem, and Discovery's messages are
unchanged. The first live attempt read an old server that an earlier
stop had missed. It is recorded in the working notes and was not a code
fault.

**Check by hand.** Open Application Portfolio Rationalization's review
and read the Routing problem section. Then decide whether the seed
paragraph's wording suits the Adaptation document.

### M17 · Growth tree

**Measured first, as the plan asks.** A full narrative records 106
events, 27 of them policy decisions: 25 ALLOW, 1 DENY and 1 ESCALATE.
Nothing is near "hundreds", so every decision is its own watering step
and none are batched.

**What changed.** A hand-built SVG growth tree replaces the lifecycle
strip in the Seeding pane (D-15, FR-G1 to G6). `LifecycleStrip.vue` is
removed, because FR-L6 is superseded by A-4.

- **A pure function of the event log.** `design/growth.ts` computes
  `growthOf(events)`, which reads nothing but the log. It gives:
  - roots from `seed.loaded`, one per layer;
  - a sprout at `system.ready`;
  - a stem leaf per system reached (`discovery.system.connected` or
    `.registered`) and per methodology assessed;
  - a branch per Agent Component built (`implementation.build.started`),
    with a leaf per `implementation.component.built` and a bud at
    `solution.ready`;
  - a bloom at `deployment.ready`, for Agent One VW;
  - a watering step per `policy.decision`.

  The current phase and the waiting-on-a-person state come from the log
  too. The frontend replays the whole log on connect, so a reloaded tree
  is the tree that grew live (FR-G5).
- **The layout keeps the strip's footprint.** The tree grows along a
  horizontal line: the seed and roots in a soil bed at the left, then
  one stem through five labelled phase sections, ending in the bloom.
  Each phase label reads complete, current or future, with the same
  marker meanings the strip had, including amber while waiting on a
  person (FR-G1). The ungrown stem is a dotted guide, so the future stays
  visible.
- **Watering (FR-G3, FR-G4).** An allowed request is a dot of water
  absorbed into the soil. A refused request is a hollow drop held above
  a barrier line, with its rule in the tooltip: it watered nothing. An
  escalated request is a ringed dot. I read FR-G3 literally here: it was
  evaluated and not denied, so it waters, but it reached a person rather
  than soaking straight in. A tally reads "Watered by 26 tool requests ·
  1 refused". The tree's accessible title says that no model calls
  occur.
- **Motion (NFR-V7).** Only an event that arrives alone, 250 ms or more
  after the previous one, animates: a 420 ms sprout, a falling drop, a
  stem transition. A replay, a resync or a run at instant speed arrives
  in a burst and simply appears in its final state. Reduced motion turns
  every animation off. Motion decides only how an element arrives, never
  what is drawn.
- **Colours.** New `--growth-*` tokens in both themes, deliberately
  muted (NFR-V6, R-14). M21 reviews them.

**Files.** `frontend/src/design/growth.ts` (new),
`components/GrowthTree.vue` (new), `components/LifecycleStrip.vue`
(removed), `views/WorkspaceView.vue`, `design/tokens.css`. No backend
change.

**Gates.** `pytest` gives 431 passed, and no test was edited. Typecheck
and build pass. Live, with the tree serialized without its
motion-only attributes:

- After a full run the tree holds 3 roots, 8 stem leaves, 3 branches with
  18 leaves, 3 buds and the bloom. Its watering is 26 absorbed and 1
  refused.
- **Replay equals live.** A reload rebuilt the identical tree
  (10,969 characters).
- **Two runs from Reset** ended with the identical tree. Reset returns to
  just the planted seed.
- **No strobing.** A whole run at instant speed produced 0 animated
  arrivals, while 25 s at 2x produced 2.
- **Reduced motion** gives the identical final tree to a full-motion
  session.
- No text in the tree claims a model or an AI call.
- The M14 walkthrough still passes 31 of 31.

**For M22.** FR-G5's determinism is proven live here. The plan's
automated determinism test is backend Python and cannot run
`growthOf`. Since the tree is a pure function of the log, event-log
determinism implies tree determinism. M22 can rely on that argument or
port `growthOf`.

**Check by hand.**

1. Watch a run at 1x and judge the motion budget: the sprouts, the
   falling drops and the stem growth (R-14).
2. Judge the horizontal form. A vertical tree would need a column taken
   from the stage.
3. Confirm the escalation reading: the deploy request waters, as a ringed
   dot.

### Follow-up · the growth tree moves to Life (D-18)

**Ruling, 2026-09-24, after M17's review.**

- The tree is vertical and depicts the process: the seed planted, then a
  sapling, a small plant, and a tree with branches and leaves.
- It grows smoothly and follows the real progression.
- It stands in the Life pane while seeding runs. When the build
  completes it hides, and the pane shows that the process has completed,
  with Agent One VW (ValueWise™).
- Four questions were answered first:
  - the layout is Life only during the build;
  - the lifecycle strip returns to the Seeding pane;
  - the hand-over happens when the build completes;
  - each phase is one growth stage.

These are recorded as D-18, with A-10 to A-12, in `decisions.md` and
`requirements.md`, and noted in the plan's M17 and M18 blocks and in §5.

**What changed.**

- **The tree** (`components/GrowthTree.vue`, rewritten) grows vertically.
  It is still drawn from `growthOf(events)`, so it remains a pure
  function of the log.
  - **Planting:** the seed, and a root per layer.
  - **Discovery (sapling):** a sprout, then a small leaf per system
    reached.
  - **Assessment (small plant):** a pair of leaves per methodology
    assessed.
  - **Implementation (tree):** the trunk heightens and thickens, and a
    branch grows per Agent Component, lengthening and gaining a foliage
    cluster with each part built, fruiting when ready. The crown fills
    out with the build, and the lower stem leaves thin as the trunk
    matures.
  - **Caption:** the stage and its phase in the process's own terms, for
    example "Small plant · Assessment · 3 methodologies assessed ·
    waiting on input".
  - **Watering is unchanged:** an allowed request soaks in as a dot, a
    refused one is held above the ground, and the tally reads "Watered by
    N tool requests".
- **Smooth growth.** Every dimension (height, girth, branch length, leaf
  and foliage size) eases towards the state the log describes, so growth
  is continuous at any speed and never flashes. A reload, and reduced
  motion, go straight to the final state. A falling drop still plays
  only for a request that arrives on its own.
- **The Life pane** (`views/LifeView.vue`) shows the tree from planting
  until the build completes, headed "Agent One VW (ValueWise™) ·
  Growing". At `IMPLEMENTATION_COMPLETE` the tree fades out and a
  "Seeding complete" statement fades in, with Agent One VW (ValueWise™)
  and its ready Agent Components below. Reduced motion skips the fade.
  The old empty state is gone.
- **Layout** (`stores/layout.ts`): Life only from planting until the build
  completes. A request still brings the Seeding pane forward (FR-W5).
- **The Seeding pane** has `LifecycleStrip.vue` back, restored exactly as
  it was before M17.

**Files.** `frontend/src/components/GrowthTree.vue`,
`components/LifecycleStrip.vue` (restored), `views/LifeView.vue`,
`views/WorkspaceView.vue` (restored to its pre-M17 form),
`stores/layout.ts`; `docs/decisions.md`, `docs/requirements.md`,
`docs/implementation-plan.md`.

**Gates.** `pytest` gives 431 passed. Typecheck and build pass. Live:

- Planting opens Life only with the seed in the soil, and the Seeding
  pane has the strip.
- The captured stages read seed, sapling, small plant and tree, the tree
  with a crown and foliage on its branches.
- A reload at the approval point rebuilt the identical tree.
- Two runs from Reset grew identical trees at the credential pause and at
  approval.
- A full-motion session settled on exactly the tree a reduced-motion one
  drew.
- At build completion the tree gave way to "Seeding complete · Agent One
  VW (ValueWise™)" with the ready list.
- The M14 walkthrough passes 31 of 31, with its expectations updated for
  D-18: the default layout after planting, and the tree in place of the
  empty state.

One observation, not a fault. During a run at instant speed, 2 drops
still fell. Each was the first request after a pause for a person, so it
arrived alone. That is two isolated drops in a whole run, not strobing.

**Check by hand.**

1. Watch a run at 1x in Life only: the seed, sapling, small plant and
   tree, the smoothness, and the hand-over.
2. Judge the tree's look (R-14). M21 designs it properly.
3. Confirm that the lost default view of the stages is acceptable. The
   Seeding pane is one click away, and it comes forward on its own for
   every question.

### Follow-up · layout, scrollbars and the tree's look (after D-18 review)

**Requested, 2026-09-24, after reviewing D-18:**

- scrollbars styled to the theme;
- Both no longer squeezing the Seeding pane, with the Activity rail
  moved to a collapsible drawer at the bottom;
- the human-input box in Discovery and Assessment no longer covering
  the Activity rail;
- bushier roots in their own colour, a denser and wider tree, and soil
  that fades so the roots show.

**What changed.**

- **Scrollbars** (`design/base.css`, `design/tokens.css`): every
  scrolling pane has a thin thumb drawn from the theme's line colours on
  a clear track, in both themes. New tokens: `--scrollbar-thumb` and
  `--scrollbar-thumb-hover`.
- **The Seeding pane** (`views/WorkspaceView.vue`):
  - The human-input surface now sits under the stages, inside the stage
    column, so it never covers the Activity rail. A long request scrolls
    within itself rather than crushing the stage.
  - In Both, the rail docks along the bottom of the pane as a drawer of
    fixed height, and the stages keep the pane's full width. The drawer's
    bar has a toggle. Closed, the bar still shows the newest entry's kind
    and message. In Seeding only, the rail stays at the side as before.
  - The rail stays mounted in every placement, so the stream keeps its
    state (NFR-A7).
- **The tree** (`components/GrowthTree.vue`), still `growthOf(events)`
  and still deterministic:
  - **Roots** are earth brown (`--growth-root`). Each layer's main root
    grows four laterals and eight fine hairs. They bush out as the plant
    above them grows: a few at planting, the whole system once the build
    is well under way. The roots thicken with the trunk.
  - **Soil** is a warm tint (`--growth-soil`, `--growth-surface`) at the
    surface that fades downward and at both ends, so the roots show
    through it.
  - **Branches** spread wider and shallower. Each part built grows a twig
    with a small tuft and two leaves.
  - **The crown** spreads wide, in a deeper green (`--growth-leaf-deep`),
    and gains two leaves for every part built. The lower stem leaves
    thin out further as the trunk matures.
  - The drawing is wider (a 520 × 500 view) and may grow taller on
    screen.
- **Docs:** decisions.md, a note in D-14 on the rail in Both, and in
  D-18 the stage table and the tree's look.

**Files.** `frontend/src/design/base.css`, `design/tokens.css`,
`views/WorkspaceView.vue`, `components/GrowthTree.vue`;
`docs/decisions.md`, `docs/project-notes.md`.

**Gates.** `pytest` gives 431 passed. Typecheck and build pass. Live, in
dark and light:

- Discovery (credentials) and Assessment (approval) were each checked in
  Both and in Seeding only. In all four, the request box's bounds clear
  the rail's.
- In Both the rail is docked at the bottom. It closes to a bar that
  shows the newest entry.
- The tree was captured at planting, as a sapling, as a small plant,
  mid-build and late in the build.
- A reload at approval rebuilt the identical tree, two runs from Reset
  grew identical trees, and the hand-over still appears at build
  completion (5 of 5).
- The M14 walkthrough passes 31 of 31.

**Check by hand.**

1. Choose Both during Discovery: the stages keep their width, and the
   Activity drawer sits at the bottom. Close and reopen it.
2. Scroll the Activity stream and the stages in both themes.
3. Watch the tree grow at 1x: the roots bush out, and the crown widens.

### Follow-up · Both during the build, the Growth control, and the tree's look (D-19)

**Requested, 2026-09-24, after reviewing the previous follow-up:**

- the stem changes colour as the tree grows;
- the tree stays reachable after the Life phase, from a drop-down at
  the top of the Life pane;
- clusters almost covered in leaves, with texture on the leaves, the
  stem and the clusters;
- denser roots, with more nodules and threads;
- Both, not Life only, during the build.

These are ruled as D-19, with A-13 and A-14, and applied in
decisions.md, requirements.md and the plan.

**What changed.**

- **Layout** (`stores/layout.ts`): the default is Both from planting
  until the build completes. It is Life only from `READY_TO_RUN`.
- **The Life pane** (`views/LifeView.vue`): after the hand-over, a
  **Growth ▾** control in the header drops the grown tree open above
  Agent One VW, and closes it again. It is closed by default, and a new
  run starts closed.
- **The tree** (`components/GrowthTree.vue`):
  - **Stem.** A new `age` target runs from 0 at the sprout to 1 late in
    the build. It colours the trunk by mixing `--growth-stem-young` with
    `--growth-bark`. Branches lag the trunk, and twigs lag the branches.
    A bark-furrow pattern fades in with age, over a rounded shading.
  - **Foliage.** Clusters take a radial gradient, lit from the upper
    left. A single leaf shape with a midrib is placed by `<use>`, and
    leaves cover every crown disc, branch cluster and twig tuft. They
    sit on a fixed-spacing sunflower spiral from the centre, so a
    growing cluster gains leaves at its rim and the ones already there
    stay put. The outer leaves reach past the rim, in three greens. A
    grown tree carries about 900 leaves.
  - **Roots.** There are eight laterals per main root, four hairs each,
    and nodules along the laterals. Six finer fibres come in as the
    roots bush out. Roots are clipped below the surface. A stroke that
    has not started is left out, because a round cap on an empty dash
    painted a stray dot.
- **Tokens** (`design/tokens.css`): `--growth-stem-young`,
  `--growth-bark`, `--growth-leaf-light` and `--growth-nodule`, in both
  themes.

**Files.** `frontend/src/stores/layout.ts`, `views/LifeView.vue`,
`components/GrowthTree.vue`, `design/tokens.css`; `docs/decisions.md`,
`docs/requirements.md`, `docs/implementation-plan.md`.

**Gates.** `pytest` gives 431 passed. Typecheck and build pass. Live, in
dark and light:

- The layout after planting is Both.
- The trunk's colour moved from 30.6% to 86.4% bark between the small
  plant and late in the build.
- At the hand-over the tree is closed behind the Growth control, which
  drops it open.
- The request box still clears the rail, and the drawer still closes.
- A reload at approval rebuilt the identical tree, two runs from Reset
  grew identical trees, and the hand-over still appears at build
  completion (5 of 5).
- The M14 walkthrough passes 31 of 31. Its expectation for the layout
  after planting is updated to D-19.

These ran against an isolated copy of the app, on ports 8001 and 5174.
A browser left open on the shared app changed its state mid-run, which
twice broke the walkthrough at unrelated steps. Windows Application
Control had also begun blocking `uv.exe`, so pytest ran through the
project's `.venv` interpreter.

**Check by hand.**

1. Plant and watch at 1x. The layout is Both, and the stem turns from
   green to bark as the build proceeds.
2. At the hand-over, open and close **Growth ▾** in the Life header.
3. Judge the leaf cover and the root density in both themes.

### Follow-up · watering pulse, stem and roots joined, Growth fills the pane

**Requested, 2026-09-24:**

- the Growth control covers the whole panel;
- the stem and roots are joined;
- watering is shown as a blue tint through the ground and roots while
  the tree glows and grows a little, not as drops on the ground.

These are recorded under D-19 and FR-G3.

**What changed.**

- **Growth** (`views/LifeView.vue`) now overlays the Life pane's body,
  everything below the header, and is revealed top first. What lies
  beneath stays mounted.
- **The join** (`components/GrowthTree.vue`): the trunk runs below the
  surface to the seed, where the roots start, and flares there.
- **Watering:**
  - The drops in the soil and the falling drop are gone.
  - Each allowed request sets a 1.1-second pulse on the figure: a
    water-blue tint over the soil and a wet-blue stroke on the roots
    (`--growth-root-wet`), with a drop-shadow glow on the plant
    (`--growth-glow`).
  - In a burst, a new pulse starts only once the last one has run.
  - Each allowed request adds a little height, girth and crown, capped
    at 30 requests and counted from the log, so the tree grows as it
    glows.
  - Refused requests are still held above the ground.

**Gates.** pytest gives 430 passed. The one failure is the known 200 ms
timing test, flaky under load and ruled not a problem. Typecheck and
build pass. Live, on an isolated copy of the app:

- A pulse was caught mid-run, with the soil tint at opacity 0.23 and the
  roots at `rgb(141, 163, 199)`. It had cleared a second later.
- No drops are in the soil.
- Growth covers the pane body exactly.
- The trunk and the roots both start at y 381.
- Replay and Reset gave identical trees (5 of 5).
- The M14 walkthrough passes 31 of 31.

**Check by hand.** Watch a run at 1x: each allowed request should read
as a soft blue soak and a glow.

### M18 · Closing the seeding phase

**Asked for, 2026-09-24:** show a clean-up before Life. The
implementation and seeding are complete, the tools that built Agent One
VW are discarded, and the seed is fully consumed because the tree now
carries what it held. Show it in the Activity stream, and in the tree if
possible.

This is M18, built with three decisions, recorded as D-20 and A-15:

- a person confirms, as D-16 rules;
- D-16's three operations stand, and a fourth retires the build tools;
- the tree sheds a stake and its seed husk.

**What changed.**

- **Lifecycle** (`domain/lifecycle.py`): `CLOSING_SEEDING` sits between
  `IMPLEMENTATION_COMPLETE` and `READY_TO_RUN`, in the Implementation
  phase. The direct edge is gone.
- **Workflow** (`simulation/workflows/closing.py`, new, registered after
  implementation):
  - A `confirmation` request, `close-seeding`, with the one option "Run
    — clean up and close seeding" and FR-H2's what, access and why.
  - Then four steps, each a capability request decided and recorded:
    1. consolidate the working notes (PR-090);
    2. purge scratch space (PR-091);
    3. promote each interface on its recorded approval (PR-093);
    4. retire the component generator and the test runner (PR-095).
  - Then "seed consumed", and the hand-over (`deployment.ready`, moved
    here from implementation).
  - `state.closing` records what was done, and the snapshot carries it.
  - It weighs 6 beats; `NARRATIVE_WEIGHT` is now 105.
- **Rules** (`protection/rules.py`, `seeds/protection.md`): four actions,
  three facts (`system_owned`, `deployment_approved`, `build_complete`)
  and the group "Closing the seeding phase", PR-090 to PR-096. The
  parity test passes. `BUILD_TOOLS` is in `protection/capabilities.py`.
- **Frontend:**
  - `ClosingSteps.vue` (new) ends the Implementation stage with the
    checklist and its rule ids.
  - The Activity stream has a CLEANUP divider (`dividerOf` in
    `design/presentation.ts`), and now follows the newest entry
    reliably: a programmatic smooth scroll had been switching following
    off during bursts.
  - The Life pane hands over at `READY_TO_RUN`. Its header reads Built,
    then Cleaning up.
  - `growth.ts` tracks the stake, the closing steps and the seed
    consumed. `GrowthTree.vue` draws the stake and husk, with tokens
    `--growth-stake` and `--growth-tie`.
  - `system.ts` and `events.ts` gain the state and the six events.

**Test edits.** This is the milestone allowed to edit assertions. The
plan expected one edit, in the state-machine suite. That suite is
generated from the transition table, so it needed none, and it now
covers the new edges on its own. These needed edits instead, each a
direct consequence of D-16:

- `test_implementation.py`:
  - the last lifecycle moves now include `CLOSING_SEEDING`;
  - the weight shares are now implementation 20 and closing 6.
- `test_assessment.py`: two tests answer the new confirmation before
  asserting completion. Their assertions are unchanged.
- `test_presentation.py`: the six new event types are classified.
- `test_protection.py`: the witness table gains the three new facts.
- `narrative.py`: the harness answers the confirmation.

New: `tests/test_closing.py`, 13 tests. They cover:

- the edges, legal and illegal;
- the confirmation;
- each step's order and rule;
- the closing record;
- a rejected component not promoted;
- scratch versus client data (PR-091, PR-092, PR-051);
- promotion reading the approval;
- retirement mid-build;
- the seed unchanged;
- skip passing through closing (FR-C7).

**Gates.** `pytest` gives 475 passed. The one failure is the known
200 ms timing test. Typecheck and build pass. Live, on an isolated copy
of the app (11 of 11):

- The run pauses for the confirmation at `IMPLEMENTATION_COMPLETE`, with
  the layout Both and the tree staked.
- The confirmation is answered through its button.
- Mid-clean-up, the tree reads "Shedding the seed" and the stream has
  the CLEANUP divider.
- The stake lifts away when the tools are retired.
- Every step appears in the stream with PR-090, PR-091, PR-093 and
  PR-095, and the protection tally counts 34.
- The layout hands over to Life at `READY_TO_RUN`.
- The grown tree stands without stake or husk, and a reload rebuilds it
  identically.
- Replay and Reset matched (5 of 5), and the M14 walkthrough passes 31
  of 31. Both drivers now confirm closing.

**Check by hand.**

1. At 1x, confirm "Run — clean up and close seeding". Watch the
   checklist tick through, the stream purge, and the tree lose its stake
   and seed.
2. Restart your own app server first: the one on port 8000 predates
   these backend changes.

### Follow-up · roots that grow and fade, and Cleanup by name

**Requested, 2026-09-24, after M18:**

- roots slightly blurred, so they appear to grow on out of view and be
  cut off by it;
- roots that grow with the plant rather than appearing whole at
  planting;
- a new name for "Closing the seeding phase";
- a report that cleanup was not working.

**Cleanup not working.** The app server on port 8000 had been started
before M18. It served none of PR-090 to PR-096, so the run went straight
from Implementation to Ready. The server was restarted. The cleanup also
sat below the build lanes, out of view, so it could pass unseen. It is
now scrolled into view when the confirmation is asked for and when
cleanup begins.

**What changed.**

- **Roots** (`components/GrowthTree.vue`):
  - A `rootReach` target replaces `rootSpread`. It starts as a radicle
    at planting, 8% of each main root, and grows with the systems,
    methodologies and parts to 1 late in the build.
  - A lateral grows only once its root has passed the point it leaves
    from, with its hairs and nodules just behind. The fibres follow the
    main roots.
  - The roots are about 35% longer. They are drawn in one bed, clipped
    at the surface, masked by a radial fade centred on the seed (wider
    than deep), and given a 0.55 Gaussian blur.
- **The name.**
  - The checklist reads "Cleanup, after implementation".
  - The bar shows `CLEANUP` for `CLOSING_SEEDING`, in `App.vue`.
  - The tree's caption reads "Cleanup".
  - The prompt and the opening event speak of cleanup.
  - Internal names are unchanged.
- **Scroll** (`components/ClosingSteps.vue`): the checklist is scrolled
  into view at the confirmation and at the start of cleanup.

**Gates.** `pytest` gives 473 passed, with the 200 ms timing test
deselected. Typecheck and build pass. Live, on an isolated copy of the
app:

- At planting only a radicle shows: dashoffset 0.92, no laterals.
- The roots lengthen through the sapling (0.84, 3 laterals) and the
  small plant (0.77, 11 laterals).
- They are fully out by the build's end, with 45 laterals, 6 fibres and
  33 nodules.
- The bed is masked and blurred.
- The checklist is titled Cleanup and scrolled into view, and the bar
  reads `CLEANUP`.
- Cleanup hands over to Life.
- The M18 check passes 12 of 12, replay and Reset 5 of 5, and the M14
  walkthrough 31 of 31.

### Follow-up · roots blur with depth, and a leaner Life pane

**Requested, 2026-09-24:**

- the roots blur more, the blur fading in from the lower half of what
  shows;
- the roots are slightly dimmer;
- the Life pane drops the build record;
- "System ready" gets another name.

**What changed.**

- **Roots** (`components/GrowthTree.vue`):
  - They are drawn twice. The sharp drawing, with a 0.4 blur, is masked
    to the top of the root bed. A `<use>` copy, with a 2.2 blur, is
    masked to the bottom. The two cross over through the middle of the
    visible roots, about 25 to 68% of the way down.
  - The seed-centred radial fade still dissolves them at the edges.
  - The colours are dimmer: `--growth-root` and `--growth-nodule` in
    both themes.
- **Life** (`components/RuntimeStage.vue`): the build record (the build
  lanes) is gone from Life, and the Implementation stage keeps it. The
  list is headed "Live Agent Components". The hand-over event reads
  "Agent One VW is live. Three Agent Components ready to run."
  (`workflows/closing.py`).
- **Docs:** decisions.md, D-19's roots and D-20's Life pane.

**Gates.** `pytest` gives 473 passed, with the 200 ms timing test
deselected. Typecheck and build pass. Live, on an isolated copy of the
app:

- The root bed has the sharp and blurred layers.
- Life shows no build record and the new heading.
- The stream says Agent One VW is live.
- Replay and Reset give 5 of 5, the M14 walkthrough 31 of 31, and the
  M18 check 12 of 12.

### M20 · Remaining dashboards

**What was already there.** M9 built all three generators and declared
all three dashboards in the descriptor schema. M10 built the generic
renderer. So License Optimization and Application Portfolio
Rationalization were already served and rendered. M20's work was to
prove they hold up in the Life pane, as the exit asks: *both dashboards
work with no new UI code and no new backend query code.*

**Verified live**, on an isolated copy of the app, each dashboard run
from the Life list:

- **License Optimization** ("Licence Utilisation"):
  - The dashboard opens in Life, URL-synced.
  - Five KPIs: 13,620 entitled, 13,002 assigned, 9,496 active, 3,171
    unused or underused, and $390k recoverable a year, over priced
    products only, with 975 seats withheld.
  - All four charts draw: the treemap, entitled against active, the
    monthly trend and recoverable cost.
  - The candidate and record tables fill.
  - A treemap click drills and narrows the figures (Microsoft 365 E3,
    Unused: 104 seats, $45k).
  - A seat row reaches the record level (LIC-001848), and Back pops one
    step.
- **Application Portfolio Rationalization** ("Application Portfolio"):
  - The dashboard opens in Life, URL-synced.
  - Five KPIs: 186 applications, $4.76M, 49,099 users, $97 per user and
    326 dependents.
  - All four charts draw, and both tables fill.
  - A treemap click drills to one application, and a row reaches its
    record level. Back pops one step.
- No console errors across either dashboard.

That makes three to four charts and a drill path each (FR-AN7), with no
methodology-specific UI (FR-EV4).

**One descriptor fix.** At the record level, Application Portfolio
labelled its breadcrumb with the application's name, the same as the
application-level crumb before it: "Portfolio / API Gateway EMEA / API
Gateway EMEA". Its `Entity.title` now names the application id, as
Ticket Anomaly names the ticket number. The trail reads "Portfolio /
API Gateway EMEA / APP-0158". This changes the descriptor only: no UI
code and no query code (`descriptors/applications.py`).

**Noted, not changed.** A treemap leaf click drills to the leaf's whole
path in one step. In License Optimization, that sets vendor, product and
utilisation class, and the crumb reads just "Unused". This is the
generic renderer's behaviour, shared by every dashboard. Changing the
label would be UI code, so it is left for M21's design pass.

**Gates.** `pytest` gives 476 passed; the 200 ms timing test passed this
time. Typecheck and build pass. The diff touches no frontend file and no
query code. M18's hash, `8e2c525`, is backfilled.

**Check by hand.** Run License Optimization and Application Portfolio
from Life, click into each treemap, then open a record.

### M19 · Life: collection and recalibration

D-17, Option B. After the seeding phase closes, Agent One VW collects
the final twelve simulated weeks of each dataset, one week a step,
recalibrates every four, and ends caught up. Every figure is still
computed from generated rows. The starting values are recorded under
D-17, "As built".

**Measured first.** The plan put generation at 0.108 s. It is 0.41 s
today, the tickets frame being most of it. With every calibration and
Life's plan precomputed, the whole build takes 0.80 s, inside NFR-P1's
2 s and the startup test's 1.5 s. A first version took 1.23 s. Moving
the ticket baselines to `bincount`s over category codes, and dropping
string comparisons from the plan, brought it down, with identical
results.

**What changed.**

- **Generators.**
  - Every frame carries a `collected` step: 0 for what was already
    collected, 1 to 12 for each week of the window.
  - `generator/__init__.py` holds the shared clock: `STEPS`, `EVERY`,
    `step_of`, `month_step`, `calibration_of` and `week_of`.
  - `tickets.calibrate` and `applications.calibrate` return, for each
    calibration, only the columns that differ from the generated frames.
  - The last calibration is empty, so the caught-up state is exactly the
    generated frames.
- **Schema and store.**
  - A `Collection` spec on each descriptor names the frame whose arrivals
    are reported, the source, the noun and any dimension that
    recalibration confirms.
  - `Dataset.at(c)` gives the frames as calibration c saw them: shallow
    copies with the recalibrated columns swapped in. Other columns are
    shared.
  - `Dataset.arrivals` and `Dataset.recalibrations` are Life's plan,
    counted from rows at startup: arrivals per step, and what each
    recalibration moved and confirmed.
- **Query engine.**
  - `FilterContext.step` is one more term (FR-LF7). With no step, the
    engine reads the full dataset, so every existing caller and test is
    unchanged.
  - The step narrows every frame, "of total" figures included, and reads
    under the calibration in force.
  - The evidence panel names its calibration (FR-LF9), and whether a
    selected cluster is confirmed or provisional.
- **API.** The dashboard endpoint describes the clock: steps, and each
  step's week and dates.
- **Life workflow** (`workflows/life.py`, run after the narrative in
  `runtime.py`):
  - It collects only for live Agent Components.
  - Each step is an event naming the source, the count and the week,
    labelled simulated.
  - Every four steps, a recalibration reports the baseline that moved
    most, and the clusters confirmed or withdrawn.
  - It ends with `life.caught_up`.
  - `state.collection` is the system cursor, and the snapshot carries it.
- **Frontend.**
  - The system store follows the cursor.
  - The Life header shows collection progress.
  - The dashboard store holds the view cursor, URL-synced as `step`:
    - at the top it follows the system;
    - a drill pins it;
    - the drill bar says how many collections are newer, and offers
      Catch up;
    - returning to the top follows again.
  - The evidence panel shows the calibration.

**Test edits.** None. All 476 existing tests passed unchanged.
`tests/test_life.py` adds 55. They check:

- the step term against the rows, for every frame, at seven steps;
- ticket KPIs growing step by step;
- filters combining with the step;
- the caught-up state equalling the full dataset;
- the generated frames staying untouched;
- baselines recomputed from the rows;
- the first recalibration confirming Cluster 27;
- provisional clusters becoming confirmed;
- application figures following the latest month;
- the evidence naming its calibration;
- pinned figures holding still;
- the workflow's events matching the rows;
- two runs from Reset matching;
- a rejected component not collected;
- zero narrative weight;
- skip completing collection, and Reset clearing it;
- the events subscribed and presented as activity;
- the API, and the running app collecting after closing.

**Gates.** `pytest` gives 531 passed. Typecheck and build pass. Live, on
an isolated copy of the app, at 2x (13 of 13):

- Life shows its progress.
- A top-level dashboard grows with collection: 139,438 tickets, then
  146,871.
- Drilled in, the view holds still and reads "Pinned to week 25 · 2
  newer collections".
- The evidence names its calibration.
- Catch up moves to the newest step, and the top follows again.
- Caught up, the dashboard shows 184,392 tickets.
- The stream has twelve collection steps. "Recalibration 1, week 27"
  moves the Resolution stall baseline from 35.71 to 34.82 hours and
  confirms Cluster 27, and the stream ends caught up.
- `?step=4` opens week 27 pinned, with the API's figures.
- The regressions pass: replay and Reset 5 of 5, the M14 walkthrough 31
  of 31, and the M18 and M20 checks.

**Check by hand.**

1. Close seeding at 1x. Watch the Life header count the weeks, open
   Ticket Anomaly Detection and see the totals grow.
2. Drill into a cluster and watch it hold still, then Catch up.
3. Read the recalibration entries in the Activity stream.

### M21 · Design pass

A review of every stage in both themes, from screenshots of a full run
on an isolated copy of the app. It settles OQ-3, checks contrast in a
test, and fixes what the review found. Nothing changes the narrative,
the rules or a figure. One fix changes what the query engine returns
during Life, and it is below.

**OQ-3, settled.**

- **Typeface:** Inter, with JetBrains Mono for figures and identifiers.
  The tokens named both from the start, but neither was installed, so
  the app rendered in Segoe UI on this machine and in something else on
  another. Both are now bundled from npm (`@fontsource-variable`) and
  served with the build, never fetched (NFR-D2). The Latin files add
  about 90 kB, loaded only when used.
- **Accent:** cobalt, as before, nudged to `#1e61f5` in the light theme
  so that it and its button label pass contrast. The dark theme's
  `#5b8cff` already did.
- ECharts draws text onto a canvas, once. A chart painted before the
  faces arrive is drawn again when they have.

**Contrast, now a test (NFR-V3).** `tests/test_design.py` reads
`tokens.css` and checks, in both themes, against WCAG 2.1:

- every text role on every surface, and on the selected-row tint, at
  4.5:1;
- the primary button's label on the accent, at 4.5:1;
- every chart role against the panel, at 3:1;
- every chart label on its fill, at 4.5:1, with light text on a filled
  role and dark text on the baseline and muted fills, as
  `charts/options.ts` chooses.

`chart-muted` is exempt from the 3:1 check, and only that one: it is
the colour of what no pattern applies to, and is meant to recede. Its
label still has to read. Against the tokens as M20 left them, 33 pairs
failed, 23 in the light theme and 10 in the dark. Each failing colour
moved in lightness only, keeping its hue:

| Token | Theme | Was | Now | Why |
| ----- | ----- | --- | --- | --- |
| `text-muted` | light | `#79818f` | `#666e7a` | 3.4:1 on sunken |
| `text-muted`, `status-neutral` | dark | `#6f7885` | `#808995` | 3.6:1 on overlay |
| `accent`, `chart-series-1` | light | `#2f6df6` | `#1e61f5` | its button label read at 4.3:1 |
| `accent-subtle` | both | `#e6edfe` / `#17233d` | `#ebf1fe` / `#15203a` | muted text on a selected row at 3.4:1 |
| `status-warning` | light | `#a96a00` | `#9a6100` | 3.9:1 on sunken |
| `status-positive` | light | `#1b7f4b` | `#1b7d4a` | 4.4:1 on sunken |
| `grade-medium` | light | `#5f7f1a` | `#597718` | 4.1:1 on sunken |
| `chart-series-3` | light | `#0e8f8f` | `#0c7f7f` | its treemap label at 3.7:1 |
| `chart-series-4` | light | `#a96a00` | `#a16500` | its treemap label at 4.2:1 |
| `chart-series-6` | light | `#5f7f1a` | `#5d7c19` | its treemap label at 4.4:1 |
| `chart-warning` | light | `#b7791f` | `#9c671a` | its label at 3.4:1 |
| `chart-anomaly` | light | `#d1451f` | `#cc431e` | its label at 4.3:1 |
| `chart-baseline` | both | `#9aa2b1` / `#4a5461` | `#8c95a6` / `#5b6777` | the baseline line at 2.6:1 and 2.3:1 |

**The pane shell.**

- In the Both layout, the pane where the work is happening leads and
  takes three fifths: Seeding while the seed grows, when Life holds only
  the tree, and Life once Agent One VW runs (`layout.lead`).
- The layout control stays at the centre of the bar. The bar was a
  space-between row, so the control drifted with the length of the
  lifecycle label: 703px while INITIALIZED, 659px at
  IMPLEMENTATION_COMPLETE. It is a three-column grid now.

**Legibility in the Both layout.** Two hand-built SVGs scale to their
column, and at half the screen their text shrank below 7px.

- The environment graph's 900-unit canvas drew at 0.52 scale. With the
  wider pane and a narrower side column it draws at 0.76, and a
  container query sets its labels larger in a narrow pane only. They
  now read at 9.8 to 10.6px. The legend goes to one column there.
  While a request is open under it, the graph is limited by height
  instead and draws at about half size again. The request has the
  viewer's attention then, and this pass leaves it.
- The build lane's nodes are wider, so "Dependency graph" and
  "Disposition engine" no longer overrun their boxes. Its kicker and
  detail text are a size up.

**The Life pane.**

- **A month not yet collected drew as zero.** Early in collection the
  ticket volume line fell to nought in July and August, which reads as
  a collapse. A category with no record collected yet is now unknown,
  `null`, so the line stops where collection has reached. The months
  still arriving, the partial one included, are shaded and labelled
  "Collecting", so June's lower figure reads as incomplete rather than
  as a fall. The query answer carries `collecting`, the categories not
  yet complete. With no step, or caught up, it is empty and every
  figure is as before.
- **The pinned view (R-18).** It is treated as M19 built it: the drill
  bar says "Pinned to week N · K newer collections" in the caution
  colour, beside Catch up, and the evidence panel names its
  calibration. The review found nothing to change.
- **Growth covered all but the evidence panel.** The panel sat above
  the overlay. The overlay now covers the whole pane.
- **A treemap cell drills several levels at once.** Its crumb named only
  the cell ("Cluster 25", or "Unused" on Licence Optimization), so the
  breadcrumb no longer said where the view stood. The crumb now names
  each level the click added: "Reassignment loop › Application Support
  - SAP › Cluster 25". It is still one crumb, for one click.

**Motion budget (R-14, NFR-V7).** Reviewed, unchanged.

- The tree has one animation: a 1.1-second pulse per watering event
  (tint, wet roots, glow). It is off under `prefers-reduced-motion`, and
  coalesces at instant speed (M15).
- Every infinite animation in the app is tied to a live state: an edge
  flowing while a component builds, a sweep while it tests, and the
  drill bar's loading line.

**Also.** The seed cards' counts kept too little space between a figure
and the next label, so "51 Sections" read as one. The first figure in
each row now keeps its distance.

**Test edits.** None. `test_design.py` adds 13 tests. `test_life.py`
adds 7, at seven steps: a month not yet collected draws no point, and
`collecting` is every month not yet complete.

**Gates.** `pytest` gives 551 passed. Typecheck and build pass. Live, on
an isolated copy, dark and light:

- in Both while seeding, Seeding is 960px of 1600;
- environment labels read at 9.8px or more;
- every build-lane label fits its box;
- the layout control is centred at 800px as the lifecycle label changes;
- in Life, Life leads;
- Growth covers the evidence panel;
- a treemap leaf's crumb names its three levels;
- the volume line stops at the cursor, under "Collecting".

The M19 and M20 checks, and replay and Reset, pass.

**Check by hand.**

1. Toggle the theme (Shift+D) at each stage and read the muted labels
   and the treemap labels.
2. In the Both layout during Discovery and the build, read the graph
   and the lane without leaning in.
3. Open Ticket Anomaly Detection early in Life: the line stops, and the
   months after it are shaded "Collecting".

### Follow-up · setup and launch without uv (`run.ps1`, 2026-09-29)

**Why.** Windows Application Control on the build machine began
blocking `uv.exe` on 2026-09-24, and by 2026-09-29 also the `python.exe`
inside a venv that uv had made. `uv run run.py` no longer starts the
app there.

**What changed.** `run.ps1` (new) does the pip route that
`requirements.txt` already described, in one command:

```
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

- It checks that npm is on the path first, because `run.py` fails
  without it, after a slow install.
- It finds Python 3.12 or newer: the `py` launcher first, then
  `python` and `python3`.
- It creates `.venv`, rebuilds one whose interpreter will not run, and
  adds pip to one that uv made without it.
- It installs `requirements.txt` only when the file has changed since
  the last install, recorded by hash.
- It checks that pandas, FastAPI and uvicorn import, and says what to do
  if Smart App Control blocks pandas's compiled files.
- It hands over to `run.py`. `-Dev` installs `requirements-dev.txt`
  instead, for the tests.

`-ExecutionPolicy Bypass` applies to that one process, so nothing needs
admin rights. `requirements.txt` gains a line pointing to it. Recorded
as D-21.

**Files.** `run.ps1` (new), `requirements.txt`.

### Follow-up · the product named Seed v0.1 (2026-10-02)

**What changed.** The top bar reads "Seed v0.1" where it read "Seed V1",
and so does the browser tab. The FastAPI title and the launch banners of
`run.py` and `run.ps1` still said "Systems V1", the name from before
M11, and now say "Seed v0.1" too. Display only (D-11). Recorded as
D-22.

**Files.** `backend/app/main.py`, `frontend/index.html`,
`frontend/src/App.vue`, `run.py`, `run.ps1`.

### M22 · Rehearsal and hardening

The whole run, rehearsed: through the running app twice from Reset, and
once at 1x through the interface only, the way a presenter gives it.
Two defects turned up and are fixed. The timing stays where it was, and
OQ-4 is closed.

**A capital letter could reset the run.** The operator shortcuts are all
on Shift, and the code said that kept them clear of the credential form.
Shift is how a capital letter is typed, though, and the handler did not
look at where the key went. A presenter typing "Rachel" into the account
field would have reset the run at the R; an S would have skipped the
phase. Shortcuts are now ignored while a field has focus. The rehearsal
types "Rachel.SVC" key by key, Shift for the capitals, and the run
carries on. FR-O2 itself held already: the operator panel never showed
in the rehearsal, and nothing outside it names a shortcut.

**The engine ran slow under load.** A beat's sleep is cut into 50 ms
slices so a speed change lands quickly (FR-O3), and the engine counted
the slices it asked for, not the time that passed. A sleep can overrun
its slice, by up to a timer tick, and more when the machine is busy. In
the first 1x rehearsal, with Chrome working hard, the narrative took
297 s of its 270 and Life 60 s of its 45. Progress is now read from the
loop's clock, in the beat's own seconds, so a speed change mid-beat also
resumes from where the beat stands. A beat can still overrun by its last
sleep's overshoot, about 10 ms, about 1 s over the narrative.

**Timing (D-8, OQ-7, R-15, D-17).** Measured beat by beat at 1x:

| Part | Seconds |
| ---- | ------- |
| Planting to Discovery complete | 139 |
| Assessment and the approval request | 64 |
| Implementation | 51 |
| Cleanup | 15 |
| **Narrative** | **270** |
| Life, outside the narrative | 45 |

No floor binds at 1x: every beat lasts its share, so the one number
still retimes the whole narrative. **The 270 seconds stay.** Answering
the three requests adds what a person takes, about half a minute in a
real run, so the narrative lands at about five minutes, the top of
OQ-7's window. Raising the total would push past it. Closing's six units
(R-15) are inside the 270, and the rest of the narrative runs about 6%
faster than before M18 to make room: discovery's beats are 2.57 s per
unit where they were 2.73. Life's clock keeps D-17's starting values, 3 s
a step and 2 more per recalibration: about 45 s to caught up, long
enough to drill in and watch a view pin.

**Determinism (NFR-D1 to D4, A-2, FR-G5).** `tests/test_rehearsal.py`
plants the bundled seed over HTTP, answers every request over HTTP, runs
through closing and Life to caught up, resets and does it again. Then:

- every event and the final System State match;
- wherever the raw runs differ at all, both sides are wall-clock times.
  This is A-2 stated exactly, checked leaf by leaf, rather than by
  dropping keys that look like times. Dropping them would have hidden a
  difference: `decidedAt` holds an event sequence number, not a time;
- the growth tree ends identical. The tree is the frontend's pure
  function of the event log, so the test bundles `growth.ts` with
  esbuild, runs it under Node over both runs' events, and compares the
  fingerprints. The tree it compares is the grown one: three branches,
  four clean-up steps, the seed consumed.

The same file holds the timing and two guards for the demo's
conditions: no URL in the code names a host other than this machine
(NFR-D2), and no model library is a dependency (NFR-D1).

**OQ-4, closed: no virtualisation.** After a full run the stream holds
142 entries, about 900 elements. Scrolling it end to end holds 17 ms
frames, and a reload replays all of it in 1.9 s. What does cost the
page is elsewhere, measured at 2x by phase:

| While | Tasks over 50 ms | Total | Longest |
| ----- | ---------------- | ----- | ------- |
| Implementation, the tree growing | 34 | 1.8 s | 75 ms |
| Cleanup, the tree changing | 28 | 1.7 s | 134 ms |
| Life, a dashboard following collection | 13 | 1.4 s | 334 ms |
| Discovery and Assessment | 2 | 0.2 s | 139 ms |

The tree eases each change over about a second, and every frame of that
re-renders the whole drawing. A dashboard that follows collection redraws
every chart at each step. Neither stalls the stream, whose entries land
on time, and neither is in this milestone's exit. Both are recorded here
as the place to look if the demo machine is slower than this one.

**Test edits.** None. `test_rehearsal.py` adds 10 tests, one of them for
the engine: every sleep made to overrun by 25 ms, a one-second beat still
lasts about a second. Before the fix it fails.

**Gates.** `pytest` gives 561 passed. Typecheck and build pass. Live, on an isolated copy,
the full narrative at 1x through the interface, with no terminal and no
API call after the page opened:

- the narrative took 268.2 s of its 270, and 4.5 s went on answering:
  the credential at 31 s, the approvals at 199 s, the confirmation at
  258 s, the hand-over at 273 s;
- Life caught up 47.0 s after the hand-over;
- "Rachel.SVC", typed key by key, reached the field and fired nothing;
- the operator panel never showed, and the console stayed clean;
- the full stream scrolled at 17 ms frames, and a reload replayed it in
  1.8 s.

The first rehearsal, before the engine fix, took 297 s and 60 s. The
regressions pass: M19 13 of 13, M20 17 of 17, replay and Reset 5 of 5,
and the M14 walkthrough 31 of 31.

**Check by hand.**

1. Type a username with capitals into the credential form: nothing
   resets.
2. Run once at 1x with a watch: about four and a half minutes from
   Enter to the hand-over, plus the time spent answering.

### Review · the documents checked against the build (2026-10-02)

**Asked for.** Take the project as it stands as final, review the
documents against the code, including the visual style, and bring the
documents to the code wherever they disagree. Edit no code.

**How it was checked.**

- Every module in `backend/app` and `frontend/src` was read against the
  requirements, the rulings and the plan.
- `pytest` gives 561 passed, as M22 recorded.
- The generators were run to confirm the figures the documents quote:
  184,392 tickets, 1,842 anomalous, 31 clusters; 13,620 seats; 186
  applications.
- A full run was driven in process and over HTTP: 140 events by the
  time Life is caught up, 34 of them policy decisions (32 ALLOW, 1 DENY,
  1 ESCALATE), and five requests to a person (one credential, three
  approval prompts and one confirmation).
- The app was run and captured at 1600 × 1000 in both themes: the seed
  screen, the credential pause, the approval, the confirmation, the Life
  pane and the Ticket Intelligence dashboard.

**What the code and the documents disagreed on.** None of it is a
defect in the narrative, the figures or the rules. All of it is accepted
as built, and recorded in `decisions.md` §8:

- the as-built chart inventory differs from OQ-1's wording in a few
  places (§4, "As built");
- R-8's credential validation was never built;
- an escalated request waters the tree, and a page load can play one
  watering pulse (A-16, measured over the DevTools protocol: one pulse
  about 1.5 s after load);
- the plan's architecture sketch predated the build (rewritten);
- §83 above predates the requirements (annotated);
- two rulings had been made in commits without a record: `run.ps1`
  (D-21) and the name Seed v0.1 (D-22).

One visual limit, accepted: in the Both layout at 1600 × 1000, the
approval surface pushes the cards' Review and Approve buttons below the
fold. The stage scrolls to them.

**Stale comments left in the code** are listed in `decisions.md` §8.2.

**Files.** `docs/requirements.md`, `docs/decisions.md`,
`docs/implementation-plan.md`, this file; new: `docs/README.md`,
`docs/architecture.md`, `docs/design-system.md`,
`docs/operator-guide.md`. No code changed.
