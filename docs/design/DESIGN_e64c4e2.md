# Design Session — split from DESIGN.md at commit `e64c4e2`

> Linked from [DESIGN.md](./DESIGN.md). This file holds requirement-analysis output produced in a single working session that would otherwise have made the central atlas too large. It is a **permanent linked record** — once a commit/PR lands for this session, its atlas row simply changes from `Active` to `Merged`/`Closed`; this file is never folded back into `DESIGN.md`.

> **How this session was run.** On 2026-11-20 the operator instructed the agent to continue and finish the project (quoted in `docs/APPROVAL_LOG.md`). The agent therefore wrote the requirements for Features 2 to 6 in one session and did not stop for answers. Every Open Question below was **decided by the agent**, not by the operator; each one gives its reason in plain words and can be overturned by the operator. The brief's rule "one feature per round" was not followed in this session for the same reason.

**Scope:** Feature 2 (manual target selection), Feature 3 (tracking), Feature 4 (lock zone), Feature 5 (tracking loss and recovery), Feature 6 (analytics and timeline), and the non-functional requirements of brief §3. **Sources:** brief §2 and §3; KUAVA Newcomer Task, Project B.

**Fixed values used below.** REF-C (`bench_720p_30s.mp4`) shows a 96 × 64 target whose centre in frame n (counted from 0) is at x = 640 + 300·sin(2πn/450), y = 360 + 150·sin(2πn/300). In its first frame the target occupies x 592 to 688, y 328 to 392. "S-1" is the generated status sequence at 30 fps: 10 unlocked, 30 locked, 5 unlocked, 15 locked, 3 lost, 7 locked (70 frames).

## User Stories

### US-7: Draw the target box
As an operator
I want to draw a box around the target on the frame shown, and adjust or redraw it
So that the tracker knows what to follow

### US-8: Track the target through the video
As an operator
I want the application to follow the selected target frame by frame with an OpenCV tracker and show its progress
So that I get the target's position on every frame without marking it by hand

### US-9: See the boxes over the video
As an operator
I want to play the original video with the tracked box drawn over it, and see the box on any frame I stop at
So that I can judge with my own eyes whether the tracker followed the target

### US-10: Define the lock zone
As an operator
I want to draw a rectangle on the picture that is the lock zone
So that the application can tell when the target is locked

### US-11: Lock status and lock periods
As an operator
I want each frame marked LOCKED when the whole target box is inside the lock zone, and every continuous lock period recorded
So that I can measure how long the target stayed locked

### US-12: Detect that tracking is lost
As an operator
I want the application to notice when it has lost the target and tell me clearly
So that wrong positions are not counted as lock time

### US-13: Select the target again and resume
As an operator
I want to mark the target again after a loss and continue tracking from there
So that one loss does not waste the rest of the video

### US-14: Lock analytics
As an operator
I want the totals for locked and unlocked time, the number of lock periods, the longest and the average lock, and the current status
So that I can report the result of a lock-on attempt

### US-15: Timeline of locked and unlocked periods
As an operator
I want a timeline under the video that shows where the target was locked, unlocked or lost
So that I can see the whole run at a glance and find the interesting moments

## Gherkin Acceptance Criteria

```gherkin
Feature: US-7 Draw the target box

  Scenario: AC-7.1 Drawing a box stores it in picture pixels
    Given REF-C is loaded and frame 1 is shown
    When I drag from picture point (592, 328) to (688, 392)
    Then the target box is stored as x 592, y 328, width 96, height 64 on frame 1
    And the box is drawn on the picture

  Scenario: AC-7.2 Dragging in the opposite direction gives the same box
    When I drag from (688, 392) to (592, 328)
    Then the target box is stored as x 592, y 328, width 96, height 64

  Scenario: AC-7.3 The box is in picture pixels whatever size the picture is shown at
    Given the 1280 x 720 picture is shown 640 pixels wide
    When I drag from screen point (296, 164) to (344, 196) of the picture area
    Then the target box is stored as x 592, y 328, width 96, height 64

  Scenario: AC-7.4 Redrawing or adjusting replaces the stored box
    Given a target box is stored
    When I draw a new box, or move the box, or drag one of its corners
    Then the stored box is the new one and the old one is gone

  Scenario: AC-7.5 The box can be drawn on any frame that is shown
    Given REF-C is loaded and frame 301 is shown
    When I draw a box
    Then it is stored for frame 301

  Scenario Outline: AC-7.6 (rejection) A box smaller than 8 pixels on a side is refused
    Given a target box is stored
    When I draw a box of <width> x <height> pixels
    Then <result>

    Examples:
      | width | height | result                                                              |
      | 8     | 8      | it is stored                                                        |
      | 7     | 40     | it is refused with found 7 x 40 and allowed at least 8 x 8; the earlier box is kept |
      | 40    | 7      | it is refused with found 40 x 7 and allowed at least 8 x 8; the earlier box is kept |

  Scenario: AC-7.7 (rejection) A box that leaves the picture is refused
    When a box reaching outside the 1280 x 720 picture is sent
    Then it is refused with a message that the box must lie inside the picture
    And drawing with the mouse cannot leave the picture: the box stops at the edge

  Scenario: AC-7.8 (rejection) No box can be drawn when no video is loaded
    Given no video is loaded
    Then drawing is not available and a box sent anyway is refused with "No video is loaded"
```

```gherkin
Feature: US-8 Track the target through the video

  Scenario: AC-8.1 The target of REF-C is followed on every frame
    Given REF-C is loaded and the target box (592, 328, 96, 64) is stored on frame 1
    When I start tracking and it finishes
    Then there is a box for each of the 900 frames
    And on every frame the box overlaps the true target (overlap ratio above 0.3)
    And the average overlap ratio over the video is at least 0.5

  Scenario: AC-8.2 Tracking starts at the frame of the target box
    Given a target box is stored on frame 31 of REF-A
    When tracking finishes
    Then frames 1 to 30 are "not tracked" and frames 31 to 90 have a result

  Scenario: AC-8.3 Progress is reported while tracking runs
    When tracking is running
    Then the frames done, the total, and the processing speed in frames per second are reported
    And the state changes from running to completed at the end

  Scenario: AC-8.4 The original video is unchanged by tracking
    When tracking has finished
    Then the stored video has the same SHA-256 checksum as the uploaded file

  Scenario: AC-8.5 A 30-second 720p video is tracked in under 60 seconds
    When REF-C is tracked from its first frame
    Then tracking completes in less than 60 seconds on a laptop CPU

  Scenario: AC-8.6 (rejection) Tracking cannot start without a target box
    Given a video is loaded and no target box is stored
    When I start tracking
    Then it is refused with a message to select a target first

  Scenario: AC-8.7 (rejection) Tracking cannot start without a video
    Given no video is loaded
    When tracking is requested
    Then it is refused with "No video is loaded"

  Scenario: AC-8.8 Replacing the video discards target, zone and results
    Given tracking has finished on one video
    When another video replaces it
    Then no target box, lock zone or tracking result of the first video remains
```

```gherkin
Feature: US-9 See the boxes over the video

  Scenario: AC-9.1 On a stopped frame the box of that frame is drawn
    Given tracking has finished
    When frame 45 is shown
    Then the box stored for frame 45 is drawn, in the colour of that frame's status

  Scenario Outline: AC-9.2 During playback the box belongs to the frame on screen
    Given a video at <fps> whose frames start at the times in its header
    When the player is at <seconds> seconds
    Then the box drawn is the one of frame <frame>

    Examples:
      | fps              | seconds | frame |
      | 30 constant      | 0.000   | 1     |
      | 30 constant      | 0.033   | 1     |
      | 30 constant      | 0.034   | 2     |
      | 30 constant      | 1.500   | 46    |
      | REF-V (variable) | 0.060   | 1     |
      | REF-V (variable) | 0.070   | 2     |
      | REF-V (variable) | 0.110   | 3     |

  Scenario: AC-9.3 Frame counter and processing speed are on screen while tracking
    When tracking is running
    Then the screen shows the frame being processed, the total, and the processing FPS

  Scenario: AC-9.4 (rejection) Play is not available without a video
    Given no video is loaded
    Then the play control cannot be used
```

```gherkin
Feature: US-10 Define the lock zone

  Scenario: AC-10.1 Drawing the zone stores it and shows it
    Given REF-C is loaded
    When I switch to zone drawing and drag from (440, 210) to (840, 510)
    Then the lock zone is stored as x 440, y 210, width 400, height 300
    And it is drawn on the picture in a style different from the target box

  Scenario: AC-10.2 The zone can be changed after tracking without tracking again
    Given tracking has finished with a lock zone
    When I draw a different lock zone
    Then every frame's status and the analytics follow the new zone
    And no tracking run is started

  Scenario: AC-10.3 Without a lock zone nothing is locked
    Given tracking has finished and no lock zone is stored
    Then no frame is LOCKED and there are no lock periods

  Scenario: AC-10.4 (rejection) A zone that is too small or leaves the picture is refused
    When a zone of 7 x 300 pixels, or one reaching outside the picture, is sent
    Then it is refused with found and allowed values, and the earlier zone is kept
```

```gherkin
Feature: US-11 Lock status and lock periods

  Scenario Outline: AC-11.1 LOCKED means the whole box is inside the zone; touching the edge counts as inside
    Given the lock zone is x 100, y 100, width 200, height 200
    When the target box is x <x>, y <y>, width <w>, height <h>
    Then the status is <status>

    Examples:
      | x   | y   | w   | h   | status   | why                                  |
      | 150 | 150 | 50  | 50  | LOCKED   | well inside                          |
      | 100 | 100 | 50  | 50  | LOCKED   | touching the top-left corner         |
      | 99  | 100 | 50  | 50  | UNLOCKED | 1 pixel past the left edge           |
      | 100 | 99  | 50  | 50  | UNLOCKED | 1 pixel past the top edge            |
      | 250 | 250 | 50  | 50  | LOCKED   | touching the bottom-right corner     |
      | 251 | 250 | 50  | 50  | UNLOCKED | 1 pixel past the right edge          |
      | 250 | 251 | 50  | 50  | UNLOCKED | 1 pixel past the bottom edge         |
      | 100 | 100 | 200 | 200 | LOCKED   | exactly the size of the zone         |
      | 90  | 90  | 220 | 220 | UNLOCKED | larger than the zone                 |
      | 400 | 400 | 50  | 50  | UNLOCKED | completely outside                   |

  Scenario: AC-11.2 Every continuous lock period of S-1 is recorded
    Given the status sequence S-1 at 30 frames per second
    Then the lock periods are frames 11 to 40 (1.000 s), 46 to 60 (0.500 s) and 64 to 70 (0.233 s)

  Scenario: AC-11.3 A period that reaches the last frame ends there
    Given 5 unlocked frames followed by 10 locked frames
    Then there is one lock period, frames 6 to 15

  Scenario: AC-11.4 A single locked frame is a lock period of one frame
    Given the statuses unlocked, locked, unlocked at 30 frames per second
    Then there is one lock period, frame 2 to 2, lasting 0.033 s

  Scenario: AC-11.5 (rejection) No locked frames, no periods
    Given only unlocked, lost or not-tracked frames, or no frames at all
    Then there are no lock periods
```

```gherkin
Feature: US-12 Detect that tracking is lost

  Scenario: AC-12.1 The tracker reporting failure means LOST
    Given tracking is running and the tracker reports failure on frame 41
    Then frame 41 is LOST with the reason "the tracker reported failure"
    And tracking stops and waits for a new target box

  Scenario Outline: AC-12.2 An area change of more than 50 % between two frames means LOST
    Given the box on one frame has an area of 10,000 square pixels
    When the box on the next frame has an area of <area>
    Then tracking is <result>

    Examples:
      | area   | result      | why                    |
      | 15,000 | not lost    | exactly 50 % larger    |
      | 15,001 | LOST        | just over 50 % larger  |
      | 5,000  | not lost    | exactly 50 % smaller   |
      | 4,999  | LOST        | just over 50 % smaller |
      | 10,000 | not lost    | unchanged              |

  Scenario: AC-12.3 A lock period in progress ends at the loss
    Given the target has been LOCKED from frame 21 and tracking is lost on frame 41
    Then that lock period is frames 21 to 40

  Scenario: AC-12.4 Frames after a loss count as LOST until the target is selected again
    Given tracking was lost on frame 41 of a 90-frame video and nothing else was done
    Then frames 41 to 90 are LOST

  Scenario: AC-12.5 The LOST status is shown clearly
    When tracking is lost
    Then the status shows LOST in red, with the frame number and the reason
```

```gherkin
Feature: US-13 Select the target again and resume

  Scenario: AC-13.1 Tracking resumes from the frame of the new box
    Given tracking was lost on frame 41
    When I draw a new target box on frame 51 and resume
    Then frames 1 to 40 keep their results, frames 41 to 50 stay LOST
    And frames 51 onward get new results

  Scenario: AC-13.2 Lock periods before and after the loss are separate
    Given the target was LOCKED on frames 21 to 40, lost on 41, selected again on 51 and LOCKED on 51 to 90
    Then the lock periods are frames 21 to 40 and frames 51 to 90

  Scenario: AC-13.3 The area rule starts afresh from the new box
    Given the box before the loss had an area of 10,000 and the new box has an area of 2,000
    When tracking resumes and the next box has an area of 2,100
    Then tracking is not lost

  Scenario: AC-13.4 Selecting on an earlier frame tracks again from there
    Given tracking has finished for frames 1 to 90
    When I draw a new target box on frame 31 and start
    Then frames 1 to 30 keep their results and frames 31 to 90 are replaced

  Scenario: AC-13.5 (rejection) A box that is refused does not resume tracking
    Given tracking is lost
    When I send a box smaller than 8 x 8 pixels
    Then it is refused, the state stays lost and nothing is tracked
```

```gherkin
Feature: US-14 Lock analytics

  Scenario: AC-14.1 The numbers for S-1 are exact
    Given the status sequence S-1 at 30 frames per second
    Then total locked is 52 frames, 1.733 s
    And total unlocked is 15 frames, 0.500 s
    And total lost is 3 frames, 0.100 s
    And the number of lock periods is 3
    And the longest lock is 30 frames, 1.000 s
    And the average lock is 17.333 frames, 0.578 s

  Scenario: AC-14.2 (rejection) With no lock periods nothing is divided by zero
    Given only unlocked frames, or no frames at all
    Then the number of lock periods is 0, and longest and average lock are 0 s

  Scenario: AC-14.3 Unlocked time leaves out lost and not-tracked frames
    Given 10 not-tracked, 20 unlocked and 30 lost frames at 30 frames per second
    Then total unlocked is 20 frames, 0.667 s, total lost is 30 frames and not tracked is 10 frames

  Scenario: AC-14.4 The current status is the status of the frame shown
    Given S-1 is the result
    Then frame 5 shows UNLOCKED, frame 20 LOCKED, frame 62 LOST

  Scenario: AC-14.5 At a non-whole frame rate durations use the exact rate
    Given 30 locked frames at 30000/1001 frames per second
    Then total locked is 1.001 s
```

```gherkin
Feature: US-15 Timeline of locked and unlocked periods

  Scenario: AC-15.1 The timeline of S-1 has one segment per run of equal status
    Given the status sequence S-1
    Then the segments are unlocked 1-10, locked 11-40, unlocked 41-45, locked 46-60, lost 61-63, locked 64-70
    And each segment's width is proportional to its number of frames

  Scenario: AC-15.2 Colours carry the status
    Then locked segments are green, unlocked amber, lost red and not-tracked grey

  Scenario: AC-15.3 The current frame is marked on the timeline
    When frame 30 of 70 is shown
    Then the position marker stands 29/70 of the way along the timeline

  Scenario: AC-15.4 (rejection) Before tracking there is nothing to colour
    Given a video is loaded and nothing has been tracked
    Then the timeline is a single not-tracked segment
```

**Non-functional requirements (brief §3, task "Requirements for both projects").** One command starts the application (`python run.py`); one command runs every automated test (`python run.py test`); large videos are never committed (`data/` is ignored, every committed test video is under 5 MB, the largest is 1.3 MB); invalid input never crashes the application (US-5, AC-7.6 to AC-7.8, AC-8.6, AC-8.7, AC-10.4, AC-13.5).

## Open Questions

All decided by the agent on the operator's instruction of 2026-11-20 to continue; none answered by the operator. Status `Resolved` here means "decided and applied", not "confirmed by the operator".

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| OQ-20 | On which frames may the target box be drawn: only the first, or any? | requirement-analysis | Resolved | Decided by the agent: any frame that is shown; the first frame is where a new video opens. Reason: re-selection after a loss (Feature 5) needs it anyway, so one rule covers both. |
| OQ-21 | Is there a smallest target box or lock zone? | requirement-analysis | Resolved | Decided by the agent: 8 × 8 pixels. Reason: a tracker needs some picture content to follow; smaller boxes are almost always mis-clicks. |
| OQ-22 | May a box reach outside the picture? | requirement-analysis | Resolved | Decided by the agent: no; it must lie fully inside, and drawing stops at the edge. Reason: pixels outside the picture do not exist for the tracker. |
| OQ-23 | Does touching the edge of the lock zone count as inside? | requirement-analysis | Resolved | Decided by the agent: yes. Reason: "inside" is the plain reading of "not outside"; the rule is then four ≤ / ≥ comparisons that are easy to test at the pixel. |
| OQ-24 | What shape is the lock zone, and how many are there? | requirement-analysis | Resolved | Decided by the agent: one rectangle with sides parallel to the picture. Reason: it is what the task describes ("a lock zone in the frame"). |
| OQ-25 | How long does a lock period of n frames last? | requirement-analysis | Resolved | Decided by the agent: n ÷ FPS seconds, with the exact frame rate. Reason: follows OQ-7 (times from frames and the average FPS) and gives the generated sequences exact answers. |
| OQ-26 | Does "total unlocked" include lost and not-tracked frames? | requirement-analysis | Resolved | Decided by the agent: no; lost and not-tracked are reported separately. Reason: the brief names three statuses; folding LOST into UNLOCKED would hide tracking failures. |
| OQ-27 | After a loss, does tracking stop and wait, or run on? | requirement-analysis | Resolved | Decided by the agent: it stops and waits; the frames from the loss onward count as LOST until a new box is given. Reason: the brief says the operator selects the target again and tracking resumes after that. |
| OQ-28 | What is the area change measured against, and is exactly 50 % a loss? | requirement-analysis | Resolved | Decided by the agent: against the box of the previous frame (after a selection: the selected box); exactly 50 % is not a loss. Reason: the task says "more than 50 % between two frames". |
| OQ-29 | Where may the target be selected again, and what happens to earlier results? | requirement-analysis | Resolved | Decided by the agent: on any frame; results before that frame are kept, from it on replaced; frames between a loss and a later selection stay LOST. Reason: one rule for first start, restart and recovery. |
| OQ-30 | When the lock zone changes after tracking, is tracking repeated? | requirement-analysis | Resolved | Decided by the agent: no; statuses and analytics are recomputed from the stored boxes. Reason: the boxes do not depend on the zone. |
| OQ-31 | Long runs: is progress shown, and can a run be cancelled (Stage 1 note for Feature 3)? | requirement-analysis | Resolved | Decided by the agent: progress, percentage and processing FPS are shown; starting again or replacing the video cancels a run; there is no separate cancel button. Reason: smallest answer that keeps a long run observable. |
| OQ-32 | What does tracking do at a frame that cannot be read (damaged file, OQ-8)? | requirement-analysis | Resolved | Decided by the agent: it stops there with the damage warning, and the frames from there on count as LOST. Reason: same behaviour as navigation (AC-5.7); nothing is invented for frames that do not exist. |
| OQ-33 | Is play/pause part of this scope (left out of Feature 1 by OQ-15)? | requirement-analysis | Resolved | Decided by the agent: yes, in US-9. Reason: boxes over the playing video are a core requirement of the task. |
| OQ-34 | Is clicking the timeline to jump to a frame required? | requirement-analysis | Resolved | Decided by the agent: no. Reason: not requested; the slider already moves to any frame. |
| OQ-35 | What is the "current tracking status" in the analytics? | requirement-analysis | Resolved | Decided by the agent: the status of the frame on screen, plus the state of the run (running, lost, completed). Reason: both are what an operator means by "current". |
