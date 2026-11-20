# Approval Log

> Single file shared by the **entire pipeline** (`requirement-analysis`, `solution-architect`, and any future stage). Exactly **one active entry** exists at a time, regardless of which stage/skill created it, with status `Pending Approval`. Update it in place as decisions accumulate during a session — never create a second pending entry. Once a human operator explicitly sets it to `Approved` or `Rejected` and the associated commit/PR lands, move it to History below and leave the active slot empty for the next stage to use.

> **How this log is used from 2026-11-20 onward.** On 2026-11-20, with the Stage 1 entry for Feature 1 still unsigned, the operator wrote in chat: "continue and finish the project and give me final version that i can push to github". From that point the agent did not stop at the approval gates; it wrote each stage's documents and continued. The agent approved nothing: **Approved By** and **Approval Date** are blank in every entry and are for the operator to fill in after reading that stage. Because several stages are waiting at the same time, the single Active Entry slot is replaced below by a list of entries awaiting the operator's signature. Decisions that the agent took on the operator's behalf are marked as such in the related documents, each with its reason.

## Entries awaiting the operator's signature

### Entry 1 — Requirement Analysis — Feature 1

- **Status**: Pending Approval
- **Stage**: Requirement Analysis
- **Session Started**: 2026-11-20
- **Related Doc(s)**: docs/design/DESIGN.md — Feature 1: Video Upload and Validation (US-1 to US-6, AC-1.1 to AC-6.12a, OQ-1 to OQ-19, all Resolved)
- **Requested By**: Human operator (project owner), via the project brief in chat
- **Decisions / Scope Covered**:
  - Scope of this entry is Feature 1 only. After OQ-1 it covers brief §7 items 1 and 2 (upload and validation, metadata, frame-by-frame navigation). Features 2 to 6 are untouched, except that showing the first frame (brief §2 F2, first bullet) is needed as the starting position for navigation and is covered by AC-6.1.
  - Drafted 6 user stories (US-1 to US-6), 81 acceptance scenarios, each either written without guessing or following from a resolved Open Question. No scenario is left blocked.
  - Recorded 41 edge cases and failure scenarios, each mapped to the scenarios that cover it. Two are marked otherwise: EC-26 does not arise in this round, and EC-38 is handed to Stage 2 (note 12).
  - Listed as not requested and therefore not included: drag-and-drop upload, upload progress bar, login or multiple users, remembering the video after a restart, queueing several videos, a maximum response time for a frame step. Left out of this round by OQ-15: typed frame number, first/last buttons, keyboard keys, larger steps, play/pause.
  - Decision by the operator (OQ-1, 2026-11-20): metadata display and frame-by-frame navigation are both part of this round.
  - Decision by the operator (OQ-2, 2026-11-20): maximum upload size is 1 GB, with 1 MB = 1,048,576 bytes, so 1,073,741,824 bytes; a file of exactly that size is accepted.
  - Decision by the operator (OQ-3, 2026-11-20): no maximum video duration; a video must have at least 2 frames.
  - Decision by the operator (OQ-4, 2026-11-20): maximum resolution 1280 × 720, inclusive; landscape videos only; no minimum resolution.
  - Decision by the operator (OQ-18, 2026-11-20): square videos are accepted; the maximum resolution is a pixel count, width × height at most 921,600.
  - Decision by the operator (OQ-5, 2026-11-20): the file name plays no part, only the content is checked; QuickTime-type content with H.264 video is accepted like MP4.
  - Decision handed to the agent by the operator (OQ-6, 2026-11-20, "do it yourself as wrote in the docx"): H.264 files the browser cannot play (10-bit, 4:2:2, 4:4:4) are refused with a clear message; only 8-bit 4:2:0 is accepted. The operator can overturn this before approving.
  - Decision by the operator (OQ-7, 2026-11-20): variable-frame-rate videos are accepted; the average FPS is shown with a warning that times are approximate.
  - Decision by the operator (OQ-8, 2026-11-20): total frames and duration are the numbers written in the file header (fast; the video is not read in full at upload); a warning is shown when the numbers turn out to differ, which is when a frame cannot be read.
  - Decision by the operator (OQ-9, 2026-11-20): videos saved with a rotation note are refused.
  - Decision by the operator (OQ-10, 2026-11-20): one video at a time; uploading another asks for confirmation; a refused new file leaves the loaded video in place; of two overlapping uploads the one started last wins.
  - Decision by the operator (OQ-11, 2026-11-20): every problem that can be found is reported at once; each message gives the value found and the value allowed; messages are in English only.
  - Decision by the operator (OQ-12, 2026-11-20): sound and data tracks are ignored; a file with two or more picture tracks is refused.
  - Decision handed to the agent by the operator (OQ-13, 2026-11-20, "[No preference]" twice): frame rate shown with two decimals; duration shown as a clock (minutes:seconds.milliseconds, hours added from one hour on). The operator can overturn this before approving.
  - Decision handed to the agent by the operator (OQ-14, 2026-11-20, "[No preference]"): the implementation log is kept at `docs/implementation/IMPLEMENTATION_LOG.md`, the path the skill writes. The operator can overturn this before approving.
  - Decision handed to the agent by the operator (OQ-15, 2026-11-20, "[No preference]"): navigation is single steps plus a slider with one position for every frame; other controls are left out of this round. The operator can overturn this before approving.
  - Decision by the operator (OQ-16, 2026-11-20): the time of the current frame is shown next to its number.
  - Decision handed to the agent by the operator (OQ-16, first part, 2026-11-20, "[No preference]"): on screen frames are counted from 1. The operator can overturn this before approving.
  - Decision handed to the agent by the operator (OQ-17, 2026-11-20, "[No preference]" twice): at either end of the video the position stays and the step button is shown as inactive; after the warning for an unreadable frame the position stays on the last frame shown. The operator can overturn this before approving.
  - Decision handed to the agent by the operator (OQ-19, 2026-11-20, "[No preference]"): 3GP files with H.264 video are accepted like MP4. The operator can overturn this before approving.
  - Summary: all 19 Open Questions are Resolved. Decided by the operator: OQ-1, OQ-2, OQ-3, OQ-4, OQ-5, OQ-7, OQ-8, OQ-9, OQ-10, OQ-11, OQ-12, OQ-16 (time shown), OQ-18. Handed to the agent and written down with reasons: OQ-6, OQ-13, OQ-14, OQ-15, OQ-16 (numbering), OQ-17, OQ-19. Nothing else was decided on the operator's behalf.
- **Open Questions Resolved This Session**:
  - OQ-1 — "Metadata and navigation both now": US-4 confirmed for this round; US-6 with AC-6.1 to AC-6.8 added; OQ-15 to OQ-17 raised.
  - OQ-2 — Maximum size 1 GB = 1,073,741,824 bytes (1 MB = 1,048,576 bytes), limit inclusive: AC-3.3a and AC-3.3b written.
  - OQ-3 — No maximum duration; minimum 2 frames: AC-3.4a to AC-3.4c written.
  - OQ-4 — Maximum 1280 × 720 inclusive; landscape only; no minimum: AC-3.5a to AC-3.5d written; OQ-18 raised.
  - OQ-18 — Square accepted; maximum applied as a pixel count of 921,600: AC-3.5e and AC-3.5f written.
  - OQ-5 — Any file name, content only; QuickTime-type content accepted like MP4: AC-2.7a to AC-2.7c written; OQ-19 raised.
  - OQ-6 — By delegation: refuse H.264 files the browser cannot play; only 8-bit 4:2:0 accepted: AC-2.8a and AC-2.8b written.
  - OQ-7 — Variable frame rate: accept, show average FPS, warn: AC-4.4a, AC-4.4b and AC-6.12a written.
  - OQ-8 — Header's frame count and duration are used; warning when a frame cannot be read: AC-4.5 and AC-5.7 written; OQ-17 extended.
  - OQ-9 — Videos with a rotation note are refused: AC-4.6 written.
  - OQ-10 — Confirm before replacing; refused new file keeps the loaded video; last of two overlapping uploads wins: AC-5.8a to AC-5.8e written.
  - OQ-11 — All problems reported; found and allowed values included; English only: AC-5.6a to AC-5.6c written.
  - OQ-12 — Sound and data tracks ignored; two or more picture tracks refused: AC-2.9a and AC-2.9b written.
  - OQ-13 — By delegation: frame rate with two decimals; duration as a clock: AC-4.7a to AC-4.7c written.
  - OQ-14 — By delegation: implementation log at `docs/implementation/IMPLEMENTATION_LOG.md`; no scenario affected.
  - OQ-15 — By delegation: single steps plus a slider: AC-6.9a to AC-6.9g written.
  - OQ-16 — Frames counted from 1 (by delegation); frame time shown (operator): AC-6.10a to AC-6.10c written.
  - OQ-17 — By delegation: position stays at the ends with the button inactive; stays on the last frame shown after the warning: AC-6.11a to AC-6.11e written.
  - OQ-19 — By delegation: 3GP with H.264 accepted like MP4: AC-2.10a and AC-2.10b written.
- **Approved By**: <!-- leave blank until a human operator approves -->
- **Approval Date**: <!-- leave blank until approved -->

### Entry 2 — Solution Architecture — Feature 1

- **Status**: Pending Approval
- **Stage**: Solution Architecture
- **Session Started**: 2026-11-20
- **Related Doc(s)**: docs/architecture/ARCHITECTURE.md (Feature 1); input: Entry 1 (unsigned when this stage was written)
- **Requested By**: Human operator (project owner), by the instruction quoted at the top of this log
- **Decisions / Scope Covered**:
  - Entities: Video, VideoMetadata, Problem/Message, FramePosition, each with invariants, boundary behaviour and concurrency analysis.
  - Decisions with benefit/drawback tables: reading container and codec information; how a frame gets on screen; upload transport; storage and state; backend and frontend stack; test strategy.
  - All ten architecture questions (AQ-1 to AQ-10) were decided by the agent on the operator's instruction to continue; none was answered by the operator. Each has its reason in the document, and the operator can overturn any of them.
- **Open Questions Resolved This Session**:
  - AQ-1 to AQ-10 — decided by the agent (see docs/architecture/ARCHITECTURE.md, Open Questions).
- **Approved By**: <!-- leave blank until a human operator approves -->
- **Approval Date**: <!-- leave blank until approved -->

---

## History

<!-- Move closed (Approved/Rejected) entries here, most recent first, once their commit/PR has landed. Keep the Stage field so it's clear which pipeline phase each entry belonged to. -->
