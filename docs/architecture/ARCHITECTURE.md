# Architecture Atlas

Central index of solution-architect output for this repository. Only requirements `Approved` (Stage: Requirement Analysis) in [docs/APPROVAL_LOG.md](../APPROVAL_LOG.md) may be modeled here (see the [solution-architect skill](../../.claude/skills/solution-architect/SKILL.md)). Individual sessions may split their work into `ARCHITECTURE_<commit-id>.md` files when this file grows too large; every such file must be listed below.

> **Gate note.** The Stage 1 entry for Feature 1 was still unsigned when this document was written. The operator instructed the agent in chat on 2026-11-20 to continue and finish the project, and the agent proceeded on that instruction. See the note at the top of `docs/APPROVAL_LOG.md`. All architecture questions below were therefore decided by the agent; each one says so and gives its reason, and the operator can overturn any of them.

## Linked Architecture Documents

| File | Scope / Topic | Started (commit) | Status |
|---|---|---|---|
| (this file) | Core — Feature 1: upload, validation, metadata, frame navigation | b916094 | Active |
| [ARCHITECTURE_e64c4e2.md](./ARCHITECTURE_e64c4e2.md) | Features 2 to 6: boxes, tracking run, lock logic, analytics (AQ-11 to AQ-17) | e64c4e2 | Active |
| [ARCHITECTURE_c072f79.md](./ARCHITECTURE_c072f79.md) | Console improvements (AQ-18, AQ-19) | c072f79 | Active |

## System overview

One Python process (FastAPI) serves a small JSON/HTTP API and the built web page. The browser page (React, TypeScript) is the operator's console. OpenCV runs only in the Python process.

```
Browser (React)                         Python process (FastAPI)
  upload control  ── raw file body ──►  ingest: stream to disk, count bytes
                                        probe:  read MP4 header (no decoding)
                                        rules:  all problems, found/allowed
  metadata panel  ◄── JSON ───────────  store:  one current video
  stage (paused)  ◄── JPEG frame k ───  frames: OpenCV decodes frame k
  stage (playing) ◄── original bytes ─  file:   served unchanged, with ranges
```

## Data Models

### Entity: Video
Traces to: US-1, US-5 (docs/design/DESIGN.md)

| Field | Type | Unit | Constraints |
|---|---|---|---|
| id | string (32 hex chars) | — | required; random; new for every accepted upload |
| name | string | — | required; the operator's file name, kept only for display |
| size | integer | bytes | required; 1 to 1,073,741,824 |
| path | filesystem path | — | required; `<data_dir>/<id>.mp4`; never derived from `name` |
| metadata | VideoMetadata | — | required |
| warnings | list of Message | — | may be empty |

**Invariants** (must always hold true):
- At most one Video is current at any time (OQ-10).
- The bytes at `path` are identical to the bytes the operator sent (AC-1.2).
- `path` is inside `data_dir` whatever `name` contains (Stage 1 note 1).
- A refused upload never becomes current and leaves no file behind.

**Boundary Behavior:**
- Min/Max size: 0 bytes is refused ("empty"); exactly 1,073,741,824 bytes is accepted; one byte more is refused. Reading stops as soon as the limit is passed.
- Empty/Null: a request with no bytes and no file name is "no file provided"; with a file name it is "the file is empty".
- Overflow/Truncation: an upload that ends early (connection lost) is discarded and its partial file deleted.

**Concurrency / Race-Scenario Analysis:**
- Two uploads overlap → each upload takes a number when it starts; only the upload holding the highest number may become current when it finishes ("the one started last wins", OQ-10). An earlier one that finishes later is discarded.
- A frame is requested while the video is being replaced → requests carry the video id; a request for an id that is no longer current is refused with "no such video".

### Entity: VideoMetadata
Traces to: US-3, US-4

| Field | Type | Unit | Constraints |
|---|---|---|---|
| width, height | integer | pixels | stored picture size; width × height ≤ 921,600; width ≥ height |
| frame_count | integer | frames | from the header's sample table; ≥ 2 |
| duration | rational (units / timescale) | seconds | from the picture track's header |
| fps | rational | frames per second | frame_count ÷ duration (the average) |
| variable_frame_rate | boolean | — | see predicate below |
| timing | list of (count, length) runs + timescale | ticks | the header's per-frame lengths, run-length encoded |

**Invariants:**
- All values describe the first picture track and come from the header; nothing is decoded at upload (OQ-8).
- `frame_count` equals the sum of the run counts in `timing`.

**Boundary Behavior:**
- Min/Max: 1 frame is refused, 2 accepted; 921,600 pixels accepted, any larger even-sized picture refused; width = height accepted, width < height refused.
- Empty/Zero: a picture track that lists no frames is refused as too short (found: 0 frames).
- Overflow: 64-bit header fields (long files) are read in full.

**Predicate: variable frame rate** (Stage 1 note 8, AQ-3). Take the time gaps between the starts of consecutive frames, in header ticks (the last frame's own length is ignored). The video is *variable* when `longest gap − shortest gap > max(1 tick, 1 % of the median gap)`; otherwise it is constant. Exactly at the threshold it is constant.

**Concurrency:** metadata is computed once per upload and never changes afterwards; no race.

### Entity: Problem / Message
Traces to: US-2, US-3, US-5 (OQ-11)

| Field | Type | Unit | Constraints |
|---|---|---|---|
| code | string | — | required; stable identifier, e.g. `codec`, `resolution` |
| message | string | — | required; one English sentence; contains `found` and `allowed` when present |
| found | string or null | — | the value found, written the English way (2,073,600) |
| allowed | string or null | — | the value allowed |

**Invariants:**
- Every problem that can be determined for a file is returned in one response (OQ-11); no problem is reported twice.
- No message contains a stack trace, exception name or server path (AC-5.3).
- All messages are produced in one module (`messages.py`); the page shows them unchanged (Stage 1 note 11).

**Boundary Behavior:** if the file is over the size limit, or is not readable as an MP4-family file, the checks that need its header cannot run and only that one problem is returned.

### Entity: FramePosition
Traces to: US-6

| Field | Type | Unit | Constraints |
|---|---|---|---|
| index | integer | frames, counted from 0 | 0 ≤ index < frame_count |
| number (on screen) | integer | frames, counted from 1 | index + 1 (OQ-16) |
| time (on screen) | rational | seconds | index ÷ fps (OQ-16, OQ-7) |

**Invariants:**
- The API, the stored results and OpenCV use `index`; only the page converts to `number`, in one function (Stage 1 note 13).
- The picture returned for `index` is frame `index` of the file as OpenCV decodes it, which is the same decoder the tracker uses.

**Boundary Behavior:**
- Min/Max: index −1 and index = frame_count are refused ("frame does not exist"); the page keeps the position and shows the step button as inactive (OQ-17).
- Unreadable frame: the request fails with the "file is damaged, this frame cannot be read" warning; the page keeps the last frame it showed (OQ-17).

**Concurrency:** several frame requests can be in flight (fast stepping, slider). The server serialises decoding with a lock. The page numbers its requests and shows only the answer to the newest one, so picture and position always agree once things settle (AC-6.6, AC-6.9e).

## Technology / Design Decisions

### Decision: reading container and codec information

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Own header reader (`mp4probe.py`, pure Python) | Reads only the index, so it is fast even for 1 GB (OQ-8); no extra install; every rule (tracks, rotation note, bit depth, frame lengths) is under our control and testable | Our own code to maintain; unusual layouts need explicit handling | ✅ |
| PyAV (FFmpeg bindings) | Battle-tested on odd files | 30 MB extra dependency; per-frame lengths need a pass over the whole file; behaviour differs between versions | ❌ |
| `ffprobe` program | Battle-tested; rich output | Needs FFmpeg installed on every machine, which breaks "runs with one command" | ❌ |
| OpenCV only | Already required | Cannot report bit depth, rotation note, track list or per-frame lengths | ❌ |

**Why own reader:** OQ-8 asks for header-only, fast validation, and the rules of US-2 to US-4 need fields that only the header tables give exactly.
**Why not PyAV:** its fast path does not expose the per-frame length table; reading packets would touch the whole file.
**Why not ffprobe:** an undeclared system dependency.
**Why not OpenCV only:** it cannot answer half of the acceptance criteria.

### Decision: how a frame gets on screen (Stage 1 note 4)

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Paused: frame image decoded by the backend. Playing: the browser's video player with boxes drawn over it | Paused picture is exactly the frame the tracker sees, also for variable frame rate; exactness is testable without a browser; playback still uses the original file as the task suggests | Two display paths in the page | ✅ |
| Browser video player only, stepping by setting the time | One display path | Seeking by time can land on a neighbouring frame; browser and OpenCV could disagree on which frame is "k" | ❌ |
| Backend frame images only | Simplest, always exact | No smooth playback; ignores the task's tip | ❌ |

**Why the hybrid:** AC-6.4, AC-6.5 and AC-6.12a demand exact frames, and the box the operator draws must be on the frame the tracker starts from.
**Why not player only:** frame-exactness would depend on browser behaviour we cannot control.
**Why not images only:** playback with boxes over the player is required in Feature 3.

### Decision: upload transport

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| File sent as the raw request body, name in a header | Streamed straight to disk; size limit enforced while reading; no multipart library | Not a classic HTML form post | ✅ |
| Multipart form upload | Standard form encoding | The framework stores the whole body in a temporary file before our code runs, so 1 GB is written twice and the limit applies late | ❌ |

**Why raw body:** a 1 GB limit needs streaming and early refusal.
**Why not multipart:** double disk writes and a late size check.

### Decision: storage and state

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| File in `data/` (git-ignored) plus state in memory | Nothing to install; matches "one video at a time"; restart starts clean | Nothing survives a restart (not requested) | ✅ |
| Database (SQLite) | Survives restarts | Persistence was listed as not requested; more code and tests | ❌ |

**Why memory + file:** smallest design that meets every scenario.
**Why not a database:** would add a feature nobody asked for.

### Decision: backend and frontend stack

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| Python + FastAPI + OpenCV; React + TypeScript + Tailwind (Vite) | The brief's suggested stack; OpenCV trackers are first-class in Python; typed page code; fast test loop | Two toolchains (Python, Node) | ✅ |
| Everything in the browser (OpenCV.js) | One toolchain | OpenCV.js lacks the contrib trackers; large download; hard to meet the speed target | ❌ |
| Python desktop UI (Qt) | One language | Not a web application as the brief asks | ❌ |

**Why the suggested stack:** it fits every requirement and the reviewers know it.
**Why not OpenCV.js:** tracker availability and speed.
**Why not Qt:** the brief asks for a web application.

### Decision: test strategy for Feature 1

| Option | Benefits | Drawbacks | Chosen |
|---|---|---|---|
| pytest against the API with committed reference videos; exact size boundary on the pure size check; Vitest for page logic; Playwright for the screen scenarios | Expectations come from how each file was made; fast; runs without FFmpeg | The 1 GB boundary is exercised through the API with a lowered limit, plus one opt-in test with real 1 GB files | ✅ |
| Generate videos during the test run | Nothing binary in the repository | Tests would need FFmpeg; slower | ❌ |
| Always upload real 1 GB files | Most literal | Several GB of disk traffic on every run | ❌ |

**Why:** keeps the suite fast and independent of FFmpeg while still asserting the real limit value (AQ-6).
**Why not generate at test time / real 1 GB always:** tooling dependency and run time.

## Open Questions

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| AQ-1 | How is container and codec information read: own header reader, PyAV, ffprobe, or OpenCV only? | solution-architect | Resolved | Decided by the agent on the operator's instruction to continue (2026-11-20): own header reader. Reason: see the decision table. |
| AQ-2 | How does a frame get on screen (Stage 1 note 4)? | solution-architect | Resolved | Decided by the agent: backend frame image when paused, browser player when playing. Reason: exact frames for stepping and target selection. |
| AQ-3 | What exactly separates constant from variable frame rate (Stage 1 note 8)? | solution-architect | Resolved | Decided by the agent: variable when the longest and shortest gap between consecutive frames differ by more than max(1 tick, 1 % of the median gap). Reason: tolerates timestamp rounding (33/34 ms patterns) but catches real variation. |
| AQ-4 | Does a cover picture kept in the file's tags count as a picture track (Stage 1 note 12)? | solution-architect | Resolved | Decided by the agent: no. Only real tracks are counted. Reason: OQ-12 speaks of tracks; a tag picture cannot be confused with the footage. |
| AQ-5 | MP4 files with a fragmented layout list no frames in the main index. Accept or refuse? | solution-architect | Resolved | Decided by the agent: refuse with a clear message. Reason: header-only reading (OQ-8) cannot count their frames; cameras and drones do not produce this layout. |
| AQ-6 | How are the 1 GB boundary tests kept fast (Stage 1 note 3)? | solution-architect | Resolved | Decided by the agent: exact byte boundary tested on the size check itself; the API path tested with a lowered limit; the default limit asserted to be 1,073,741,824; one opt-in slow test uploads real 1 GB files. |
| AQ-7 | Should upload also check that the index does not point past the end of the file (Stage 1 note 9)? | solution-architect | Resolved | Decided by the agent: no. Reason: OQ-8 chose to trust the header and warn when a frame turns out to be unreadable; an extra rule would change that choice. |
| AQ-8 | Is the replace confirmation asked before the new file is sent or after its checks (Stage 1 note 10)? | solution-architect | Resolved | Decided by the agent: before sending. Reason: a declined 1 GB upload should not be transferred first. |
| AQ-9 | For a file with a rotation note, is orientation judged on the stored or the shown picture (Stage 1 note 14)? | solution-architect | Resolved | Decided by the agent: stored picture. Reason: the file is refused anyway; the stored size is what the header states. |
| AQ-10 | Where is the uploaded video kept and for how long? | solution-architect | Resolved | Decided by the agent: in `data/` (git-ignored) until it is replaced; cleared at start-up. Reason: persistence was not requested. |
