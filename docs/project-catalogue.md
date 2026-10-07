# Damien — Project Catalogue

Reviewed: **6 October 2026**. **16 projects** across real-world/client work, academic assignments and personal projects.

This is a source-grounded working catalogue for portfolio writing. GitHub repositories were inspected using `gh`, including source, documentation, dependencies, test files and relevant branches. The portfolio was reviewed from the current local workspace because its GitHub repository is empty. Repository inspection is not a fresh build, test run or production-site audit.

**Evidence conventions**

- **Confirmed role:** supplied directly by Damien. Repository ownership or commit authorship alone is not treated as proof of complete authorship.
- **Implemented/source-backed:** supported by inspected code, configuration or tests. Where only documentation supports a capability, that distinction is stated.
- **Recorded result:** an existing notebook output or report, not a newly reproduced measurement.
- **To confirm:** missing personal context, attribution, delivery status or evidence.
- **Lessons and next steps:** suggested discussion points and improvements; not claims about Damien's personal experience or a committed roadmap.

No measured client-business outcomes were supplied. Deployment configuration demonstrates an operational design, not that a service is currently live. Technical challenges below explain problems the implementation addresses; they are not invented accounts of incidents Damien personally encountered. Some remote trees omit files referenced by their documentation or imports; the relevant limitations are noted below.

## Contents

### Real-world / client projects

1. [Agent Property — Bilingual Property Website and CMS](#1-agent-property--bilingual-property-website-and-cms)
2. [MyReport — WhatsApp Customer Follow-up and Reporting Workspace](#2-myreport--whatsapp-customer-follow-up-and-reporting-workspace)
3. [DWMLight / ANVA CMS — Multilingual Product Website and Custom CMS](#3-dwmlight--anva-cms--multilingual-product-website-and-custom-cms)
4. [AMPLYFII (Ampress) — Influencer Campaign Operations Platform](#4-amplyfii-ampress--influencer-campaign-operations-platform)

### Academic projects

5. [FYP — Hybrid Anomaly Detection for Microservice Observability](#5-fyp--hybrid-anomaly-detection-for-microservice-observability)
6. [Concurrent Programming — Airport Simulation](#6-concurrent-programming--airport-simulation)
7. [Data Structures — E-commerce Analytics and Tournament Management](#7-data-structures--e-commerce-analytics-and-tournament-management)
8. [DTM — Coupon Data Preparation and Exploratory Analysis](#8-dtm--coupon-data-preparation-and-exploratory-analysis)
9. [Java Programming G18 — Service Centre Management](#9-java-programming-g18--service-centre-management)
10. [OODJ — Purchasing and Inventory Management](#10-oodj--purchasing-and-inventory-management)
11. [PFDA — Credit-Risk Data Analysis](#11-pfda--credit-risk-data-analysis)
12. [TXSA — Comparative Text Preprocessing](#12-txsa--comparative-text-preprocessing)
13. [SDM — Recruitment and Employment Workflow Prototype](#13-sdm--recruitment-and-employment-workflow-prototype)
14. [RTS — Ground and Onboard Control Simulation](#14-rts--ground-and-onboard-control-simulation)

### Personal projects

15. [Fedora Dotfiles — Customized Wayland Desktop Environment](#15-fedora-dotfiles--customized-wayland-desktop-environment)
16. [Damien Portfolio — Immersive 3D Portfolio](#16-damien-portfolio--immersive-3d-portfolio)

---

## Real-world / client projects

### 1. Agent Property — Bilingual Property Website and CMS

#### Overview

A bilingual property-discovery website that combines CMS-managed listings, housing-scheme information and educational content with direct WhatsApp enquiries.

Public website: [MyRumawip](https://myrumawip.com/).

#### Problem and purpose

Prospective buyers need understandable property information and a straightforward way to enquire. The operator needs to maintain listings and guides without repeatedly changing application code. The inspected implementation addresses these needs through a public website backed by an editorial CMS.

#### My role and contribution

**Confirmed: sole developer.** Suitable portfolio wording: “I developed the property website, CMS integration and deployment workflow end to end.” The exact delivery period and client-approved project name remain to confirm.

#### Key features

- English and Malay content, with English using unprefixed URLs and Malay using `/ms/`.
- Property detail pages, scheme pages, guides, blog content and grouped FAQs.
- Strapi-managed content, media and SEO fields, including structured-data support.
- Direct WhatsApp enquiry links; configurable analytics for accepted WhatsApp-click events.
- Cached CMS requests, revalidation support and content/media synchronization tooling.

#### Architecture and workflow

`Editors → Strapi 5 → PostgreSQL/media storage → server-side Next.js fetches → public pages → WhatsApp enquiry`

The monorepo separates `frontend/` from `strapi-cms/`. The CMS client is server-only, uses a private token when configured, validates responses with Zod and defaults to a 300-second revalidation interval. Deployment documentation describes a PM2-managed frontend, Docker-hosted CMS/database and Ansible-managed server configuration.

#### Technologies and technical decisions

**Next.js App Router, React, TypeScript, Tailwind CSS v4, Strapi 5, PostgreSQL, Docker Compose, PM2, Ansible and GitHub Actions.** Server-side CMS access keeps privileged tokens out of browser code. Locale-aware caching and a shared content model separate editorial changes from application releases. These are implementation-supported advantages; confirm the original reasons for choosing the stack before writing a personal decision narrative.

#### Technical challenges and solutions

- **Localized routes and content:** locale helpers and separate translation dictionaries coordinate routing with CMS queries.
- **CMS response shape:** the typed client validates data rather than assuming every response is valid.
- **Safe content synchronization:** documented merge tooling preserves destination content rather than replacing the entire production dataset; media identity and nested component population require careful handling.
- **Repeatable operations:** the repository contains CI/deployment scripts and Ansible-managed environment configuration.

#### Results and evidence

The repository contains both application packages, source-backed CMS fetching, content schemas and operational tooling. Documentation records content-sync and deployment considerations. No traffic, lead-conversion, Lighthouse or time-saving result is claimed here without an approved measurement. The public website is MyRumawip, at https://myrumawip.com/.

#### Lessons and next steps

Potential takeaways: multilingual content needs consistent routing, caching and editorial ownership; CMS integration involves more than rendering JSON. Proposed next steps: publish an approved listing/enquiry demo, record SEO/accessibility measurements and document the content-editor workflow with screenshots.

#### Links and source references

- [MyRumawip website](https://myrumawip.com/)
- [Repository](https://github.com/DamienCKj2812/agent-limenghar-property)
- [`frontend/AGENTS.md`](https://github.com/DamienCKj2812/agent-limenghar-property/blob/main/frontend/AGENTS.md) — routes, localization and frontend operations.
- [`frontend/src/lib/strapi/client.ts`](https://github.com/DamienCKj2812/agent-limenghar-property/blob/main/frontend/src/lib/strapi/client.ts) — server-only, validated CMS requests.
- [`strapi-cms/AGENTS.md`](https://github.com/DamienCKj2812/agent-limenghar-property/blob/main/strapi-cms/AGENTS.md) — content types, sync and media behavior.

### 2. MyReport — WhatsApp Customer Follow-up and Reporting Workspace

#### Overview

A customer-management workspace that organizes WhatsApp conversations, confirmed customer requirements, eligibility records and follow-up actions, with human-reviewed AI assistance.

**Access:** Hosted privately via Tailscale; not publicly accessible.

#### Problem and purpose

A large conversation history makes it difficult to remember customer requirements, identify overdue follow-ups and preserve the reasoning behind eligibility assessments. The application organizes work around actionable queues and customer history rather than treating a spreadsheet or chat list as the complete customer record.

#### My role and contribution

**Confirmed: sole developer.** Suitable wording: “I built the customer workspace and its message-ingestion, review and integration workflows.” `MyReport` is the name used by repository documentation; confirm the preferred public name and delivery period.

#### Key features

- Read-only WhatsApp ingestion and history reconciliation through WAHA.
- Owner-scoped contact workspaces with lifecycle, requirements, notes and assessment history.
- AI-proposed updates validated against a structured schema and reviewed before becoming confirmed facts.
- Follow-up/appointment scheduling and Google Calendar integration endpoints.
- Operational reports, inbox updates through Supabase Realtime, and action-oriented queues.

#### Architecture and workflow

`WAHA → authenticated webhook/normalization → Supabase message history → extraction/review → confirmed customer records → follow-ups/calendar/reporting`

Supabase is the canonical store. Documented customer-domain mutations use owner-scoped RPCs that update records and audit history together. The frontend/server workspace is under `app/frontend/`; database configuration and migrations belong to `app/supabase/`. Operational documentation describes a self-hosted stack with PM2, reverse-proxy boundaries and private Tailscale access.

#### Technologies and technical decisions

**Next.js, TypeScript, Supabase/PostgreSQL, RLS and database RPCs, WAHA, Anthropic-assisted extraction, Google Calendar OAuth, PM2 and self-hosted infrastructure.** Immutable messages, proposed AI values and confirmed domain data are deliberately separate. The repository documents an owner-approved extraction-provider setup; describe the replaceable AI boundary rather than exposing account-specific operational details.

#### Technical challenges and solutions

- **Duplicate/unreliable message delivery:** provider-message IDs support idempotency and additive reconciliation.
- **WhatsApp identifiers/history differences:** ingestion documentation explains LID-to-phone resolution, pagination and linked-device history limitations.
- **Untrusted or invalid AI output:** tests exercise schema validation, conflicting ranges, controlled values and prompt construction that retains customer messages as data.
- **Historical integrity:** pinned-note replacement and new eligibility assessments preserve prior records and audit history.

#### Results and evidence

Inspected documentation and tests establish the ingestion, review and customer-workspace contracts; calendar and Sheets integration routes also exist. The tree contains unit/integration-oriented tests and browser workflow tests. Some imported implementation files are absent from the remote snapshot, so it is not independently reproducible from the inspected tree alone. Google Sheets is an optional reporting destination, not the primary database; a complete export workflow was not verified. No adoption or time-saving number is claimed.

#### Lessons and next steps

Potential takeaways: reliable customer automation needs traceable state, idempotent ingestion and an explicit human-review boundary. Proposed next steps: ensure the full implementation is committed, record an approved message-to-follow-up demo and measure overdue-action reduction or review time.

#### Links and source references

- Deployment is private via Tailscale; there is no public website link.
- [Repository](https://github.com/DamienCKj2812/report-automation)
- [`docs/customer-workspace.md`](https://github.com/DamienCKj2812/report-automation/blob/main/docs/customer-workspace.md) — owner-scoped writes, history and Realtime.
- [`docs/waha-ingestion.md`](https://github.com/DamienCKj2812/report-automation/blob/main/docs/waha-ingestion.md) — read-only ingestion, pagination and backfill.
- [`webhook.test.ts`](https://github.com/DamienCKj2812/report-automation/blob/main/app/frontend/src/lib/waha/webhook.test.ts) and [`extraction.test.ts`](https://github.com/DamienCKj2812/report-automation/blob/main/app/frontend/src/lib/ai/extraction.test.ts) — concrete validation cases.

### 3. DWMLight / ANVA CMS — Multilingual Product Website and Custom CMS

#### Overview

A multilingual product and company website backed by a custom content-management API, including localized content, product media and downloadable catalogues.

Public website: [DWMLight](https://dwmlight.com/en).

#### Problem and purpose

A product-oriented business needs to maintain products, categories, case studies, news and localized documents consistently. A custom CMS supplies structured content and administrative permissions, while the public site presents that content in an appropriate language.

#### My role and contribution

**Confirmed: CMS/backend development and deployment/server responsibilities.** Suitable wording: “I developed the CMS/backend supporting DWMLight and handled deployment and server operations.” The frontend is reviewed to explain system integration, not attributed entirely to Damien.

#### Key features

- Schema-driven content collections and components.
- Content creation, updates, ordering and translation handling.
- Tenant/locale modules, user roles and permission checks.
- Media management and public content, email and media endpoints.
- Public product/category pages, case studies, news and language-specific product PDFs in the DWMLight frontend.

#### Architecture and workflow

`CMS users → authenticated Express controllers → injected services → MongoDB/media storage → public API → localized Next.js website`

ANVA CMS organizes features under `src/module/`, with controllers, database models/services and shared context/dependency injection. The inspected content controller obtains validation schemas from the attribute service, checks permissions and combines base content with requested translation fields. The DWMLight frontend repository supplies the consuming website. Some public product code selects language-specific values client-side; avoid describing all localization as server-side CMS negotiation.

#### Technologies and technical decisions

**Backend:** TypeScript, Express, MongoDB, AJV, JWT-related authentication dependencies, Multer/Sharp, Nodemailer and OpenTelemetry. **Frontend context:** Next.js 15, React 19, TypeScript, Tailwind CSS v4 and localization libraries. **Operations:** PM2 deployment instructions and controlled Node memory limits. Schema-driven validation allows content structures to vary without creating a new hard-coded controller for every page.

#### Technical challenges and solutions

- **Flexible yet validated content:** collection-defined schemas feed content validation and service behavior.
- **Localized fields/documents:** content merging and explicit PDF-language fields distinguish shared media structure from translated copy.
- **Administrative access:** content mutations are guarded by authentication and operation-specific permissions.
- **Deployment resources:** package scripts and deployment guidance provide separate builds/processes with explicit memory settings.

#### Results and evidence

Both repositories contain source-backed CMS/public-site integration. Backend modules cover content, attributes, translations, tenants, media and user administration. The frontend includes product filtering and catalogue/PDF support. No customer count, business uplift, deployment uptime or frontend authorship is inferred. The real-world project name is confirmed as DWMLight, with public website https://dwmlight.com/en.

#### Lessons and next steps

Potential takeaways: a reusable CMS needs clear validation, permissions and translation boundaries. Proposed next steps: demonstrate a content update from admin to public page, document the API contract and add evidence of backup/recovery and deployment reliability. ANVA CMS is also the observed application in the FYP; the two catalogue entries describe different purposes, not two independent implementations of the CMS.

#### Links and source references

- [DWMLight website](https://dwmlight.com/en)
- [DWMLight website repository](https://github.com/maxscale-io/Aria) and [ANVA CMS repository](https://github.com/maxscale-io/anva-cms).
- [`content/controller.ts`](https://github.com/maxscale-io/anva-cms/blob/main/src/module/content/controller.ts) — permission-checked, schema-driven content operations.
- [`routes.public.ts`](https://github.com/maxscale-io/anva-cms/blob/main/src/middleware/routes.public.ts) and [`package.json`](https://github.com/maxscale-io/anva-cms/blob/main/package.json).
- [Localized product PDFs](https://github.com/maxscale-io/Aria/blob/main/docs/CMS_LOCALIZED_PRODUCT_PDFS.md) and [product API adapter](https://github.com/maxscale-io/Aria/blob/main/src/api/Product/api.ts).

### 4. AMPLYFII (Ampress) — Influencer Campaign Operations Platform

#### Overview

An influencer-marketing platform that helps teams manage creator partnerships and campaigns.

**Status: Unreleased.** [Preview login](https://amplyfii.io/login?redirect=%2F) is provided as an unreleased preview, not a launched public product.

#### Problem and purpose

Help teams organise influencer-marketing work and coordinate creator partnerships in one place.

#### My role and contribution

Contributing to product development and collaborating with another developer to support the overall user experience.

#### Project status

Currently in development and unreleased. This portfolio shares only the product's general purpose and my broad contribution; further details are confidential under an NDA.

#### Links and source references

- [AMPLYFII (Ampress) preview login — unreleased](https://amplyfii.io/login?redirect=%2F)

---

## Academic projects

### 5. FYP — Hybrid Anomaly Detection for Microservice Observability

#### Overview

A telemetry-based anomaly-detection system that combines OpenTelemetry ingestion, Redis streaming, machine-learning inference and a live observability dashboard, evaluated using telemetry from an instrumented CMS application.

#### Problem and purpose

Static monitoring thresholds can miss complex behavior or produce noisy alerts when system conditions vary. This FYP investigates whether supervised and unsupervised detectors can be combined to detect multivariate anomalies while retaining low false-positive rates and useful explanations of unusual metrics.

The project spans three repositories: `logging-microservice` is the backend/ML core, `logging-microservice-ui` is the dashboard, and `logging-loading` generates load and injected faults. ANVA CMS supplies the observed application; it is supporting context, not a fourth independent FYP project.

#### My role and contribution

**FYP ownership is confirmed as a portfolio project; exact personal implementation responsibilities remain to confirm.** Do not yet claim sole authorship of every service or model. Damien confirmed that **XGBoost + LOF is the current live model** and approved using the committed notebook's offline results with their evaluation context.

Suggested attribution to finalize: “For my FYP, I [designed/built/evaluated — confirm scope] an end-to-end hybrid anomaly-detection system for instrumented application telemetry.”

#### Key features

- OTLP metrics and traces collection through a Go backend and OpenTelemetry Collector.
- Redis Streams for decoupled telemetry/inference/event processing and PostgreSQL persistence when enabled.
- Supervised, unsupervised, hybrid and static-threshold model comparisons.
- Live metrics/history display, anomaly APIs and WebSocket integration.
- Metric attribution using baseline deviation, plus controlled load and chaos scenarios.

The receiver supports **metrics and traces**, not an implemented OTLP logs ingestion service. “Logging” in the repository names should not become a claim of complete log/metric/trace support.

#### Architecture and workflow

```text
logging-loading (Locust + fault/pressure scenarios)
        │ drives workload and injected faults
        ▼
ANVA CMS ── OTLP telemetry ──► OpenTelemetry Collector
                                      │
                                      ▼
                            Go telemetry receiver
                                      │
                                 Redis Streams
                              ┌───────┴────────┐
                              ▼                ▼
                     Persistence workers   Python ML inference
                              │                │
                              ▼                ▼
                          PostgreSQL     anomalies_stream
                              └───────┬────────┘
                                      ▼
                              REST/WebSocket API
                                      ▼
                          React observability dashboard
```

`cmd/backend` and `cmd/api` are separate Go entrypoints. Telemetry is prepared as aligned **10-second multivariate buckets**. The inspected dashboard hook seeds chart state from historical REST results, then applies incremental WebSocket updates. It bounds chart groups, series and point histories to avoid unbounded rendering.

Runtime documentation separates live and training databases. **Metric/trace DB insertion defaults to disabled**, so collecting training data requires the appropriate database mode and insertion configuration; the existence of a database does not imply all live telemetry is being persisted. PostgreSQL is an external requirement in the documented Compose topology.

#### Technologies and technical decisions

**Go, gRPC/OTLP, OpenTelemetry Collector, Redis Streams, PostgreSQL, Python, scikit-learn, PyOD, XGBoost, Jupyter, React 19, TypeScript, TanStack Start/Router/Query, Tailwind CSS v4, Orval, Locust, Toxiproxy and Docker Compose.**

- Separate ingestion and background processing prevents database/model work from becoming the receiver's entire synchronous responsibility.
- Unsupervised adapters expose consistent scoring/prediction interfaces; Isolation Forest/LOF scores are oriented so larger values mean more anomalous.
- Novelty-mode LOF supports scoring previously unseen samples.
- Live/history chart composition provides context beyond only the latest event.
- Model selection considers recall, precision, F1, ROC-AUC, false positives and latency rather than accuracy alone.

These are supported design characteristics. The complete model-selection and fusion implementation is not all present in the remote tree; do not infer undocumented threshold formulas.

#### Technical challenges and solutions

1. **No naturally complete ground truth:** recorded evaluation injects synthetic spikes, drifts and dropouts into real collected telemetry to create labels. This permits comparison but does not establish accuracy on independently labelled real incidents.
2. **Different detector score conventions:** inspected model adapters normalize score orientation and expose a common interface.
3. **Cumulative counters and differently sampled data:** notebook/runtime documentation describes aligned buckets and delta-derived features; the dashboard handles monotonic counters explicitly.
4. **Alert usefulness:** anomaly handlers serve history, summaries and top drivers; documented attribution compares metrics with learned baseline statistics. Attribution is a deviation explanation, not proven causal root-cause analysis.
5. **Repeatable anomalous workloads:** Locust's diurnal baseline can be overridden by traffic/authentication spikes; chaos tooling also provides network and resource-pressure scenarios.

#### Results and evidence

**Recorded offline notebook run — not rerun during this catalogue review:**

| Item | Recorded value |
|---|---:|
| Prepared 10-second samples | 3,260 |
| Features | 32 |
| Training samples | 2,282 |
| Test samples | 978 |
| Injected anomalous rows across the full dataset | 394 |
| Recommended model | XGBoost + LOF hybrid |
| Precision | 0.9221 (92.21%) |
| Recall | 0.7717 (77.17%) |
| F1 | 0.8402 |
| False-positive rate | 0.0068 (0.68%) |
| ROC-AUC | 0.9012 |
| Mean inference latency | 13.7249 ms |
| Weighted deployment score | 0.8588 |

The notebook ranks candidates with **35% F1 + 25% recall + 20% ROC-AUC + 10% precision + 10% (1 − FPR)**. Recorded latency is reviewed separately against the 10-second interval. This weighting is a project-defined selection rule, not an external industry standard.

Safe portfolio wording: “In a recorded offline evaluation on real telemetry with injected anomaly labels, the XGBoost–LOF hybrid achieved an F1 score of 0.8402 and a 0.68% false-positive rate.” Damien confirms that the same model combination is used live; the recorded offline scores should not be described as live production performance.

The notebook's introductory text still mentions a Random Forest/Isolation Forest hybrid, but its ranked outputs and current backend guidance identify XGBoost/LOF. Use the current evidence rather than copying the stale introduction. Several referenced training, evaluation and hybrid-runtime files are missing from the remote snapshot, so the complete experiment cannot be reproduced from that snapshot alone.

#### Lessons and next steps

Potential takeaways: an observability ML system requires data engineering, controlled experiments, deployment configuration and useful interfaces as well as a detector. A high ROC-AUC does not automatically imply a good operating threshold.

Proposed next steps: commit the complete pipeline; reproduce the notebook with saved configuration and data provenance; validate chronological/episode-disjoint splits; evaluate separately labelled fault episodes; investigate constant/zero-valued features; report latency percentiles and hardware; document threshold/fusion settings and artifact versions. Confirm which of these are already in the final submission.

#### Links and source references

- [Backend and ML](https://github.com/DamienCKj2812/logging-microservice), [dashboard](https://github.com/DamienCKj2812/logging-microservice-ui), [load/chaos tooling](https://github.com/DamienCKj2812/logging-loading).
- [Observed ANVA CMS](https://github.com/maxscale-io/anva-cms).
- [Offline evaluation notebook](https://github.com/DamienCKj2812/logging-microservice/blob/main/ml/notebooks/offline_model_evaluation.ipynb) — dataset, model rankings and stored metrics.
- [Backend guidance](https://github.com/DamienCKj2812/logging-microservice/blob/main/AGENTS.md), [detector adapters](https://github.com/DamienCKj2812/logging-microservice/blob/main/ml/models/unsupervised.py), [anomaly handlers](https://github.com/DamienCKj2812/logging-microservice/blob/main/backend/internal/api/anomalies/handler.go).
- [Dashboard metrics hook](https://github.com/DamienCKj2812/logging-microservice-ui/blob/main/src/hooks/use-metrics.ts) and [Locust load shape](https://github.com/DamienCKj2812/logging-loading/blob/main/locustfile.py).

### 6. Concurrent Programming — Airport Simulation

#### Overview

A Java airport simulation modeling aircraft activity and access to shared runway, gate and refueling resources.

#### Problem and purpose

Concurrent aircraft must coordinate limited resources without treating every operation as an unrelated sequential action. The assignment demonstrates threads, resource admission and synchronization in a recognizable operational scenario.

#### My role and contribution

**To confirm:** whether this was individual or group work, and which simulation/controller components Damien implemented.

#### Key features

- A `Plane` thread for each simulated aircraft.
- A single-permit runway semaphore and three-permit ground-admission semaphore.
- Gate assignment protected by a lock and a concurrent plane-to-gate map.
- Emergency-specific landing logic and a shared refueling component.
- Statistics for served aircraft, passenger counts and waiting times.

#### Architecture and workflow

`Main → Plane threads → AirTrafficController → shared gates/runway/refueling → completion statistics`

Aircraft request admission, perform simulated landing/service/refueling and depart. The controller maintains shared state rather than embedding gate allocation separately in each aircraft.

#### Technologies and technical decisions

**Java, Maven, threads, Semaphore, synchronized collections/blocks and ConcurrentHashMap.** Semaphores represent capacity; a guarded queue represents individual gate identities. This demonstrates different synchronization responsibilities rather than using a single collection for everything.

#### Technical challenges and solutions

The source addresses shared-capacity admission, exclusive resource use and gate-state updates. However, the inspected aircraft lifecycle releases the runway only after servicing and departure, potentially serializing more work than a realistic airport model. Emergency behavior is implemented, but fair priority, deadlock freedom and interrupt-safe cleanup were not verified.

#### Results and evidence

The source includes a runnable-style simulation entrypoint and a statistics function. No fresh simulation run, throughput benchmark or proof of concurrency correctness was performed. Treat the printed statistics as capabilities, not measured results.

#### Lessons and next steps

Potential takeaways: protecting individual fields is not enough; acquisition order and resource lifetime determine overall behavior. Proposed next steps: separate runway ownership for landing/takeoff, test emergency and interrupted paths, and verify final resource permits under repeated runs.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/ConcurrentProgrammingAssignment).
- [`AirTrafficController.java`](https://github.com/DamienCKj2812/ConcurrentProgrammingAssignment/blob/main/src/main/java/com/example/ccpassignment/AirTrafficController.java) and [`Plane.java`](https://github.com/DamienCKj2812/ConcurrentProgrammingAssignment/blob/main/src/main/java/com/example/ccpassignment/Plane.java).

### 7. Data Structures — E-commerce Analytics and Tournament Management

#### Overview

A two-part C++ assignment applying custom data structures to transaction/review analysis and tournament, spectator and result-management simulations.

#### Problem and purpose

The assignment explores how data representation and algorithm choice affect searching, sorting, prioritization and resource allocation. The two repositories are presented together as requested, but they are separate executables and application domains—not one integrated deployed system.

#### My role and contribution

**To confirm:** Damien's tasks in each part, team size and which structures/algorithms were personally implemented.

#### Key features

- Part 1: CSV-backed transactions and reviews, custom arrays and doubly linked lists.
- Searching alternatives including exponential/Fibonacci and linked-list-oriented approaches.
- Merge/quick sorting helpers and elapsed-time/memory instrumentation.
- Part 2: team registration/check-in, replacements and multi-stage match scheduling.
- Priority-based spectator seating, overflow/stream-slot queues and game-history logging.

#### Architecture and workflow

`Part 1: CSV → domain records → custom structures → sort/search/analysis → console output`

`Part 2: teams → registration/check-in → match stages → winners/history; spectators → priority seating → overflow/stream allocation`

The active Part 1 entrypoint demonstrates merge sorting transactions and quick sorting reviews. Other experimental paths are present in helpers or commented out. Part 2 provides separate menu paths for tournament management, spectator queues and result history.

#### Technologies and technical decisions

**C++, templates, pointer-based linked lists, custom dynamic arrays, priority/circular queues, stacks, CSV and `std::chrono`.** The implementation exposes algorithm mechanics directly rather than hiding all operations behind standard containers. Comparator helpers support multiple record fields.

#### Technical challenges and solutions

The code deals with maintaining linked-list relationships during sorting, preserving team references through match stages and handling bounded seating/stream capacity. Timing and memory output make trade-offs observable. Instrumentation alone does not establish that one algorithm wins under all data distributions.

#### Results and evidence

Both repositories contain concrete structures and application demonstrations. Part 2's sample setup creates 24 teams and exercises spectator allocation. These are demonstration inputs, not user/adoption numbers. No reproducible benchmark comparison or final assignment grade was supplied.

#### Lessons and next steps

Potential takeaways: algorithm complexity, ownership and domain rules interact. Proposed next steps: benchmark consistent datasets/distributions, cover empty/single-element structures and bracket edge cases, and replace hard-coded demonstration inputs with reusable scenarios.

#### Links and source references

- [Part 1](https://github.com/DamienCKj2812/DSTRAssignment) and [Part 2](https://github.com/DamienCKj2812/DSTRAssignmentPart2).
- [Part 1 entrypoint](https://github.com/DamienCKj2812/DSTRAssignment/blob/main/DSTRAssignment/main.cpp), [search helpers](https://github.com/DamienCKj2812/DSTRAssignment/blob/main/DSTRAssignment/ArraySearch.hpp), [list sorting](https://github.com/DamienCKj2812/DSTRAssignment/blob/main/DSTRAssignment/DoublyLinkedListSort.hpp).
- [Part 2 entrypoint](https://github.com/DamienCKj2812/DSTRAssignmentPart2/blob/main/DSTRAssignmentPart2/Main.cpp).

### 8. DTM — Coupon Data Preparation and Exploratory Analysis

#### Overview

An R data-preparation study that introduces controlled data-quality problems into an in-vehicle coupon dataset, cleans it and compares exploratory views before and after preprocessing.

#### Problem and purpose

Missing values, outliers and inconsistent categories can obscure analysis. This assignment makes those problems explicit and examines preprocessing methods rather than presenting an already-clean CSV as sufficient analytical work.

#### My role and contribution

**To confirm:** Damien's preprocessing/EDA responsibilities, group context and the official expansion/title of the DTM module.

#### Key features

- Seeded generation of missing values and temperature outliers.
- Controlled category inconsistencies in fields such as weather, time and education.
- Empty-value normalization and numerical/categorical preprocessing helpers.
- MICE-based categorical imputation using polynomial regression.
- Before/after frequency summaries and plots, plus cleaned CSV output.

#### Architecture and workflow

`Original coupon CSV → controlled corruption → uncleaned CSV → preprocessing → cleaned CSV → before/after EDA`

The repository separates corruption generation, preprocessing and exploratory scripts into recognizable stages, with CSV files carrying intermediate datasets.

#### Technologies and technical decisions

**R, RStudio project configuration, dplyr, mice and ggplot2.** Fixed seeds make selected corruption steps repeatable. Multiple-imputation tooling is used for categorical fields, but the inspected preprocessing selects a single completed dataset; do not describe the analysis as pooling multiple-imputation uncertainty.

#### Technical challenges and solutions

The code addresses blank values, inconsistent types and missing categorical values through helpers and transformations. The generated corruption is an experiment under controlled conditions, not a claim about naturally occurring production data. The exact categorical normalization path should be demonstrated in a reproducible run.

#### Results and evidence

Source scripts and original/uncleaned/cleaned datasets are present. EDA summarizes the coupon and contextual variables. No prediction accuracy, statistical improvement or verified end-to-end execution is claimed; the inspected scripts also contain stray expressions requiring cleanup before reproducibility is assumed.

#### Lessons and next steps

Potential takeaways: dataset quality and category semantics should be checked before drawing conclusions. Proposed next steps: make preprocessing a clean reproducible pipeline, record missing-value counts and distributions before/after, and keep outcome-label imputation separate from any future predictive evaluation.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/DTMAssignment).
- [Corruption generation](https://github.com/DamienCKj2812/DTMAssignment/blob/main/unclean_data_process.R), [preprocessing](https://github.com/DamienCKj2812/DTMAssignment/blob/main/PreProcessing/main.R), [post-cleaning EDA](https://github.com/DamienCKj2812/DTMAssignment/blob/main/EDAAfterDataPreprocessing/main.R).

### 9. Java Programming G18 — Service Centre Management

#### Overview

A Java desktop service-centre application for registering service jobs, assigning technicians, tracking appointments, payments and feedback.

#### Problem and purpose

Managers and technicians need consistent job records and clear responsibilities across scheduling, service completion and payment. The inspected domain uses hostel/customer and machine details; the official business scenario should be confirmed before choosing a more specific public title.

#### My role and contribution

**To confirm:** whether Damien implemented the manager, technician, authentication, persistence or UI components, and how work was divided in G18.

#### Key features

- Role-specific authentication and manager/technician desktop screens.
- Service-job registration with appointment dates and duplicate-order checks.
- Technician assignment and technician-specific appointment lists.
- Job completion, payment status and feedback handling.
- Monthly paid/unpaid summaries and file-backed records.

#### Architecture and workflow

`Login/role UI → CentreManager/Technician logic → in-memory job records → local text-file persistence`

`CentreManager` loads and maintains job details; `Technician` extends it for technician workflows. Feedback is accepted only when the job is completed and paid.

#### Technologies and technical decisions

**Java, Swing/NetBeans desktop forms, file I/O, collections, inheritance and `LocalDate`.** File storage keeps the assignment self-contained without a database server. Separate classes expose domain operations, although inheritance also shares persistence responsibilities.

#### Technical challenges and solutions

The implementation coordinates job/payment status, appointment parsing and role-specific filtering. Date validation and explicit completion/payment checks enforce parts of the workflow. Rewriting text files is simple for an assignment but does not establish transactional safety for concurrent users.

#### Results and evidence

Source-backed manager/technician workflows and persistence handlers are available. This is a desktop academic application, not a verified commercial deployment. No grade, user study or execution evidence was supplied.

#### Lessons and next steps

Potential takeaways: UI actions should map to explicit business transitions and validated data. Proposed next steps: introduce typed job records, separate storage from inheritance and test duplicate registration, technician assignment and completion/payment/feedback transitions.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/Java-Programming-G18-).
- [`CentreManager.java`](https://github.com/DamienCKj2812/Java-Programming-G18-/blob/main/src/main/CentreManager.java) and [`Technician.java`](https://github.com/DamienCKj2812/Java-Programming-G18-/blob/main/src/main/Technician.java).

### 10. OODJ — Purchasing and Inventory Management

#### Overview

A role-based Java desktop purchasing/inventory application covering item records, stock visibility, purchase orders, payment recording and administrative activity.

#### Problem and purpose

A purchasing workflow spans different users and record types. This assignment explores object-oriented modeling and role-specific screens for inventory, sales, purchasing, finance and administration.

#### My role and contribution

**To confirm:** Damien's assigned roles/modules and the team contribution split. Repository ownership does not establish authorship of all five role interfaces.

#### Key features

- Login and role-specific desktop navigation.
- Inventory item creation, updates and deletion, including quantities/reorder information.
- Sales/stock screens and purchase-manager order screens.
- Finance screens for approved orders and payment records.
- User administration and activity-log management.

#### Architecture and workflow

`Swing role screens → domain models → FileManager/local files → refreshed tables and activity logs`

The inspected finance screen retrieves an approved order, calculates quantity × item price, records payment and changes the order status. This is internal payment bookkeeping, not an integrated online payment gateway.

#### Technologies and technical decisions

**Java, Swing, NetBeans forms, object-oriented domain models, collections and delimited text-file persistence.** `Inventory` centralizes record transformations rather than making every screen parse storage independently. Files avoid a database dependency for the academic demonstration.

#### Technical challenges and solutions

The source handles record lookup, duplicate item names, table filtering and cross-record payment calculation. Role-specific UIs model responsibilities. Client-side role navigation alone should not be described as independently audited security, and multi-file updates are not automatically transactional.

#### Results and evidence

The repository includes role interfaces and concrete inventory/payment code. No real purchasing volume or financial processing claim is made. End-to-end execution, assignment outcomes and Damien's module ownership remain unconfirmed.

#### Lessons and next steps

Potential takeaways: domain logic and persistence benefit from separation from generated UI code. Proposed next steps: test order/payment invariants, introduce typed monetary fields and a transaction-capable database, and document role permissions independently of screen visibility.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/OODJ).
- [`Inventory.java`](https://github.com/DamienCKj2812/OODJ/blob/main/JavaApplication7/src/models/Inventory.java) and [`MakePaymentFM.java`](https://github.com/DamienCKj2812/OODJ/blob/main/JavaApplication7/src/UI/FinanceManager/MakePaymentFM.java).

### 11. PFDA — Credit-Risk Data Analysis

#### Overview

An R-based group study of credit-risk data, combining cleaning, exploratory analysis, statistical tests and predictive experiments.

#### Problem and purpose

Missing or inconsistent financial/categorical fields complicate the interpretation of credit classifications. The assignment explores relationships between factors such as savings, property, checking status and installment commitments and the dataset's credit labels.

#### My role and contribution

**To confirm:** Damien's preprocessing and analysis contribution. A `kahjun/` folder contains savings/property questions and modeling work; that naming is supporting attribution evidence, not a substitute for Damien confirming the actual scope.

#### Key features

- Missing-value inspection and cleaning/imputation helpers.
- Mean/median/mode, MICE, nearest-neighbor and hot-deck approaches in the scripts.
- Savings-status and property-magnitude analysis.
- Random Forest and logistic-regression experiments with confusion-matrix/accuracy code.
- Additional group analysis using plots, chi-square tests and a t-test.

#### Architecture and workflow

`Credit-risk CSV → shared cleaning → cleaned dataset → member-specific questions → plots/tests/models → interpretation`

The project separates shared cleaning from `kahjun/`, `siaufung/`, `xiehang/` and `zixuan/` analytical work. The inspected `kahjun/main.R` uses a seeded 80/20 split for a Random Forest experiment; other scripts differ in split/model setup.

#### Technologies and technical decisions

**R, dplyr/tidyr, mice, caret, VIM/RANN, ggplot2, randomForest and statistical modeling functions.** Separate question scripts make the analytical argument visible. Library installation commands or imports are not evidence that every referenced model is actually used in the submitted analysis.

#### Technical challenges and solutions

The scripts handle categorical values, missingness and relationships among explanatory variables. Model experiments provide evaluation code rather than relying only on visual associations. Imputation/splitting choices require review: cleaning that uses the outcome label or fits before splitting can compromise future predictive claims.

#### Results and evidence

Source and a cleaned CSV are present; inspected scripts calculate confusion matrices, accuracy, AIC and statistical tests. Final numeric outputs were not verified, so none are invented. This is academic credit-data analysis, not a validated lending decision system.

#### Lessons and next steps

Potential takeaways: distinguish association, predictive performance and business decisions. Proposed next steps: consolidate the scripts into a reproducible report, fit preprocessing on training data only, verify factor/target encoding and include precision/recall or class-balanced metrics.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/PFDAGroupAssignment).
- [Cleaning](https://github.com/DamienCKj2812/PFDAGroupAssignment/blob/main/data_cleaning/main.R), [Kah Jun analysis](https://github.com/DamienCKj2812/PFDAGroupAssignment/blob/main/kahjun/main.R), [group statistical analysis](https://github.com/DamienCKj2812/PFDAGroupAssignment/blob/main/xiehang/main.R).

### 12. TXSA — Comparative Text Preprocessing

#### Overview

A notebook-based text-analytics assignment comparing tokenization approaches and demonstrating stop-word/punctuation filtering on a supplied text corpus.

#### Problem and purpose

Tokenization changes the representation used by later analysis. The assignment compares approaches explicitly instead of assuming that whitespace splitting, regex tokenization and NLP libraries produce interchangeable outputs.

#### My role and contribution

**To confirm:** full individual/group responsibility. The q5 notebook is explicitly labelled with Chong Kah Jun's name/student identifier and presents a TextBlob alternative. That is strong source attribution for the individual notebook, while Damien requested other academic roles remain pending confirmation.

#### Key features

- Comparison of Python `split()`, regex `\w+` and NLTK `word_tokenize`.
- Identification and removal of English stop words and punctuation.
- TextBlob word extraction as an alternative approach.
- Written comparison of output behavior, API style and suitability.

#### Architecture and workflow

`Provided text file → tokenizer variants → inspected token lists → filtering → comparative discussion`

The inspected work is in `part-a/q1.ipynb` and `part-a/q5.ipynb`. The requested Part 2 repository is empty and was omitted with Damien's approval; no Part 2 features are inferred.

#### Technologies and technical decisions

**Python, Jupyter, NLTK, TextBlob, regex and standard string utilities.** Keeping alternative approaches together makes punctuation retention and token boundaries directly comparable. TextBlob is an abstraction over NLP tooling, not an independently designed tokenizer.

#### Technical challenges and solutions

The notebooks demonstrate that whitespace tokens retain attached punctuation, while regex and library methods differ in boundaries and punctuation handling. They explain the trade-off between convenient word extraction and retaining syntax. Exact tokenizer internals depend on the installed library/version, so the notebook's implementation descriptions should not be generalized without checking.

#### Results and evidence

Concrete notebook code and written comparisons are available. The verified scope is preprocessing, not a complete sentiment classifier, topic model or search engine. No accuracy/latency result is claimed.

#### Lessons and next steps

Potential takeaways: preprocessing should match the downstream task; removing punctuation can remove useful information. Proposed next steps: add multilingual/contraction/URL cases, pin tokenizer resources and compare effects on a defined downstream analysis.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/txsa-group-assignment).
- [Group preprocessing notebook](https://github.com/DamienCKj2812/txsa-group-assignment/blob/main/part-a/q1.ipynb) and [individual alternative notebook](https://github.com/DamienCKj2812/txsa-group-assignment/blob/main/part-a/q5.ipynb).

### 13. SDM — Recruitment and Employment Workflow Prototype

#### Overview

A multi-role React frontend prototype for recruitment and employment workflows, including applicant, employer, staff and manager experiences.

#### Problem and purpose

Recruitment processes involve different information and actions for each user type. The assignment models role-based navigation and screens for job discovery, applicant/employer management, contracts, meetings and operational reporting.

#### My role and contribution

**To confirm:** Damien's design/development responsibilities, assigned role screens and group contribution split.

#### Key features

- Role-aware navigation for applicants, employers, staff and managers.
- Job-search/company-detail and applicant-profile screens.
- Employer and internal dashboards/reporting views.
- Contract-status/detail and contract-upload UI.
- Shared route categories for meetings, contracts and payments.

#### Architecture and workflow

`Local user fixtures/Recoil state → role-derived React Router routes → role screens → local demonstration data`

`App.jsx` derives roles from local user lists and uses them to choose visible routes. Contract records come from static TypeScript fixtures. The inspected create-contract screen opens a file input and displays a send button; it does not establish a real submission/delivery service.

#### Technologies and technical decisions

**React 18, Vite, JavaScript/TypeScript components, React Router, Recoil, Radix UI, GSAP, ECharts and calendar UI dependencies.** Lazy-loading helpers separate screen loading. Although a generative-AI SDK appears in dependencies, dependency presence alone does not verify a working AI feature.

#### Technical challenges and solutions

The prototype addresses multiple-role navigation and reuse of shared workflow screens. Route selection makes the academic user journeys demonstrable. Fixture-backed login and client-side route gating are prototype mechanisms, not a production authentication/authorization service.

#### Results and evidence

Source-backed role routing, dashboards and contract fixture/UI behavior are present. The reviewed scope is a frontend workflow prototype; persisted recruitment operations, real payment processing and contract delivery were not established. No usability study or final grade was supplied.

#### Lessons and next steps

Potential takeaways: a convincing interface and a complete backend workflow are different milestones. Proposed next steps: define the API/domain model, implement server-side identity/permissions and persistent records, then validate each role's end-to-end journey.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/SDMGroupAssignment).
- [`App.jsx`](https://github.com/DamienCKj2812/SDMGroupAssignment/blob/main/src/App.jsx), [contract fixtures](https://github.com/DamienCKj2812/SDMGroupAssignment/blob/main/src/_common/data/contract-data.ts), [contract screen](https://github.com/DamienCKj2812/SDMGroupAssignment/blob/main/src/pages/company/contract/create-contract/view/index.tsx).

### 14. RTS — Ground and Onboard Control Simulation

#### Overview

A Rust real-time-systems assignment modeling communication between a Ground Control Station (GCS) and an Onboard Control System (OCS), with timed commands, telemetry and fault handling.

#### Problem and purpose

Control systems need to dispatch commands, interpret telemetry and react to faults within timing constraints. The project explores command scheduling, shared state, communication protocols and instrumentation in a simulated control environment.

#### My role and contribution

**Confirmed: Damien contributed the GCS.** The component expansions were confirmed in the clarification. Suitable wording: “I developed the Ground Control Station side, including [confirm personally owned components] for command scheduling, telemetry handling and control-state checks.” OCS work is described only as integration context. The official assignment title remains to confirm.

#### Key features

- Scheduled GCS commands for Normal/Degraded mode changes and Ping.
- TCP packet transmission with sequence IDs and timestamped command logging.
- Telemetry decoding for gyro, battery and thermal messages.
- GCS checks before issuing Normal-mode commands, including overheating/state conditions.
- OCS command decoding/response construction, atomic state and thermal-fault/priority experiments.

#### Architecture and workflow

`GCS schedule/state checks → TCP command packets → OCS validation/control state → telemetry/responses → GCS decoding/logs`

The meaningful source is split across **`gcs-branch` and `ocs-branch`**. `main` contains only the short README and a design diagram. GCS code maintains scheduled commands in a deque; OCS code provides shared atomic state and command protocol structures.

#### Technologies and technical decisions

**Rust 2024, Cargo, TCP, `Instant`/`Duration`, atomics, Arc/Mutex, serde/serde_json, CSV logging and thread-priority experiments.** Fixed-layout typed packets make communication explicit. Monotonic scheduling time is distinct from logged wall-clock timestamps.

#### Technical challenges and solutions

- **Timing visibility:** GCS measures dispatch lateness and logs on-time/missed-deadline status.
- **Unsafe transitions:** command validation checks mode/temperature/overheating before permitting a Normal transition.
- **Protocol boundaries:** telemetry decoders reject empty, incorrectly sized or unknown payloads.
- **Fault experiments:** OCS code injects thermal-sensor unavailability and records fault events; thread-priority experiments compare worker activity.

#### Results and evidence

Both branches contain concrete source, and the GCS branch includes command/performance/telemetry log artifacts. Those artifacts were not used to claim a verified timing guarantee. Some scheduled examples use zero-millisecond deadlines, and referenced entrypoint/helper modules are missing from the inspected branch trees; a complete build and timing experiment was not reproduced. General-purpose OS thread priority is not proof of hard real-time behavior.

#### Lessons and next steps

Potential takeaways: real-time evaluation must define deadlines and measure misses, not just show thread activity. Proposed next steps: commit complete buildable branch sources, document a paired GCS/OCS launch, set meaningful deadlines and report latency distributions, misses and fault-recovery evidence.

#### Links and source references

- [Repository](https://github.com/BaconCoding74/rust-gcs-ocs-assignment).
- [GCS commands](https://github.com/BaconCoding74/rust-gcs-ocs-assignment/blob/gcs-branch/src/command.rs), [schedule](https://github.com/BaconCoding74/rust-gcs-ocs-assignment/blob/gcs-branch/src/command_schedule.rs), [telemetry](https://github.com/BaconCoding74/rust-gcs-ocs-assignment/blob/gcs-branch/src/telemetry.rs).
- [OCS protocol](https://github.com/BaconCoding74/rust-gcs-ocs-assignment/blob/ocs-branch/src/protocol/command_packet.rs) and [fault injection](https://github.com/BaconCoding74/rust-gcs-ocs-assignment/blob/ocs-branch/src/thermal_control/fault_injection.rs).

---

## Personal projects

### 15. Fedora Dotfiles — Customized Wayland Desktop Environment

#### Overview

A personalized Fedora desktop/development environment combining KDE Plasma and Hyprland sessions with a custom shell, login appearance, sharing picker and reusable configuration management.

#### Problem and purpose

A consistent workstation requires more than a wallpaper: session startup, displays, credentials, theming and tools must work together. This repository captures the configuration and custom integration code needed to recreate and maintain that environment.

#### My role and contribution

**Personal project.** Present Damien's configuration/integration and custom development work while crediting the upstream tools. The precise authorship boundaries of imported shell/theme components remain to confirm; do not describe KDE, Hyprland or all bundled themes as original implementations.

#### Key features

- GNU Stow-managed user configuration for separate KDE and Hyprland sessions.
- Quickshell/QML shell, theme/wallpaper and lock-related components.
- Pixel Temple SDDM login theme and credential/session guidance.
- A custom native PyQt6 screen/window/region sharing chooser.
- Terminal/editor/browser configuration, desktop utilities and battery-warning lifecycle logic.

#### Architecture and workflow

`Versioned Stow packages → home configuration/session services → KDE or Hyprland → custom shell/tools`

The SDDM theme is installed as a self-contained system copy. The share picker replaces only the chooser UI: the existing desktop portal still controls permissions, restore data and PipeWire sharing. Theme/desktop components cooperate with upstream services rather than replacing the entire Linux graphics stack.

#### Technologies and technical decisions

**Fedora Linux, KDE Plasma, Hyprland/Wayland, GNU Stow, Quickshell/QML, Python/PyQt6, SDDM/KWin, shell scripting and portal/PipeWire integration.** The sharing picker uses asynchronous in-memory previews and protocol-compatible output. The battery controller is independent of UPower so state transitions can be tested without manipulating the actual battery.

#### Technical challenges and solutions

- **Display geometry:** the picker documents fractional scaling, rotation and negative desktop positions.
- **Sharing protocol correctness:** selection records use portal handles and emit only on explicit acceptance.
- **Preview lifecycle:** captures avoid overlap and stop when the chooser closes.
- **Repeated battery alerts:** a latch prevents threshold jitter from repeatedly warning; recovery rearms the state.

#### Results and evidence

Documentation, QML/controller source and focused test instructions are present. The share picker documents a 500 ms preview-refresh cadence; the controller defines 20/10/5% warning levels. These are implementation settings, not measured system-performance improvements. No clean-machine setup or full desktop session was tested during this review.

#### Lessons and next steps

Potential takeaways: polished desktop tools depend on protocols, cleanup and recovery paths as much as appearance. Proposed next steps: publish screenshots/video, record a clean-machine setup and document which components are original versus adapted from upstream configurations.

#### Links and source references

- [Repository](https://github.com/DamienCKj2812/fedora-dotfiles).
- [README](https://github.com/DamienCKj2812/fedora-dotfiles/blob/main/README.md), [share-picker guide](https://github.com/DamienCKj2812/fedora-dotfiles/blob/main/share-picker/README.md), [battery controller](https://github.com/DamienCKj2812/fedora-dotfiles/blob/main/quickshell/.config/quickshell/services/BatteryWarningController.qml).

### 16. Damien Portfolio — Immersive 3D Portfolio

#### Overview

A monochrome interactive portfolio that takes visitors through a city, lobby and elevator into dedicated rooms for identity, skills, projects and experience/education.

#### Problem and purpose

The project presents portfolio information as a navigable spatial experience while keeping content, controls and loading understandable. It combines architectural design, Blender authoring, export tooling and browser interaction rather than displaying a standalone decorative 3D model.

#### My role and contribution

**Personal portfolio project; reviewed from the current local workspace.** Suggested wording: “I developed an immersive portfolio combining Blender-authored spaces with a React/Three.js browser experience.” Confirm the scope of original asset work and acknowledge third-party assets, music or references where relevant.

#### Key features

- Reversible city-to-lobby journey and an interactive elevator connecting four rooms.
- Spatial project displays, profile/contact interactions and skill exhibits.
- Guided room routes, free look, keyboard/touch controls and return transitions.
- Independent visible-area animation clocks with reduced-motion handling.
- Staged loading, Retry/cancel states, package caching, interaction audio and persistent music controls.

#### Architecture and workflow

`Blender-authored masters → Python integration/export → binary geometry/motion/route packages + manifests → React loader → shared React Three Fiber Canvas → room controls`

`App.tsx` lazy-loads `CityWalkthrough` and keeps audio providers/controls around it. Native point vertices and curve centerlines are exported separately from solid triangles; the browser uses manifest offsets/hashes and authored animation/route data. A single demand-rendered Canvas is shared across areas.

#### Technologies and technical decisions

**React 19, TypeScript, Vite, Three.js, React Three Fiber/Drei, Tailwind CSS v4, Blender, Python export/build tooling and TypeScript Node package-verification scripts.** Native point/line export preserves the visual representation an ordinary GLB would not retain. Capped DPR, active-area clocks, demand rendering and staged caching control ongoing browser work. Planar reflections are documented for the lobby, Skills and Projects floors; do not assume every native glass effect is reproduced identically in every browser room.

#### Technical challenges and solutions

- **Coordinate/handoff consistency:** geometry and camera data share Blender-to-browser basis conversion and doorway alignment.
- **Input ownership:** room gestures and guided routes take control during visits/departures rather than competing with the city timeline.
- **Idle cost:** invalidation continues while motion is active and settles when the visible experience is idle.
- **Source/export agreement:** verification checks package bounds, destinations, authored transforms and routes.
- **Visual detail:** architectural rooms, including the black-glass observatory floor and satin-black walls/ceiling, are generated through model-specific workflows.

#### Results and evidence

The local source, authored models, generated packages and architecture documentation establish the implementation. During the preceding observatory update, native geometry/walking checks, room-package verification and source comparison passed. That is focused asset evidence, not a fresh full-site browser/performance audit for this catalogue. GitHub is currently empty, so the repository URL is not yet a usable source/demo link.

#### Lessons and next steps

Potential takeaways: 3D web experiences need explicit loading, input, accessibility and lifecycle design. Proposed next steps: publish the current source/build, replace sample project/timeline content with approved records, record a tour and measure browser performance on desktop/mobile. Complete preloading and video banners are documented as planned rather than shipped features.

#### Links and source references

- [GitHub repository — currently empty](https://github.com/DamienCKj2812/damien-portfolio).
- [Local architecture](architecture.md), [development/deployment](development.md), [roadmap](roadmap.md).
- [Application entry](../src/App.tsx), [dependencies](../package.json), [room destinations](../assets/journey/room-destinations.json), [export workflow](../assets/journey/WORKFLOW.md).

---

## Remaining details to confirm

These questions are retained rather than filled with invented personal claims. They can be answered later without repeating the technical review.

| Project(s) | Missing information |
|---|---|
| All projects | Official title, timeframe, approved screenshots/demo URLs and one personally meaningful lesson. |
| Agent Property / MyReport | Public-facing names, delivery status, client-approved descriptions and production/demo URLs. Sole-developer roles are already confirmed. |
| DWMLight / ANVA CMS | Specific backend modules personally delivered, deployment scope and frontend collaborator attribution. Public project name is DWMLight; the frontend repository remains `Aria`. |
| AMPLYFII (Ampress) | NDA-covered: share only the general product purpose and broad contribution. |
| FYP | Official research title, exact individual implementation scope, final submission/report, experiment environment and whether the recorded notebook run is the final reported evaluation. Current live XGBoost/LOF selection is confirmed. |
| Concurrent Programming | Individual/group context, personally implemented classes and any submitted concurrency validation. |
| DSTR | Contribution split by part/structure, final algorithm comparison tables and assignment outcomes. |
| DTM | Official module title, personal preprocessing/EDA contribution and the final cleaned-data report. |
| Java G18 / OODJ | Personally delivered role modules and the official assignment/business scenario. |
| PFDA | Whether `kahjun/` is the complete personal contribution, cleaning responsibilities and final statistical/model outputs. |
| TXSA | Confirmation of q5 authorship and other group contributions. The empty Part 2 repository is intentionally omitted. |
| SDM | Personal screens/features, official project name and whether any backend existed outside this repository. |
| RTS | Official project title, exact GCS components personally implemented and final timing/fault experiment results. GCS ownership is confirmed. |
| Fedora Dotfiles | Original/adapted component attribution, screenshots and clean-machine setup evidence. |
| Portfolio | Asset attribution, current deployment URL and measured browser performance. |

## Reviewed source revisions

The following commit IDs were recorded during review. Main-text links use readable branch paths; these IDs identify the source snapshots for subsequent verification. Source files inspected earlier in the review were fetched from the then-current branch heads; a moving remote branch may need a comparison before reusing numerical results.

| Repository | Ref | Commit recorded |
|---|---|---|
| DamienCKj2812/agent-limenghar-property | HEAD/main | `2bd8b621cab0660a98fd880e925ce820cd3b09b2` |
| DamienCKj2812/report-automation | HEAD/main | `5a48a7fda6f93e45f719f499aeef5a279c57ad68` |
| maxscale-io/Aria | HEAD/main | `f35a8559f0d2e1cc0b1879af86179b59d5ae1894` |
| maxscale-io/anva-cms | HEAD/main | `2a964af2fd822a26c4f750a844b6c325b866d25d` |
| DamienCKj2812/logging-loading | HEAD/main | `cb194c5edd71a58158edcc32e26b016a7dfcb3a3` |
| DamienCKj2812/logging-microservice | HEAD/main | `b3d55e3709c9b25841ba411abc92fd80b4d48057` |
| DamienCKj2812/logging-microservice-ui | HEAD/main | `8922e3d51be98b02cbc379041ba2d5e1015b25d9` |
| DamienCKj2812/ConcurrentProgrammingAssignment | HEAD/main | `09d4175d777fc975a979ff67a89bf2ad0349e94f` |
| DamienCKj2812/DSTRAssignment | HEAD/main | `118f0c69da3ff4e0d52e03fdf8314e550862a5ad` |
| DamienCKj2812/DSTRAssignmentPart2 | HEAD/main | `09bfa22becd277f1fadf6fb8ea8b578fd4680e35` |
| DamienCKj2812/DTMAssignment | HEAD/main | `4c204aa919683b6e95ef46a4fa47f2d80568928a` |
| DamienCKj2812/Java-Programming-G18- | HEAD/main | `aa5b887965a284ccdfe0d5f3ce336bb6bacb96c7` |
| DamienCKj2812/OODJ | HEAD/main | `a097333fbf39f1bbda8c3a5aec08ab28289b6604` |
| DamienCKj2812/PFDAGroupAssignment | HEAD/main | `8a5ff287ef577b4eec06f190265492ba1898ff3e` |
| DamienCKj2812/txsa-group-assignment | HEAD/main | `fe5d03483cfce104fc77f67152b623c9852c7dd8` |
| DamienCKj2812/SDMGroupAssignment | HEAD/main | `6a3e72c8b44d7fb72570725a24b1b2e94f835eb1` |
| DamienCKj2812/fedora-dotfiles | HEAD/main | `7c9c9d288aa3c11daf06c4a9de5917c25a6ccfe4` |
| BaconCoding74/rust-gcs-ocs-assignment | main | `23ada794565f8566280718ad3f7ee688f4cb9b78` |
| BaconCoding74/rust-gcs-ocs-assignment | gcs-branch | `7465d7cc18b334ccd16e0420ccd11d0739e5d3eb` |
| BaconCoding74/rust-gcs-ocs-assignment | ocs-branch | `6792a40f82fe3e951ddadecbf32333d4a73c9d6d` |
| DamienCKj2812/damien-portfolio | Local workspace | Uncommitted local working tree; no remote source commit available. |

### Source limitations and review method

- Each included remote repository was inspected through GitHub API calls made with `gh`: metadata/tree inventory and selected documentation/source relevant to the ten explanation sections. This was not an exhaustive review of every source line.
- RTS required branch-specific inspection; its `main` branch does not contain the implemented subsystems.
- FYP notebook outputs were read directly, including the real-telemetry configuration, dataset/split counts, ranking and recommended model. No new training/evaluation was executed.
- Referenced but uncommitted files limit reproducibility particularly in MyReport, FYP and RTS. Features backed only by guidance/tests are described accordingly.
- `txsa-part2-tp067165` was confirmed empty and omitted at Damien's request. The combined TXSA project currently covers only source available in the group repository.
- Private repository/source links require access. This catalogue contains technical descriptions, not credentials or internal deployment addresses.
- Proposed lessons/improvements should be personalized before being presented as first-person statements. Tests present in a repository are evidence of test coverage intent, not proof that they passed in this review.
