# Concepts pack — architecture signals for AI-assisted coding

**Location:** `.ai/concepts/`  
**Scope:** Markdown documentation only. **Does not** modify `.ai/skills/` (skills remain the canonical automation layer).

**Purpose:** Normalize ideas from a single public talk into **repeatable checks** and **copy-paste prompts** so future work can wire them into rules, skills, CI gates, or review bots. These concepts are **domain-agnostic** - apply them in any repo that adopts Agent OS. **Operator workflow:** see `.ai/docs/guides/workflows/README.md`.

**Consumable-by-AI contract:** Each concept folder has `README.md` (human + agent context) and `prompt.md` (short **procedure** with an explicit **output shape**). Agents should treat numbers and named studies in this pack as **hypotheses** unless backed by **your** metrics, bills, or primary sources.

---

## Source

- **Video:** [YouTube — speaker discusses monoliths, microservices, coupling, cost, ops load, DORA, and AI-assisted coding](https://youtu.be/6e9B7q3gvYY)
- **This file:** Contains a **formatted transcript** (paragraph breaks, minor readability edits). Meaning is preserved; **quantitative claims** should be **verified** before use in ADRs, SLAs, or external communication.

---

## How this relates to `.ai/skills/`

| `.ai/skills/` idea | This pack |
|--------------------|-----------|
| Folder = stable id; `skill.md` + optional `reference.md` | Folder = concept id; `README.md` + `prompt.md` |
| Tool-agnostic numbered workflows | Same: numbered steps + required outputs |
| Gates and checklists | Concepts expose **candidate gates** for later promotion into a skill |

**Next steps (out of scope for this edit):** Map selected gates into `code-implementation`, `plan-master`, or **`concept-run`** (registered under `.ai/skills/concept-run/`) after review.

---

## Concept index

Stable **MOD-*** ids are for cross-links only; they are not registered in `.cursorrules`.

| Id | Directory | Use when… |
|----|-----------|-----------|
| MOD-01 | [`coupling-audit/`](coupling-audit/README.md) | Splitting deployables, extracting services, or assessing change blast radius |
| MOD-02 | [`network-cost/`](network-cost/README.md) | Adding RPC/HTTP hops, drawing synchronous chains, setting latency budgets |
| MOD-03 | [`cost-model/`](cost-model/README.md) | New service/mesh/observability line items; ADR with **\$** |
| MOD-04 | [`ops-headcount/`](ops-headcount/README.md) | Ownership, on-call, SRE/DevOps capacity vs service count |
| MOD-05 | [`modularity-vs-distribution/`](modularity-vs-distribution/README.md) | Choosing modular monolith vs services; extraction rationale |
| MOD-06 | [`ai-amplification/`](ai-amplification/README.md) | **AI-generated code** reliability: boundaries, reviewability, churn |

---

## Trigger table — when to run a concept (operator quick-reference)

This table answers: **"I am about to do X — which concept prompt MUST I run, and where does the output live?"** It is the single source of truth for concept invocation; skills and standards reference it instead of duplicating triggers.

| If you are about to… | Run prompt | Output goes to | Required or recommended |
|---|---|---|---|
| Open a feature SPEC (`{FEATURE_SPEC_ROOT}/<slug>/YYYYMMDD-SPEC.md`) | List MOD-01…MOD-06 in **§15 Concept / NFR registry** with `applies yes/no` + reason | SPEC §15 | **Required** by `FEATURE_STANDARD §3` |
| Run `@code-implementation plan - M{N}` | Copy SPEC §15 rows into `### Concept / NFR registry (this iteration)` in `NEXT.md` | `NEXT.md ## Current iteration` | **Required** by `code-implementation` valid-iteration criteria |
| Run **`@code-implementation`** (start / continue / complete) in a **Cursor or agent session** | [`ai-amplification/prompt.md`](ai-amplification/prompt.md) (MOD-06) | PR description, task `Notes`, or `NEXT.md` iteration registry | **Required** — treat as **AI-assisted: yes** by default; only **`human-only`** (same message, human author) opts out |
| Implement a task whose diff crosses **>1 hard module boundary** (per `{BOUNDARY_MAP}` or interim `DIRECTORY_MAP`) | [`coupling-audit/prompt.md`](coupling-audit/prompt.md) (MOD-01) | PR description; attach to iteration `Notes` | **Required** when boundaries crossed |
| Add a new **synchronous network hop** on a critical request path | [`network-cost/prompt.md`](network-cost/prompt.md) (MOD-02) | ADR appendix **or** SPEC §9 | Recommended |
| Add a new **billable unit** (service, cluster, mesh, log index) | [`cost-model/prompt.md`](cost-model/prompt.md) (MOD-03) | ADR with `$` estimate; tag `evidence` | Recommended; **Required** when crossing the team cost threshold |
| Add a new **deployable / on-call surface** | [`ops-headcount/prompt.md`](ops-headcount/prompt.md) (MOD-04) | Operations runbook + ADR | Recommended |
| Propose **extracting a service** from the monolith | MOD-01 + MOD-05 + MOD-03 + MOD-04 (run in that order) | Architecture ADR | **Required** before approval |
| Run `@code-verify milestone` | Re-run any concept whose iteration row is `Applies=yes` and `Status=pending` | Iteration registry; mark `done` or `gap` | **Required** by verify check matrix |

**Evidence tags (mandatory on every quantitative output):** `measured` | `estimated` | `assumption` | `unknown`. Skill outputs must not present an `assumption` as `measured`.

**AI-assisted default:** Any implementation work driven by a Cursor/agent session is **AI-assisted: yes** unless the human explicitly declares **`human-only`** in the same message. Agents must not self-classify agent-authored diffs as non-AI to skip MOD-06.

**If unsure which concept applies:** default to **MOD-01 (coupling-audit)**. It is the lightest prompt and surfaces whether the change deserves deeper review.

---

## Reliability rules for any agent using this pack

1. **Separate** *story / analogy* from *claim with a citable study*. When in doubt, label **Unverified** and ask for a link or internal metric.
2. **Prefer local measurement** over transcript benchmarks (latency, cost, incident rate, deployment frequency).
3. **`prompt.md` outputs** should include an **`evidence` field**: `measured` \| `estimated` \| `assumption` \| `unknown`.
4. **Do not** treat this pack as authority on DORA, CNCF, or vendor case studies — **look up primary sources** if a decision depends on them.

---

## Formatted transcript

*Paragraphing added. One unclear phrase in the audio is noted inline.*

### Opening — distributed monolith

You split your monolith into microservices. Congratulations. You just made yourself slower, more expensive, and harder to fire from. Microservices aren't an architecture. They're a tax. And right now, most of you are paying it without getting anything back. The companies selling you this pattern have 1,000 engineers. You have 12. That little mismatch is the problem. You didn't escape the monolith. You distributed it.

### Coupling and coordination

Here's what actually happens. You split the code into 30 services, but the business logic is still coupled. One rule changes and you're touching five services, coordinating five releases, running five sets of integration tests. That's not autonomy. That's coordination hell with extra steps. I have watched teams spend three weeks debugging a customer order failure that traced through eight services before anyone found the actual bug. One wrong serialization in service four, three weeks.

This is the distributed monolith. Physically separated, logically chained. It's the worst of both worlds. **Do a coupling audit** before you split anything, or you're just moving the mess around.

### Network cost

Network calls are not free. This is physics, not opinion. In-process function calls run in nanoseconds. HTTP over TLS runs in 1 to 10 milliseconds. Chain five services together on a single request, you're at 50 to 100 milliseconds of overhead before a single line of your business logic executes. And that number is minimum. That's a million time difference in communication speed. And those of you out there that want me to explain the math, well, you write a function, do a memory call, and then write something on a web service or a rest request across the wire, and then do that call. Just use `toString`. Let me know how long it takes to connect and actually run. That's what I'm talking about.

One team I know moved from microservices back to a monolith. Their average API response time dropped from 1.2 seconds to 89 milliseconds. They changed absolutely nothing else. Same logic, same database, just eliminated the network hops. 93% improvement, zero feature work, just architecture. Measure your inter-service latency before you accept it like normal because that number is lying to you about your system's actual capability.

### Money — compute, mesh, observability

Let's talk about money because this conversation never does. Microservices need about 25 more compute than some equivalent monolith. Container orchestration overhead, side car proxies, service mesh. Istio style side cars can consume up to 90% of a pod CPU and memory. 90% your workload is running on the leftovers. Then you add observability, distributed tracing, centralized logging, APM tooling across 50 services. That's 50,000 to 500,000 per year just to see what's happening in your own system.

Amazon Prime Video, AWS Step Functions, Lambda, the full serverless microservice stack hit a hard ceiling at 5% of expected load. Infrastructure costs were eating them. They consolidated into a monolith on EC2 and ECS. Costs dropped over 90%. You want to see the numbers? Check out my blog. Don't know where the blog is? Go to my link tree. Links in the description. Put a dollar number on your architecture every quarter. If you can't justify it against the benefits, you're running a look at me, I'm cool type of infrastructure.

### Ops headcount and consolidation stories

Here's the one that gets teams fired. Mature microservices, one SRE for every 10 to 15 services. Less mature, no standardized platform tooling, one SRE for every five to 10 services. You have 40 services and two DevOps engineer. Do that math right now. You're already underwater. A well-architected monolith, one or two DevOps engineers. Entire application, doesn't matter how many internal modules you have.

Segment hit 50 plus microservices, debugging pain, deployment friction, head of line blocking where one failing service delayed event delivery across the whole platform, multiple repos, diverging shared libraries, the maintenance burden became unaffordable. They consolidated, not because they failed at microservices, because the cost of benefits stopped making sense. Headcount your architecture the same way you headcount your product team, or it'll headcount you.

### DORA — modularity vs style

The DORA data from 2024 is definitive. Elite teams deploy 973 times more frequently than low performers. Change failure rate five times lower. Mean time to recovery 6,570 times faster. That's not microservices doing that. That's modularity doing that. Elite teams with modular monoliths hit the same DORA numbers as elite microservices teams. The architecture style isn't a variable. The coupling is the variable.

Think about a circuit breaker panel in a building. Every circuit is isolated. A fault doesn't kill the server room. You don't need a different building per appliance. You need clean insulation inside one structure. That's a modular monolith. One deployable, clean internal boundaries, domain owned modules, shared database with logical schema separation. You get the rigor without the network tax. Build modules with hard internal API boundaries first. Distribute only when you have a specific, measurable reason to.

### AI as amplifier (2025 DORA mentioned)

This is the one nobody's talking about yet. 2025 DORA research. AI tool increased task completion 21%. Pull request volume up 98%. Delivery performance flat. Here's why. AI is an amplifier. In a tightly coupled architecture, AI-generated code creates a higher volume of bugs faster. Code churn doubled from 3.3% to over *[transcript audio unclear — treat magnitude as directional, not literal]*. AI only delivers real value when the architecture is modular and decoupled because that's the only context where a change can be isolated and verified quickly. You can't review AI code in a code base where every module touches every other module. The engineers shipping AI-assisted features fastest right now are working in a clean modular systems. Not because AI is smarter there, because the architecture lets you contain the blast radius of something going wrong.

So, before you adopt AI coding tools, fix your coupling. Otherwise, you're accelerating into a wall.

### Conway — ownership before boundaries

Your system architecture mirrors your communication structure, always. This isn't a theory. It's been observed consistently for decades. If three teams have to coordinate the ship of feature, you have three services that are logically coupled. The org chart is writing the code. The fix isn't restructuring the code first, it's restructuring ownership. Stream-aligned teams. One team owns one business capability end-to-end. Catalog team owns catalog. Order teams own orders. No cross-team coordination required for standard feature delivery. Two-pizza team, eight to 10 people. That's your threshold. If a team needs more than that to manage their domain, the domain is too big or the architecture is too tangled.

I've seen teams reorganize their code base four times and wonder nothing got faster. They kept the same org structure every time. The architecture snapped back to match the org within six months, every single time. You need to align team ownership to business domains before you touch any deployment boundary.

### Industry course-correction (CNCF survey cited)

The 2025 CNCF survey, 42% of organizations actively consolidating microservices back into larger deployable units. Service mesh adoption dropped from 18% in '23 to 8% in '25. The industry is course-correcting. For 90% of applications, the modular monolith is the right architecture right now. Not because microservices are wrong, because the microservice premium only pays off when you actually need independent scaling at the service level, or when your org is too large for shared deployment.

### Modular monolith as default — tools and strangler

And the modular monolith isn't a dead end, it's a launchpad. If you build real module boundaries with tools like ArchUnit, you enforce package rules programmatically, or Spring Modulith, you verify boundaries at runtime, structuring it as a real option later. You move a module out when you have a specific reason, traffic spike, team size, polyglot requirements, not because someone read a blog post. The Strangler Fig pattern handles legacy migration. New capabilities like modular slices, route traffic incrementally through an API gateway, retire the old code piece by piece. No big bang rewrites, no 6-month freeze. Default to the modular monolith, extract only when you can name the specific scaling or ownership problem you're solving.

### When microservices can win

I'm not here to tell you microservices are always wrong, they're not. A thousand plus engineers, a shared monolith that scales, create coordination costs that grow as a square number of teams, not linearly, exponentially. One shared library upgrade becomes a company-wide negotiation. Microservices break that by making the blast radius of decisions physically bounded. A team upgrades their runtime, switches from Java to Go for some high concurrency workload. They adopt a different data store. No architecture review board sign-off is required. That's what Amazon and Netflix are actually buying, not CPU efficiency, organizational independence.

And if your system has real scaling variance, say your search component needs a hundred times more compute than your settings page, a monolith will force you to over-provision the wrong thing. Independent scaling is the right call, but you need a thousand engineers or extreme traffic variance to justify the overhead, not 12 engineers in a dream. If you can't name the specific organizational or scaling constraint that microservices solve for you, you don't have the problem microservices fix.

### FinOps and ADRs

Architecture is a financial decision, not just a technical one. In 2026, FinOps is a board-level concern. The CTO is getting asked to justify infrastructure spend in quarterly reviews. That means developers need architectural literacy. You need to know the cost implications of spinning up a new service before you do it. Use cost calculators before deploying. Document architectural tradeoffs in architectural decision records, ADRs, not to slow down decisions, to make decisions visible and reversible. One team I know was running on $80,000 a month on microservices infrastructure. They upgraded to a monolith, same feature set, $4,000 a month. That's not an edge case. That's what happens when nobody adds up the bill. Write an ADR for every architectural decision above a certain cost threshold and make the dollar number visible from day one.

### Mindset — complexity budgets

Here's the mindset shift that separates engineers from developers. You're not choosing between two technology options. You're choosing between two complexity budgets. Every distributed call is a complexity investment. Every additional service is a cognitive load investment. Every team coordination requirement is a velocity investment. And all of those investments have to be paid back with actual business outcomes. The engineer's job is not to implement the most technically interesting system. It's to match the complexity of the system to the complexity of the actual problem, nothing more, nothing less.

Monolith is not a failure. A microservice is not maturity. Tight coupling is the failure. Accidental distribution is immaturity. The goal is always modularity of logic. Where that logic runs is a deployment detail you should be able to change. The best architecture I've ever seen was a system nobody thought about. It shipped features, it stayed up, it cost a predictable amount of money. Nobody was on call at 2:00 a.m. tracing requests through 12 services. The developers owned their domains, understood their boundaries, and moved fast because the system got out of their way. That's the target, not the number of services, the number of times your architecture gets out of your team's way.

You need more serious CTO? There's a link right here. It's also in the description. 42% of the industry is already undoing what you might be about to build. The question is whether you land that before or after you pay for it.
