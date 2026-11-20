# Design Session — split from DESIGN.md at commit `c072f79`

> Linked from [DESIGN.md](./DESIGN.md). Requirements for three improvements the operator chose on 2026-11-20 after using the console with a real clip: a live target telemetry panel, Play waiting for tracking to finish, and a clearer timeline. The operator chose the features; the Open Questions below were **decided by the agent** to meet the deadline of 21 November and are marked so. Each can be overturned.

**Why these three.** In the operator's test with a real 727-frame clip, (1) pressing Play during tracking showed frames the tracker had not reached as "Not tracked", which looked like a fault; (2) the panels gave no numbers about the target itself; (3) the timeline had no time scale.

## User Stories

### US-16: Live target telemetry
As an operator
I want to see the tracked box's position, size and change in area for the frame on screen, and how far it is from the lock-zone edges
So that I can see why a frame is LOCKED, UNLOCKED or LOST

### US-17: Play waits for tracking
As an operator
I want Play to be unavailable while tracking runs, and frames the tracker has not reached to be called "Not tracked yet"
So that I do not mistake unprocessed frames for a lost target

### US-18: Timeline with a time scale
As an operator
I want time marks along the timeline and each lock period numbered on it
So that I can read when things happened and match periods with the analytics list

## Gherkin Acceptance Criteria

```gherkin
Feature: US-16 Live target telemetry

  Scenario: AC-16.1 Telemetry of a tracked frame
    Given the box on frame index 10 is x 180, y 292, width 96, height 66
    And the box on frame index 9 is x 172, y 292, width 96, height 66
    When frame index 10 is shown
    Then the telemetry shows centre 228, 325; size 96 × 66; area 6,336 px²; area change 0.0 %

  Scenario Outline: AC-16.2 Area change is measured against the previous frame, with the 50 % loss limit shown
    Given the previous frame's box has an area of 10,000 px²
    When the frame shown has a box of <area> px²
    Then the area change reads "<text>"

    Examples:
      | area   | text    |
      | 15,000 | +50.0 % |
      | 4,000  | −60.0 % |
      | 10,000 | 0.0 %   |

  Scenario: AC-16.3 No area change for the first frame of a run or after a loss
    Given the frame shown has a box but the frame before it has none (not tracked or lost)
    Then the area change reads "—"

  Scenario Outline: AC-16.4 Margin to the lock zone: the smallest distance from the box to a zone edge
    Given the lock zone is x 100, y 100, width 200, height 200
    When the frame shown has the box x <x>, y 150, width 50, height 50
    Then the zone margin reads "<text>"

    Examples:
      | x   | text              |
      | 150 | 50 px inside      |
      | 100 | 0 px inside       |
      | 99  | 1 px outside      |

  Scenario: AC-16.5 Without a box or a zone the telemetry says so
    Given the frame shown is not tracked or lost
    Then position, size, area and change read "—"
    And with no lock zone the margin reads "No lock zone"
```

```gherkin
Feature: US-17 Play waits for tracking

  Scenario: AC-17.1 Play is unavailable while tracking runs
    Given tracking is running
    Then the Play button cannot be used and says tracking must finish first
    When tracking completes, is lost or stops
    Then Play can be used again

  Scenario: AC-17.2 Frames the tracker has not reached are "Not tracked yet"
    Given tracking is running and has reached frame index 20
    When frame index 60 is shown
    Then the status reads "Not tracked yet"
    And frames before the start of the run still read "Not tracked"

  Scenario: AC-17.3 Starting tracking stops playback
    Given the video is playing
    When tracking is started
    Then playback stops on the frame on screen
```

```gherkin
Feature: US-18 Timeline with a time scale

  Scenario Outline: AC-18.1 Time marks at a readable step
    Given a video of <seconds> seconds
    Then the timeline has marks every <step>, at most 10 steps, starting at 0

    Examples:
      | seconds | step  |
      | 3.0     | 0.5 s |
      | 24.258  | 5 s   |
      | 600     | 1 min |

  Scenario: AC-18.2 Lock periods are numbered on the timeline in the same order as the analytics list
    Given lock periods 1 and 2 exist
    Then the locked stretches on the timeline are labelled 1 and 2
```

## Open Questions

All decided by the agent; none answered by the operator.

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| OQ-36 | Which telemetry values are shown? | requirement-analysis | Resolved | Decided by the agent: box centre, size, area, area change from the previous frame, and margin to the zone. Reason: together they explain the three statuses (area change → LOST, margin → LOCKED/UNLOCKED). |
| OQ-37 | Is the area change signed? | requirement-analysis | Resolved | Decided by the agent: yes, + for growth and − for shrinking, one decimal. Reason: the loss rule counts both directions; the sign shows which. |
| OQ-38 | What does "Play waits" mean exactly: disabled, or play only the processed part? | requirement-analysis | Resolved | Decided by the agent: disabled while tracking runs. Reason: simplest rule the operator can predict. |
| OQ-39 | How are time marks chosen? | requirement-analysis | Resolved | Decided by the agent: the smallest step from 0.5 s, 1 s, 2 s, 5 s, 10 s, 15 s, 30 s, 1, 2, 5, 10, 15, 30 min, 1 h that gives at most 10 steps. |
