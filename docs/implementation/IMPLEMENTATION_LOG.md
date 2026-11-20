# Implementation Log

Append one entry per implementation pass (one story per pass), **most recent first**. Never edit or delete a previous pass's entry — this file is a traceable history, not a living document.

> **Read this first.** All passes below were made on 2026-11-20 after the operator instructed the agent to continue and finish the project (quoted in `docs/APPROVAL_LOG.md`). **Approval basis for every pass: none signed.** The requirement and architecture entries were unsigned when the code was written. Implementation questions (`IQ-`) were decided by the agent and are marked so. Pull requests could not be opened from the agent's environment; every branch was merged into `main` locally with a merge commit instead of a squash-merged pull request. Each pass names its test commit (red) and its code commit (green) so the order can be checked in the Git history.

**Final state:** `python run.py test` → 246 backend tests (pytest), 68 page-logic tests (Vitest), 14 browser tests (Playwright, Chromium) pass on the agent's Linux machine. 3 further backend tests with real 1 GB files are opt-in (`--slow`) and passed when run once.

**Scenarios without an end-to-end automated test** (their logic is tested, the on-screen behaviour was not driven by a test): AC-1.4 (cancelling the file chooser), AC-6.9e (dragging the slider fast; the newest-request rule behind it is tested and rapid stepping is driven in the browser), AC-7.4 (moving and resizing a box with the mouse; the geometry is tested), AC-9.3 beyond presence of the numbers, AC-15.2 for the amber colour (green and red are asserted).

---

## Pass: 2026-11-20 — Fix: Pause landed one frame off (found by the operator's test run on Windows)

**Branch:** `bugfix/pause-frame-mismatch` · **Red:** `0930cdb` · **Green:** `2459d7b`
**Traces to:** AC-9.2, AC-6.6 (picture and position agree).
**Found by:** the operator ran `python run.py test` on a Windows laptop; `test_playback_draws_over_the_player_and_stops_on_an_exact_frame` failed: the counter read 4 while the still showed frame 3. The test had passed on the agent's Linux machine.
**Cause:** Pause computed the frame from the player's `currentTime`, which on that machine lags the frame the browser has just shown. The page also stored a newly shown frame a moment before painting its number.
**Red:** the test now reads the frame number at the instant Pause is pressed and requires counter, slider and still to stay on it for a second. A "lagging" variant makes `currentTime` trail the shown frame by 40 ms. It failed 3 of 3 runs before the fix.
**Green:** Pause uses the frame number as painted on screen; per-frame notices after Pause are ignored. Both variants passed 30 of 30 runs.
**Deviation:** the playback test was changed, but to make it stricter, not to make it pass. Browser tests: 13 → 14.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-14 | When paused, which frame is "the frame on screen": the one the player's clock names, or the one whose number is shown? | Resolved | Decided by the agent: the one whose number is shown. Reason: it is what the operator was reading when they pressed Pause. |

## Pass: 2026-11-20 — One-command run and test (brief §3)

**Branch:** `chore/run-script` · **Commit:** `a316dbe`
`run.py` starts the application or runs all three test suites. Verified with `--system-python`. The `.venv` path of the script was exercised on Linux only; Windows and macOS were not available to the agent.

## Pass: 2026-11-20 — Page for US-1 to US-15 (operator's console)

**Branch:** `feature/operator-console` · **Commit:** `c45eff2`
**Traces to:** DESIGN.md US-1 to US-6; DESIGN_e64c4e2.md US-7 to US-15; ARCHITECTURE.md "how a frame gets on screen"; ARCHITECTURE_e64c4e2.md "which frame is on screen during playback".

**Deviation: no red phase and not one story per pass.** The page was built in one pass for all stories, and its 13 browser tests (`e2e/test_console.py`) were written after it. They passed on the first run. The logic the page relies on was built test-first in the pass before this one.

| Scenario | Status | Test |
|---|---|---|
| AC-6.7, AC-7.8, AC-9.4 nothing usable without a video | ✅ | `test_nothing_can_be_used_before_a_video_is_loaded` |
| AC-1.1, AC-4.1, AC-4.7, AC-6.1, AC-6.10a | ✅ | `test_upload_shows_first_frame_and_metadata` |
| AC-6.2, AC-6.3, AC-6.9b/c, AC-6.11a-c | ✅ | `test_stepping_and_the_ends_of_the_video` |
| AC-6.9a, AC-6.9d | ✅ | `test_slider_then_step_continues_from_there` |
| AC-6.6 | ✅ | `test_picture_and_position_agree_after_rapid_stepping` |
| AC-5.6a, AC-4.3, AC-5.1 | ✅ | `test_a_refused_file_lists_every_problem_and_a_good_file_still_loads` |
| AC-5.8a/b/c/e | ✅ | `test_replacing_a_video_asks_first` |
| AC-5.6c | ✅ | `test_messages_and_numbers_are_english_in_a_turkish_browser` |
| AC-4.4a, AC-6.10c | ✅ | `test_variable_frame_rate_shows_the_average_and_a_warning` |
| AC-5.7, AC-6.9g, AC-6.11d/e | ✅ | `test_a_frame_that_cannot_be_read_warns_and_keeps_the_position` |
| AC-7.1, AC-7.3, AC-8.1-8.3, AC-9.1, AC-10.1, AC-11, AC-14, AC-15.1 | ✅ | `test_draw_target_and_zone_track_and_read_the_result` |
| AC-9.2 | ✅ | `test_playback_draws_over_the_player_and_stops_on_an_exact_frame` |
| AC-12.1, AC-12.5, AC-13.1 | ✅ | `test_loss_is_shown_and_tracking_resumes_from_a_new_box` |

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-9 | How is the replace confirmation shown? | Resolved | Decided by the agent: the browser's own confirm dialog. Reason: no extra code, works with the keyboard, and the tested decision function takes a yes/no answer. |
| IQ-10 | What does the page do when tracking is lost? | Resolved | Decided by the agent: it goes to the frame of the loss and selects the target tool. Reason: the next thing the operator must do is draw a box there. |
| IQ-11 | Does the player make sound? | Resolved | Decided by the agent: no, it is muted. Reason: OQ-12 says sound tracks are ignored. |
| IQ-12 | Can a box be drawn while tracking runs or the video plays? | Resolved | Decided by the agent: no. Reason: the frame under the mouse would not be the frame the box is stored for. |
| IQ-13 | Does a page reload lose the loaded video? | Resolved | Decided by the agent: no; the page asks the server for the current video on start. Persistence across a server restart remains out of scope. |

## Pass: 2026-11-20 — Page logic for US-4 to US-15

**Branch:** `feature/console-logic` · **Red:** `fddc628` (4 test files fail to load: the modules do not exist) · **Green:** `0243532` (68 passed)
**Covers:** AC-4.7a/b, AC-5.6c, AC-9.2, AC-6.10a-c, AC-7.1 to AC-7.4, AC-7.7, AC-5.8a/b/e, AC-6.6, AC-6.9e, AC-14.4, AC-6.11, AC-15.3 in `frontend/src/lib/*.test.ts`.
**Deviation:** one expectation in `timing.test.ts` was wrong and was corrected before the green commit. The last frame of REF-V starts at 2.9667 s (30 × 1/15 s + 29 × 1/30 s), so 2.96 s shows frame 59, not 60. The corrected value follows from the fixture's definition, not from the code's output.

## Pass: 2026-11-20 — US-13 Select the target again and resume

**Branch:** `feature/reselect-and-resume` · **Commit:** `8bb677a` (tests only)
**Deviation: no red phase.** All 5 tests (AC-13.1 to AC-13.5, `tests/test_us13_resume.py`) passed on the first run, because the restart rule built in US-8 and the loss rule built in US-12 already give this behaviour. Falsification checks instead, run and reverted: making a restart forget earlier results fails 3 tests; making the area rule compare with an old box fails 1 test.

## Pass: 2026-11-20 — US-12 Detect that tracking is lost

**Branch:** `feature/loss-detection` · **Red:** `3021e66` (collection error: `area_changed` does not exist) · **Green:** `debce7e` (241 passed)
**Covers:** AC-12.1 to AC-12.4 and OQ-32 in `tests/test_us12_loss.py`. The 50 % rule is tested at exactly 50 % and at 50 % ± one hundredth of a pixel of width, both as a pure function and through a run.
**Predicates matched:** `area_changed` (exclusive at 50 %); FrameResult invariant "from the loss to the end is lost".
**Deviation:** the set-up of one US-8 test (`test_the_run_before_is_cancelled_when_tracking_starts_again`) was changed: its scripted boxes and its selected box now have the same area. The old set-up broke the new area rule. Its assertions were not weakened.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-8 | What is the run's state after a frame that cannot be read? | Resolved | Decided by the agent: `stopped`, distinct from `lost`, with the damage message. |

## Pass: 2026-11-20 — US-8 Track the target through the video

**Branch:** `feature/tracking-run` · **Red:** `22c5cca` (11 failed) · **Green:** `f669d1f` (227 passed)
**Covers:** AC-8.1 to AC-8.8, AC-10.2 in `tests/test_us08_tracking.py`. AC-8.1 and AC-8.5 use the real CSRT tracker on REF-C: a box on all 900 frames, overlap with the known target path above 0.3 on every frame and at least 0.5 on average, in under 60 s (about 30 s on one core of the agent's sandbox).
**Predicates matched:** TrackingRun "at most one run" (restart cancels and joins); "file only read" (checksum after tracking).

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-6 | How often does the page ask for progress, and how much is sent? | Resolved | Decided by the agent: every 250 ms, and only results from the last known frame on; a new run number makes the server send everything. |
| IQ-7 | What happens when tracking is started while a run is active? | Resolved | Decided by the agent: the active run is cancelled and the new one starts. |

## Pass: 2026-11-20 — US-10 Define the lock zone (backend)

**Branch:** `feature/lock-zone` · **Red:** `dd99af2` (9 failed) · **Green:** `11dfb09` (216 passed) · **Covers:** AC-10.1, AC-10.4 in `tests/test_us10_lock_zone.py`.

## Pass: 2026-11-20 — US-7 Draw the target box (backend)

**Branch:** `feature/target-box` · **Red:** `247dd40` (24 failed) · **Green:** `7c2ee43` (207 passed)
**Covers:** AC-7.1, AC-7.4 to AC-7.8 in `tests/test_us07_target_box.py`: 8 × 8 accepted, 7 on a side refused; touching the picture edge accepted, one pixel past refused.

## Pass: 2026-11-20 — US-14 Lock analytics and US-15 Timeline (logic)

**Branch:** `feature/analytics-and-timeline` · **Red:** `8f274ed` (collection error) · **Green:** `8395289` (183 passed)
**Deviation:** two stories in one pass (both are pure functions over the same status list).
**Covers:** AC-14.1 to AC-14.3, AC-14.5, AC-15.1, AC-15.4 in `tests/test_us14_us15_analytics.py`, with the generated sequence S-1 and its known answers.

## Pass: 2026-11-20 — US-11 Lock status and lock periods

**Branch:** `feature/lock-status-and-periods` · **Red:** `2a41cac` (collection error) · **Green:** `ccba6c0` (173 passed)
**Covers:** AC-11.1 to AC-11.5, AC-10.3 in `tests/test_us11_lock_logic.py`: every edge of the zone one pixel either way, and generated box sequences (a box crossing the zone, entering twice with a loss between, outgrowing the zone) whose lock periods are known by construction.

## Pass: 2026-11-20 — US-6 Step through the video frame by frame (backend)

**Branch:** `feature/frame-navigation` · **Red:** `dc10d04` (22 failed, 1 passed) · **Green:** `d0ee44f` (147 passed)
**Covers:** AC-6.1 to AC-6.8, AC-6.9a/b/g, AC-6.11, AC-6.12a, AC-5.7 in `tests/test_us06_frames.py`. Each reference video carries a per-frame marker, so the tests check which frame a picture is.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-5 | How many recent pictures are kept for stepping back quickly? | Resolved | Decided by the agent: 96. Reason: about three seconds of video, a few megabytes. |

## Pass: 2026-11-20 — US-5 Clear errors and a stable application

**Branch:** `feature/clear-errors` · **Tests:** `19a9d87` (4 failed, 29 passed) · **Fix:** `375b39d` (124 passed)
**Deviation: mostly no red phase.** 29 of 33 tests passed at once because US-1 to US-4 had already built the behaviour. The 4 failures found two real defects: a file was left on disk after an unexpected failure (fixed), and the `truncated.mp4` fixture still contained its index, because the ffmpeg used writes the index first (fixture rebuilt without its index). Falsification checks, run and reverted: disabling the "started last wins" rule, writing numbers with dots, and ignoring problems each fail 2 tests.
**Covers:** AC-5.1 to AC-5.6c, AC-5.8a/c/d in `tests/test_us05_errors.py`.

## Pass: 2026-11-20 — US-4 See the video's metadata after upload

**Branch:** `feature/video-metadata` · **Red:** `04cdbe2` (23 failed, 1 passed) · **Green:** `d001ba7` (91 passed)
**Covers:** AC-4.1 to AC-4.6, AC-4.7c, metadata of AC-2.9a, and the predicate of AQ-3 at its boundary, in `tests/test_us04_metadata.py`.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-4 | Which way round is the rotation angle reported, and what about transforms that are not a plain turn? | Resolved | Decided by the agent: the same sign as ffprobe's "rotation"; any other transform is refused as "a display transform other than a plain turn". |

## Pass: 2026-11-20 — US-3 Enforce file size, resolution and duration limits

**Branch:** `feature/upload-limits` · **Red:** `ff1562c` (15 failed, 16 passed) · **Green:** `de4ede9` (67 passed, 3 opt-in tests deselected)
**Covers:** AC-3.1 to AC-3.5f, AQ-5 in `tests/test_us03_limits.py`. The size limit is tested at 1,073,741,823 / 1,073,741,824 / 1,073,741,825 bytes on the size check, through the API with a lowered limit, and (opt-in) with real files of those three sizes, which passed in 5.4 s.

## Pass: 2026-11-20 — US-2 Refuse files that are not H.264 MP4

**Branch:** `feature/file-type-validation` · **Red:** `a5d76a7` (17 failed, 13 passed) · **Green:** `655a2b2` (36 passed)
**Covers:** AC-2.1 to AC-2.10, AQ-4 in `tests/test_us02_file_type.py`.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-3 | Does the "not an MP4" message name what the file looks like? | Resolved | Decided by the agent: yes, when it can be recognised from the first bytes (AVI, Matroska, WebM, PNG, JPEG, PDF, ZIP, text). |

## Pass: 2026-11-20 — US-1 Upload a drone video

**Branch:** `feature/video-upload` · **Red:** `98ec0ea` (6 errors: no application code) · **Green:** `ae02789` (6 passed)
**Covers:** AC-1.1 to AC-1.3, AC-1.5 and the server side of AC-1.4 in `tests/test_us01_upload.py`, plus a test that a file name with path parts cannot leave the data folder.

| ID | Question | Status | Resolution |
|---|---|---|---|
| IQ-1 | How does a file name with non-English letters travel in a request header? | Resolved | Decided by the agent: percent-encoded UTF-8 in `X-File-Name`. |
| IQ-2 | Which HTTP status does each refusal use? | Resolved | Decided by the agent: 400 no file or interrupted, 413 too large, 422 failed a check, 409 overtaken by a later upload, 404 no such video or frame. |

## Earlier: reference videos

**Branch:** `test/reference-videos` · **Commit:** `973df78`. 51 generated test files (2.5 MB in total, the largest 1.3 MB) and the script that rebuilds them.
