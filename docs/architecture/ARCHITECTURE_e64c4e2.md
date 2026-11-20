# Architecture Session — split from ARCHITECTURE.md at commit `e64c4e2`

> Linked from [ARCHITECTURE.md](./ARCHITECTURE.md). Permanent linked record of the architecture session for Features 2 to 6 (requirements: [DESIGN_e64c4e2.md](../design/DESIGN_e64c4e2.md)).

> **Gate note.** The requirements this builds on were not signed when this was written; the agent continued on the operator's instruction of 2026-11-20 (see `docs/APPROVAL_LOG.md`). Every architecture question below was decided by the agent and says so.

## Data Models

### Entity: Box
Traces to: US-7, US-10, US-11

| Field | Type | Unit | Constraints |
|---|---|---|---|
| x, y | number | picture pixels from the top-left corner | finite; ≥ 0 |
| w, h | number | picture pixels | finite; ≥ 8 for a box the operator draws |

**Invariants:**
- A box the operator draws lies fully inside the picture: x + w ≤ width and y + h ≤ height (OQ-22).
- Coordinates are picture pixels everywhere (API, storage, tracker); only the page converts to and from screen pixels, in one function (AC-7.3).

**Boundary Behavior:**
- Min: 8 × 8 accepted, 7 on either side refused (OQ-21). Max: the full picture is accepted.
- Zero / negative / not a number: refused as a bad request; the stored box is unchanged.
- Boxes produced by the tracker are stored as returned (they may be smaller than 8 px); a tracker box with no area counts as a tracker failure.

**Concurrency:** target box and lock zone are single values replaced as a whole under the session lock; the last write wins.

**Predicate: inside(box, zone)** — true exactly when `box.x ≥ zone.x`, `box.y ≥ zone.y`, `box.x + box.w ≤ zone.x + zone.w` and `box.y + box.h ≤ zone.y + zone.h` (edges inclusive, OQ-23).

**Predicate: area_changed(previous, current)** — true exactly when `|area(current) − area(previous)| > 0.5 × area(previous)` (OQ-28). Exactly 50 % is false.

### Entity: FrameResult (one per frame of the video)
Traces to: US-8, US-12, US-13

| Field | Type | Unit | Constraints |
|---|---|---|---|
| value | one of: not tracked, lost, Box | — | exactly one per frame index |

**Derived status** per frame (US-11): not tracked → `not_tracked`; lost → `lost`; a Box → `locked` if a lock zone exists and inside(box, zone), else `unlocked`.

**Invariants:**
- The list always has exactly `frame_count` entries.
- A (re)start at frame g keeps entries before g, and replaces every entry from g on (OQ-29).
- When a run stops at frame f because of a loss or an unreadable frame, entries f to the end are `lost` (OQ-27, OQ-32).

### Entity: TrackingRun
Traces to: US-8, US-12, US-13

| Field | Type | Unit | Constraints |
|---|---|---|---|
| state | idle, running, lost, completed, stopped | — | `stopped` = met a frame that cannot be read |
| revision | integer | — | +1 on every (re)start; lets the page drop stale data |
| start_frame | integer | frame index from 0 | frame of the target box |
| current_frame | integer | frame index from 0 | last frame handled by this run |
| processing_fps | number | frames per second | frames handled ÷ seconds since this run started |
| lost_at, lost_reason | integer, text | frame index; — | set in states `lost` and `stopped` |

**Invariants:**
- At most one run per video is active. Starting a run cancels the one before it and waits for it to end before changing results.
- The uploaded file is only read, never written (AC-8.4).

**Boundary Behavior:**
- Start on the last frame: that frame gets the selected box and the run completes at once.
- Loss on the very next frame after a selection is possible and handled like any other loss.

**Concurrency / Race-Scenario Analysis:**
- The page polls while the run writes results → one lock guards results and run fields; a poll gets a consistent copy.
- A new start arrives while a run is active → a cancel flag is set, the old run is joined, then results from the new frame on are cleared and the new run starts.
- The video is replaced while a run is active → the session is closed (cancel + join) before the file is deleted.
- The lock zone changes while a run is active → statuses are computed from results and zone at read time, so they are always consistent with the zone in force.

### Entity: LockPeriod / Analytics
Traces to: US-11, US-14, US-15

| Field | Type | Unit | Constraints |
|---|---|---|---|
| start, end | integer | frame index from 0 | inclusive; start ≤ end; all frames between are `locked` |
| frames | integer | frames | end − start + 1 |
| seconds | number | seconds | frames ÷ fps (OQ-25) |

Analytics: frames and seconds for locked, unlocked, lost, not tracked; number of periods; longest and average period. **Boundary:** with no periods, count, longest and average are 0 (no division). **Invariant:** locked + unlocked + lost + not tracked = frame_count.

## Technology / Design Decisions

### Decision: which OpenCV tracker

Measured on REF-C (900 frames, 1280 × 720) on one CPU core of the agent's sandbox; "overlap" is the mean overlap ratio with the true target.

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| CSRT | Mean overlap 0.70; adapts the box size (so the 50 % area rule means something); 31 frames/s = 29 s for the benchmark | Slowest of the fast trackers | ✅ |
| KCF | 152 frames/s | Mean overlap 0.45; the box size never changes, so the area rule could never fire | ❌ |
| MIL | Mean overlap 0.71; in the main OpenCV package | 27 frames/s, slower than CSRT, and no size adaptation | ❌ |
| Deep trackers (Nano, ViT, DaSiamRPN) | Accurate | Need model files that would have to be downloaded and stored | ❌ |

**Why CSRT:** best accuracy among the built-in trackers, twice as fast as the 60-second limit requires even on one slow core, and it changes the box size.
**Why not KCF:** fast but loose, and blind to size.
**Why not MIL:** no faster and no better.
**Why not deep trackers:** extra model files conflict with "runs with one command".
The tracker name is a setting; KCF and MIL remain selectable.

### Decision: how tracking runs and reports

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Background thread; the page polls a status endpoint a few times per second | Simple; testable with plain HTTP; a long run never blocks other requests | Progress arrives in steps, not continuously | ✅ |
| WebSocket or server-sent events | Continuous updates | More moving parts and harder tests for no visible gain at 4 polls/s | ❌ |
| Track inside the request | Simplest code | A 30-second video would hold the request for half a minute; no progress, no navigation meanwhile | ❌ |

**Why thread + polling:** meets "real-time processing information" with the least machinery.
**Why not WebSocket/SSE:** complexity without benefit here.
**Why not in-request:** blocks the interface.

### Decision: where lock logic lives

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Pure Python functions in `lock_logic.py`, fed with boxes and a zone | Tested independently with generated box sequences that have known answers, as the task requires; one source of truth | The page must ask the server after a zone change | ✅ |
| In the page (TypeScript) | Instant recalculation | Two languages would hold the rules; harder to test against the tracker | ❌ |

**Why Python, pure:** the task demands independent tests of the lock-duration logic.
**Why not in the page:** duplicates the rules.

### Decision: which frame is on screen during playback

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Map the player's media time to a frame with the header's per-frame start times; use the browser's per-frame callback when it exists | Correct for variable frame rate (AC-9.2); pure function, testable | Depends on the browser reporting the media time of the frame shown | ✅ |
| frame = round(time × FPS) | One line | Wrong for variable frame rate; rounding can show the neighbour's box | ❌ |

**Why the table lookup:** OQ-7 accepts variable-frame-rate files.
**Why not multiply by FPS:** breaks exactly on those files.
When playback stops, the page shows the backend's picture for that frame, so the stopped view is exact in any case.

## Open Questions

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| AQ-11 | Which OpenCV tracker is used? | solution-architect | Resolved | Decided by the agent: CSRT, with the measurements in the table above. |
| AQ-12 | How does tracking run and report progress? | solution-architect | Resolved | Decided by the agent: background thread with polling. |
| AQ-13 | Where is the lock logic computed? | solution-architect | Resolved | Decided by the agent: in pure Python functions on the server. |
| AQ-14 | How is the player's time mapped to a frame? | solution-architect | Resolved | Decided by the agent: by the header's per-frame start times; the last frame whose start is not after the media time. |
| AQ-15 | Are frames processed at full size or shrunk for speed? | solution-architect | Resolved | Decided by the agent: full size. Reason: 921,600 pixels is the maximum (OQ-18) and CSRT already meets the time limit; shrinking would cost accuracy for nothing. |
| AQ-16 | How are tracking tests made repeatable? | solution-architect | Resolved | Decided by the agent: the loss and resume rules are tested with a scripted stand-in for the tracker (it returns boxes written in the test); one test uses the real CSRT tracker on REF-C against the known target path. Reason: the OpenCV tracker is the one true external dependency. |
| AQ-17 | What is stored for a frame where the tracker returns an empty box? | solution-architect | Resolved | Decided by the agent: it is treated as a tracker failure (LOST). |
