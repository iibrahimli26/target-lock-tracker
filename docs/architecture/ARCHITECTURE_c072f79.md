# Architecture Session — split from ARCHITECTURE.md at commit `c072f79`

> Linked from [ARCHITECTURE.md](./ARCHITECTURE.md). Design for US-16 to US-18 ([DESIGN_c072f79.md](../design/DESIGN_c072f79.md)). Decided by the agent on the operator's instruction; the requirements were unsigned when this was written.

No backend change is needed: the page already receives every frame's box, the lock zone, the run state and the run's current frame.

### Decision: where telemetry and timeline marks are computed

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Pure TypeScript functions in the page (`lib/telemetry.ts`, `lib/flow.ts`) | No new API; updates instantly while stepping; tested with Vitest | Area and margin rules exist in TypeScript as well as Python | ✅ |
| New backend endpoint per frame | One language for the rules | A request per step; slower stepping; more code | ❌ |

**Why the page:** telemetry only *describes* a frame; the decisions (LOCKED, LOST) stay on the server. The TypeScript margin uses the same inclusive edge rule as `geometry.inside`, and a test checks both agree at the edge.

### Decision: "Not tracked yet"

The page derives it: run state `running`, frame index after `current_frame` and at or after `start_frame`. No new status is stored.

## Open Questions

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| AQ-18 | Where are telemetry and marks computed? | solution-architect | Resolved | Decided by the agent: in the page, as pure functions. |
| AQ-19 | Is "Not tracked yet" a new server status? | solution-architect | Resolved | Decided by the agent: no; the page derives it from the run state. |
