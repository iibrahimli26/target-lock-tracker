# Design & Requirements Atlas

Central index of requirement analysis output for this repository. Individual sessions may split their work into `DESIGN_<commit-id>.md` files (see the [requirement-analysis skill](https://github.com/AADaoud/agentic-skill-keychain/tree/main/skills/requirement-analysis)) when this file grows too large; every such file must be listed below.

> **Project:** Target-Lock Video Tracker (KUAVA Newcomer Task, Project B). Requirements are written one feature at a time. Each feature is approved in `docs/APPROVAL_LOG.md` before its architecture starts.

## Linked Design Documents

| File | Scope / Topic | Started (commit) | Status |
|---|---|---|---|
| (this file) | Core — Feature 1: Video Upload and Validation, including metadata and frame-by-frame navigation (OQ-1) | — | Active |

## User Stories

**Feature 1 — Video Upload and Validation** · Session 2026-11-20 · Status: Pending Approval (see `docs/APPROVAL_LOG.md`)

- **Sources:** project brief §2 (Feature 1), §3, §7 (items 1 and 2), §9; KUAVA Newcomer Task, Project B ("Only MP4 (H.264) files need to be supported") and "Requirements for both projects" ("Invalid input shows a clear error message. It never crashes the app.").
- **Role:** *operator* means the person at the laptop who analyses drone footage. No login or user roles were requested.

| In scope this round | Out of scope this round |
|---|---|
| Choosing a video file and loading it into the application | Drawing, adjusting and storing the target box (Feature 2) |
| Checking file type, codec, file size, resolution and duration | Tracking, lock zone, loss detection, analytics (Features 3 to 6) |
| Clear error messages; the application keeps working after bad input | Visual styling of the screen (follows the brief's design direction; no behaviour) |
| Showing FPS, resolution, duration and total frames (confirmed by OQ-1) | |
| Showing the first frame and stepping through the video frame by frame (added by OQ-1) | |

Not requested in the brief or the task, and therefore **not included** (say so if you want any of them): drag-and-drop upload, an upload progress bar, login or multiple users, remembering the video after the application restarts, queueing several videos, a maximum response time for a frame step. Left out of this round by OQ-15: jumping to a typed frame number, first/last buttons, keyboard keys, larger steps, play/pause.

### US-1: Upload a drone video
As an operator
I want to choose an MP4 (H.264) video file from my computer and load it into the application
So that I can select a target and track it in the following steps

Traces to: brief §2 F1 "Accept MP4 videos encoded with H.264"; brief §2 F3 "Keep the original video unchanged".

### US-2: Refuse files that are not H.264 MP4
As an operator
I want the application to refuse any file that is not an MP4 containing H.264 video, and to tell me why
So that I do not lose time on footage the tracker cannot process

Traces to: brief §2 F1 "Validate file type, codec"; task "Only MP4 (H.264) files need to be supported".

### US-3: Enforce file size, resolution and duration limits
As an operator
I want the application to refuse videos outside the supported size, resolution and duration range, and to tell me the limit
So that processing time stays predictable on a laptop

Traces to: brief §2 F1 "Validate … resolution, duration, and file size"; brief §3 (30 s / 720p performance target).

### US-4: See the video's metadata after upload
As an operator
I want to see the frame rate, resolution, duration and total number of frames of the loaded video
So that I can confirm it is the right footage and trust the time measurements built on these numbers later

Traces to: brief §2 F1 "Extract video metadata, including FPS, resolution, duration, and total frames". Confirmed for this round by OQ-1 (2026-11-20).

### US-5: Clear errors and a stable application on bad input
As an operator
I want every failed upload to give me a readable error and leave the application working
So that I can correct the problem and try again without restarting anything

Traces to: brief §2 F1 "Display clear error messages for invalid files"; brief §3 "must handle invalid input without crashing".

### US-6: Step through the video frame by frame
As an operator
I want to move through the loaded video one frame at a time and see which frame I am on
So that I can inspect the footage precisely and find the exact frame I need

Traces to: brief §2 F1 "Support frame-by-frame navigation"; brief §7 item 2 "Frame extraction and video navigation"; brief §2 F2 "Display the first frame of the uploaded video" (the starting position). Added to this round by OQ-1 (2026-11-20).

## Gherkin Acceptance Criteria

**Reading notes**

- Scenario IDs (`AC-<story>.<n>`) exist so tests and the implementation log can point at them.
- Scenarios state which facts an error message must contain, not its full sentence. Since OQ-11: messages are in English, every problem that can be found is reported, and each message gives the value found and the value allowed (AC-5.6a to AC-5.6c). The exact wording is not fixed here.
- No scenario is left blocked: every Open Question raised in this round is resolved. Each limit has scenarios exactly at the limit, one step inside and one step outside.

**Reference test videos** (expected values come from how each file is made, never from what the application prints)

| ID | File | Properties |
|---|---|---|
| REF-A | `ref_720p.mp4` | MP4, one H.264 video track (8-bit, 4:2:0), 1280 × 720, constant 30 fps, 90 frames, 3.0 s, no audio, no rotation flag, under 5 MB |
| REF-B | `ref_360p.mp4` | Same kind of file: 640 × 360, constant 25 fps, 50 frames, 2.0 s |
| REF-C | `bench_720p_30s.mp4` | Same kind of file: 1280 × 720, constant 30 fps, 900 frames, 30.0 s, under 5 MB |
| REF-D | `long_720p_10min.mp4` | Same kind of file: 1280 × 720, constant 30 fps, 18,000 frames, 600.0 s, under 5 MB |
| REF-V | `vfr_720p.mp4` | Like REF-A but with a variable frame rate: 1280 × 720, 60 frames, 3.0 s; frames alternately last 1/15 s and 1/30 s, so the average is exactly 20 fps |
| REF-X | `damaged_720p.mp4` | REF-A with its index intact but the later part of its picture data cut off: the header still says 90 frames and 3.0 s, but only an early part can be read (at least the first 10 frames can, the last 30 cannot) |

In every reference video each frame is individually identifiable: it carries a marker whose position depends only on the frame's place in the video, so a test can tell exactly which frame is on screen.

```gherkin
Feature: US-1 Upload a drone video

  Scenario: AC-1.1 A valid H.264 MP4 is accepted
    Given the application is running and no video is loaded
    When I upload REF-A ("ref_720p.mp4")
    Then the upload is reported as accepted
    And "ref_720p.mp4" is shown as the loaded video
    And no error message is shown

  Scenario: AC-1.2 The video the application works with is identical to my file
    Given I have uploaded REF-A successfully
    When the video held by the application is compared with the file I chose
    Then both have the same size in bytes and the same SHA-256 checksum

  Scenario: AC-1.3 A file name with spaces and non-English letters is accepted
    Given a copy of REF-A named "İHA görüntüsü 01.mp4"
    When I upload it
    Then the upload is accepted
    And the name "İHA görüntüsü 01.mp4" is shown exactly as written

  Scenario: AC-1.4 Cancelling the file chooser changes nothing
    Given no video is loaded
    When I open the file chooser and close it without choosing a file
    Then no upload starts
    And no error message is shown
    And the application still shows that no video is loaded

  Scenario: AC-1.5 (rejection) An upload without a file is refused
    Given the application is running and no video is loaded
    When an upload is submitted that contains no file
    Then it is refused with an error message saying that no file was provided
    And no video is loaded
```

```gherkin
Feature: US-2 Refuse files that are not H.264 MP4

  Scenario: AC-2.1 An MP4 file with H.264 video passes the type and codec checks
    Given no video is loaded
    When I upload REF-B ("ref_360p.mp4")
    Then the upload is accepted
    And no file-type error and no codec error is shown

  Scenario Outline: AC-2.2 (rejection) A file that is not a video is refused
    Given no video is loaded
    When I upload "<file>"
    Then the upload is refused
    And the error message says the file is not an MP4 video
    And no video is loaded

    Examples:
      | file       |
      | photo.png  |
      | notes.txt  |
      | report.pdf |

  Scenario Outline: AC-2.3 (rejection) A video in another container format is refused
    Given no video is loaded
    When I upload "<file>", a playable video in the <container> format
    Then the upload is refused
    And the error message says only MP4 (H.264) files are supported
    And no video is loaded

    Examples:
      | file      | container |
      | clip.avi  | AVI       |
      | clip.mkv  | Matroska  |
      | clip.webm | WebM      |

  Scenario Outline: AC-2.4 (rejection) An MP4 file whose video is not H.264 is refused
    Given no video is loaded
    When I upload "<file>", an MP4 file whose video track is encoded with <codec>
    Then the upload is refused
    And the error message says the video codec is not H.264
    And no video is loaded

    Examples:
      | file           | codec         |
      | clip_hevc.mp4  | H.265 (HEVC)  |
      | clip_mpeg4.mp4 | MPEG-4 Part 2 |

  Scenario: AC-2.5 (rejection) A non-video file renamed to ".mp4" is refused
    Given "fake.mp4" is a plain text file whose name was changed to end in ".mp4"
    When I upload "fake.mp4"
    Then the upload is refused
    And the error message says the file is not a valid MP4 video
    And no video is loaded

  Scenario: AC-2.6 (rejection) An MP4 file with no video track is refused
    Given "audio_only.mp4" is an MP4 file that contains only an audio track
    When I upload "audio_only.mp4"
    Then the upload is refused
    And the error message says no H.264 video was found in the file
    And no video is loaded

  # From OQ-5: the file name plays no part; only the content is checked.
  # QuickTime-type content with H.264 video is accepted like MP4.
  Scenario Outline: AC-2.7a H.264 MP4 content is accepted whatever the file is called
    Given no video is loaded
    And "<file>" is a byte-for-byte copy of REF-A under another name
    When I upload "<file>"
    Then the upload is accepted
    And "<file>" is shown as the loaded video

    Examples:
      | file         | why                                       |
      | DJI_0001.MP4 | upper-case extension, as drones name files |
      | clip.m4v     | another video extension                   |
      | clip.mov     | QuickTime extension                       |
      | clip         | no extension                              |
      | clip.txt     | extension of a different kind of file     |

  Scenario: AC-2.7b A QuickTime file with H.264 video is accepted
    Given no video is loaded
    And "phone.mov" is a QuickTime file with one H.264 video track that passes every other check
    When I upload "phone.mov"
    Then the upload is accepted
    And no file-type error and no codec error is shown

  Scenario: AC-2.7c (rejection) A QuickTime file whose video is not H.264 is refused
    Given no video is loaded
    And "phone_hevc.mov" is a QuickTime file whose video track is encoded with H.265 (HEVC)
    When I upload "phone_hevc.mov"
    Then the upload is refused
    And the error message says the video codec is not H.264
    And no video is loaded

  # From OQ-6: only H.264 with 8-bit colour and 4:2:0 colour sampling is
  # accepted, because that is what web browsers play reliably.
  Scenario: AC-2.8a 8-bit 4:2:0 video with full colour range is accepted
    Given no video is loaded
    And "h264_fullrange.mp4" is an MP4 file with H.264 video in 8-bit colour, 4:2:0, full colour range, that passes every other check
    When I upload "h264_fullrange.mp4"
    Then the upload is accepted
    And no colour-format error is shown

  Scenario Outline: AC-2.8b (rejection) H.264 in a colour format browsers cannot play is refused
    Given no video is loaded
    And "<file>" is an MP4 file with H.264 video in <format> that passes every other check
    When I upload "<file>"
    Then the upload is refused
    And the error message says the video's colour format is not supported
    And no video is loaded

    Examples:
      | file           | format               |
      | h264_10bit.mp4 | 10-bit colour, 4:2:0 |
      | h264_422.mp4   | 8-bit colour, 4:2:2  |
      | h264_444.mp4   | 8-bit colour, 4:4:4  |

  # From OQ-12: sound and data tracks are ignored; a file with two or more
  # picture (video) tracks is refused.
  Scenario Outline: AC-2.9a Sound and data tracks are ignored
    Given no video is loaded
    And "<file>" is REF-A with <extra> added
    When I upload "<file>"
    Then the upload is accepted
    And the metadata is that of the picture track: 1280 x 720 pixels, 30 frames per second, 90 frames, 3.0 seconds

    Examples:
      | file                | extra                                              |
      | with_sound.mp4      | a sound track lasting 4.0 seconds                  |
      | with_data.mp4       | a data track                                       |
      | with_sound_data.mp4 | a sound track lasting 4.0 seconds and a data track |

  Scenario Outline: AC-2.9b (rejection) A file with more than one picture track is refused
    Given no video is loaded
    And "<file>" is REF-A with <extra> added
    When I upload "<file>"
    Then the upload is refused
    And the error message says the file has more than one video track, with 2 as found and 1 as allowed
    And no video is loaded

    Examples:
      | file             | extra                                              |
      | two_videos.mp4   | a second H.264 video track                         |
      | with_preview.mp4 | a preview picture stored as a second picture track |

  # From OQ-19: 3GP files are treated like MP4; the codec rule is the same.
  Scenario: AC-2.10a A 3GP file with H.264 video is accepted
    Given no video is loaded
    And "old_phone.3gp" is a 3GP file with one H.264 video track that passes every other check
    When I upload "old_phone.3gp"
    Then the upload is accepted
    And no file-type error and no codec error is shown

  Scenario: AC-2.10b (rejection) A 3GP file whose video is not H.264 is refused
    Given no video is loaded
    And "old_phone_h263.3gp" is a 3GP file whose video track is encoded with H.263
    When I upload "old_phone_h263.3gp"
    Then the upload is refused
    And the error message gives codec H.263 as found and H.264 as allowed
    And no video is loaded
```


```gherkin
Feature: US-3 Enforce file size, resolution and duration limits

  # Firm because brief §3 requires a 30-second 720p video to be processed,
  # so the limits, whatever they become, must admit it.
  Scenario: AC-3.1 The benchmark-sized video is within all limits
    Given no video is loaded
    When I upload REF-C ("bench_720p_30s.mp4", 1280 x 720, 30.0 s)
    Then the upload is accepted
    And no size, resolution or duration error is shown

  Scenario: AC-3.2 (rejection) An empty file is refused
    Given "empty.mp4" is a file of 0 bytes
    When I upload "empty.mp4"
    Then the upload is refused
    And the error message says the file is empty
    And no video is loaded

  # Limit from OQ-2: 1 GB = 1024 MB = 1,073,741,824 bytes (1 MB = 1,048,576 bytes).
  # A file of exactly this size is accepted.
  Scenario Outline: AC-3.3a A file at or just under the maximum size is accepted
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of exactly <bytes> bytes that passes every other check
    When I upload "<file>"
    Then the upload is accepted
    And no file-size error is shown

    Examples:
      | file            | bytes         |
      | under_limit.mp4 | 1,073,741,823 |
      | at_limit.mp4    | 1,073,741,824 |

  Scenario: AC-3.3b (rejection) A file one byte over the maximum size is refused
    Given no video is loaded
    And "over_limit.mp4" is an H.264 MP4 file of exactly 1,073,741,825 bytes that passes every other check
    When I upload "over_limit.mp4"
    Then the upload is refused
    And the error message says the file is larger than the maximum allowed size
    And no video is loaded

  # Duration rules from OQ-3: no maximum; minimum 2 frames.
  # The frame count is the one written in the file header (OQ-8).
  Scenario: AC-3.4a A video far longer than the benchmark is accepted
    Given no video is loaded
    When I upload REF-D ("long_720p_10min.mp4", 600.0 s, 20 times the benchmark length)
    Then the upload is accepted
    And no duration error is shown

  Scenario Outline: AC-3.4b A video with the minimum number of frames, or one more, is accepted
    Given no video is loaded
    And "<file>" is an H.264 MP4 file with exactly <frames> frames that passes every other check
    When I upload "<file>"
    Then the upload is accepted
    And no duration error is shown

    Examples:
      | file             | frames |
      | two_frames.mp4   | 2      |
      | three_frames.mp4 | 3      |

  Scenario: AC-3.4c (rejection) A video with only one frame is refused
    Given no video is loaded
    And "one_frame.mp4" is an H.264 MP4 file with exactly 1 frame that passes every other check
    When I upload "one_frame.mp4"
    Then the upload is refused
    And the error message says the video is too short
    And no video is loaded

  # Resolution rules from OQ-4 and OQ-18:
  #   - maximum: width x height at most 921,600 pixels (the pixels in 1280 x 720)
  #   - orientation: width at least equal to height (landscape or square)
  #   - no minimum
  # Sizes are the stored sizes. A file with a rotation note is refused in any case (AC-4.6).
  # H.264 with 4:2:0 colour has even dimensions, so neighbouring sizes are 2 px apart.
  Scenario Outline: AC-3.5a A landscape video at or just inside the limits is accepted
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of <width> x <height> pixels that passes every other check
    When I upload "<file>"
    Then the upload is accepted
    And no resolution error is shown

    Examples:
      | file             | width | height | why                              |
      | res_1280x720.mp4 | 1280  | 720    | exactly the maximum              |
      | res_1278x720.mp4 | 1278  | 720    | one step narrower                |
      | res_1280x718.mp4 | 1280  | 718    | one step lower                   |
      | res_722x720.mp4  | 722   | 720    | landscape by the smallest margin |

  Scenario Outline: AC-3.5b (rejection) A video larger than the maximum resolution is refused
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of <width> x <height> pixels that passes every other check
    When I upload "<file>"
    Then the upload is refused
    And the error message says the resolution is larger than the maximum allowed
    And no video is loaded

    Examples:
      | file              | width | height | why             |
      | res_1282x720.mp4  | 1282  | 720    | one step wider  |
      | res_1280x722.mp4  | 1280  | 722    | one step taller |
      | res_1920x1080.mp4 | 1920  | 1080   | 1080p           |

  Scenario: AC-3.5c A very small landscape video is accepted
    Given no video is loaded
    And "res_32x18.mp4" is an H.264 MP4 file of 32 x 18 pixels that passes every other check
    When I upload "res_32x18.mp4"
    Then the upload is accepted
    And no resolution error is shown

  Scenario Outline: AC-3.5d (rejection) A portrait video is refused
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of <width> x <height> pixels that passes every other check
    When I upload "<file>"
    Then the upload is refused
    And the error message says only landscape videos are supported
    And no video is loaded

    Examples:
      | file            | width | height | why                             |
      | res_360x640.mp4 | 360   | 640    | clearly portrait                |
      | res_718x720.mp4 | 718   | 720    | portrait by the smallest margin |

  Scenario Outline: AC-3.5e Square and wide videos within the pixel maximum are accepted
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of <width> x <height> pixels that passes every other check
    When I upload "<file>"
    Then the upload is accepted
    And no resolution error is shown

    Examples:
      | file             | width | height | pixels  | why                                     |
      | res_720x720.mp4  | 720   | 720    | 518,400 | square                                  |
      | res_960x960.mp4  | 960   | 960    | 921,600 | square, exactly the maximum             |
      | res_1440x480.mp4 | 1440  | 480    | 691,200 | wider than 1280 px, within the maximum  |
      | res_1600x576.mp4 | 1600  | 576    | 921,600 | wider than 1280 px, exactly the maximum |

  Scenario Outline: AC-3.5f (rejection) Square and wide videos over the pixel maximum are refused
    Given no video is loaded
    And "<file>" is an H.264 MP4 file of <width> x <height> pixels that passes every other check
    When I upload "<file>"
    Then the upload is refused
    And the error message says the resolution is larger than the maximum allowed
    And no video is loaded

    Examples:
      | file             | width | height | pixels  | why                   |
      | res_962x962.mp4  | 962   | 962    | 925,444 | square, one step over |
      | res_1602x576.mp4 | 1602  | 576    | 922,752 | wide, one step over   |
```


```gherkin
Feature: US-4 See the video's metadata after upload

  Scenario: AC-4.1 Metadata of the 720p reference video is shown
    Given no video is loaded
    When I upload REF-A ("ref_720p.mp4")
    Then the metadata shows a resolution of 1280 x 720 pixels
    And a frame rate of 30 frames per second
    And a total of 90 frames
    And a duration of 3.0 seconds

  # Second file with different values: proves the numbers are read, not fixed.
  Scenario: AC-4.2 Metadata follows the file
    Given no video is loaded
    When I upload REF-B ("ref_360p.mp4")
    Then the metadata shows a resolution of 640 x 360 pixels
    And a frame rate of 25 frames per second
    And a total of 50 frames
    And a duration of 2.0 seconds

  Scenario: AC-4.3 (rejection) No metadata is shown for a refused file
    Given no video is loaded
    When I upload "notes.txt"
    Then the upload is refused
    And no frame rate, resolution, duration or frame count is shown

  # From OQ-7: variable-frame-rate videos are accepted, the average FPS is
  # shown (total frames / duration), and a warning says times are approximate.
  Scenario: AC-4.4a A variable-frame-rate video is accepted with a warning
    Given no video is loaded
    When I upload REF-V ("vfr_720p.mp4")
    Then the upload is accepted
    And the metadata shows a frame rate of 20 frames per second, the average for this file
    And a total of 60 frames and a duration of 3.0 seconds
    And a warning says the frame rate is variable and that times are approximate

  Scenario: AC-4.4b A constant-frame-rate video gets no such warning
    Given no video is loaded
    When I upload REF-A ("ref_720p.mp4")
    Then the upload is accepted
    And no variable-frame-rate warning is shown

  # From OQ-8: total frames and duration are the numbers written in the file
  # header. The video is not read in full at upload.
  Scenario: AC-4.5 A file whose header promises more frames than can be read shows the header's numbers
    Given no video is loaded
    When I upload REF-X ("damaged_720p.mp4")
    Then the upload is accepted
    And the metadata shows a total of 90 frames and a duration of 3.0 seconds

  # From OQ-9: a video saved with a "turn when showing" note (rotation
  # metadata) is refused, whatever the angle. REF-A, which has no such note,
  # is accepted (AC-1.1).
  Scenario Outline: AC-4.6 (rejection) A video saved with a rotation note is refused
    Given no video is loaded
    And "<file>" is a copy of REF-A saved with a note to turn the picture by <angle> degrees when showing
    When I upload "<file>"
    Then the upload is refused
    And the error message says rotated videos are not supported
    And no video is loaded

    Examples:
      | file        | angle |
      | rot_90.mp4  | 90    |
      | rot_180.mp4 | 180   |
      | rot_270.mp4 | 270   |

  # From OQ-13: the frame rate is always written with two decimals; the
  # duration is written as a clock, minutes:seconds.milliseconds, rounded to
  # the nearest millisecond, with hours in front from one hour on.
  # In this format AC-4.1 reads 30.00 and 00:03.000, AC-4.2 reads 25.00 and
  # 00:02.000, AC-4.4a reads 20.00 and 00:03.000.
  Scenario Outline: AC-4.7a Frame rates are written with two decimals
    When a frame rate of <fps> frames per second is shown
    Then it reads "<text>"

    Examples:
      | fps          | text  |
      | 30           | 30.00 |
      | 25           | 25.00 |
      | 30000 / 1001 | 29.97 |
      | 24000 / 1001 | 23.98 |
      | 60000 / 1001 | 59.94 |

  Scenario Outline: AC-4.7b Durations are written as a clock
    When a duration of <seconds> seconds is shown
    Then it reads "<text>"

    Examples:
      | seconds   | text        | why                             |
      | 3.0       | 00:03.000   | short clip                      |
      | 0.0666667 | 00:00.067   | 2 frames at 30 fps, rounded     |
      | 59.999    | 00:59.999   | just under one minute           |
      | 60.0      | 01:00.000   | exactly one minute              |
      | 600.0     | 10:00.000   | REF-D                           |
      | 3599.999  | 59:59.999   | just under one hour             |
      | 3600.0    | 1:00:00.000 | exactly one hour                |
      | 3725.5    | 1:02:05.500 | over one hour                   |

  Scenario: AC-4.7c A 29.97 fps video shows 29.97 and its exact duration
    Given no video is loaded
    And "ntsc_720p.mp4" is like REF-A but recorded at 30000/1001 frames per second, so its 90 frames last 3.003 s
    When I upload "ntsc_720p.mp4"
    Then the metadata shows a frame rate of "29.97"
    And a duration of "00:03.003"
    And a total of 90 frames
```


```gherkin
Feature: US-5 Clear errors and a stable application on bad input

  Scenario: AC-5.1 A valid upload works straight after a refused one
    Given I uploaded "notes.txt" and it was refused with an error message
    When I upload REF-A ("ref_720p.mp4") without restarting the application
    Then the upload is accepted
    And the earlier error message is no longer shown

  Scenario: AC-5.2 (rejection) A cut-off MP4 file is refused
    Given "truncated.mp4" is REF-A with the end of the file cut off,
      so that its index (the part that lists where every frame is) is missing
    When I upload "truncated.mp4"
    Then the upload is refused
    And the error message says the file is damaged or incomplete
    And no video is loaded

  Scenario: AC-5.3 (rejection) Error messages are readable and hide internals
    When any upload is refused
    Then the error message is a plain sentence that names the check that failed
    And it contains no stack trace, no exception name and no server file path

  Scenario: AC-5.4 (rejection) An interrupted upload leaves nothing half-loaded
    Given no video is loaded and an upload is in progress
    When the upload is interrupted before it finishes
    Then no video is loaded
    And a new upload of REF-A is accepted

  Scenario: AC-5.5 The application survives a series of bad files
    Given the application is running
    When I upload every invalid file from AC-2.2 to AC-2.6, AC-3.2 and AC-5.2, one after another
    Then each one is refused with its own error message
    And the application is still running and accepts REF-A afterwards

  # From OQ-8: REF-X passes upload because only the header is read (unlike
  # AC-5.2, where the index itself is missing). The damage shows when a frame
  # that cannot be read is asked for, and the operator is then warned.
  Scenario: AC-5.7 (rejection) A frame that cannot be read gives a warning, not a crash
    Given REF-X ("damaged_720p.mp4") is loaded and the first frame is shown
    When I step forward until a frame cannot be read
    Then a warning says the file is damaged and this frame cannot be read
    And the application keeps running
    And I can still step backward to frames that can be read

  # From OQ-10: one video is loaded at a time. Uploading another asks for
  # confirmation; a refused new file leaves the loaded video in place; if a
  # second upload starts while one is still running, the one started last wins.
  Scenario: AC-5.8a Replacing the loaded video after confirming
    Given REF-A ("ref_720p.mp4") is loaded
    When I upload REF-B ("ref_360p.mp4")
    Then I am asked to confirm replacing the loaded video
    When I confirm
    Then REF-B is the loaded video
    And the metadata shows 640 x 360 pixels, 25 frames per second, 50 frames and 2.0 seconds
    And the picture shown is the first frame of REF-B

  Scenario: AC-5.8b Declining the confirmation keeps everything as it was
    Given REF-A is loaded and I have stepped forward to the 10th frame
    When I upload REF-B and decline the confirmation
    Then REF-A is still the loaded video
    And the picture shown is still the 10th frame of REF-A

  Scenario: AC-5.8c (rejection) A refused new file leaves the loaded video in place
    Given REF-A is loaded and I have stepped forward to the 10th frame
    When I upload "notes.txt", confirming the replacement if I am asked
    Then the upload is refused with an error message
    And REF-A is still the loaded video, with its metadata unchanged
    And the picture shown is still the 10th frame of REF-A

  Scenario: AC-5.8d When a second upload starts during an upload, the one started last wins
    Given no video is loaded and an upload of REF-C is in progress
    When I start an upload of REF-B before the first has finished
    Then, once the application has settled, REF-B is the loaded video
    And the metadata and the picture shown belong to REF-B
    And nothing of REF-C is shown

  Scenario: AC-5.8e No confirmation is asked when nothing is loaded
    Given no video is loaded
    When I upload REF-A
    Then I am not asked to confirm anything
    And REF-A is the loaded video

  # From OQ-11: every problem that can be found is reported at once; each
  # message gives the value found and the value allowed; messages are in English.
  Scenario: AC-5.6a (rejection) A file with several problems gets one message per problem
    Given no video is loaded
    And "three_problems.mp4" is an H.264 MP4 file of 1920 x 1080 pixels with 1 frame, saved with a 180-degree rotation note
    When I upload "three_problems.mp4"
    Then the upload is refused
    And one message says the resolution is too large, with 2,073,600 pixels (1920 x 1080) as found and 921,600 pixels as the maximum
    And one message says the video is too short, with 1 frame as found and 2 frames as the minimum
    And one message says rotated videos are not supported, with 180 degrees as found
    And no other problem is reported
    And no video is loaded

  # Applies to every check that compares a value with a limit or an allowed
  # set. A file that is not a video at all has no meaningful "found" value;
  # its message says so and names what is allowed (AC-2.2, AC-2.5).
  Scenario Outline: AC-5.6b (rejection) Each message gives the value found and the value allowed
    Given no video is loaded
    When I upload "<file>"
    Then the upload is refused
    And the error message gives <found> as found and <allowed> as allowed

    Examples:
      | file              | found                          | allowed                    |
      | clip_hevc.mp4     | codec H.265 (HEVC)             | H.264                      |
      | h264_10bit.mp4    | 10-bit colour, 4:2:0           | 8-bit colour, 4:2:0        |
      | over_limit.mp4    | 1,073,741,825 bytes            | 1,073,741,824 bytes (1 GB) |
      | res_1920x1080.mp4 | 2,073,600 pixels (1920 x 1080) | 921,600 pixels             |
      | res_360x640.mp4   | 360 x 640, portrait            | landscape or square        |
      | one_frame.mp4     | 1 frame                        | at least 2 frames          |
      | rot_90.mp4        | rotation of 90 degrees         | no rotation                |

  Scenario: AC-5.6c Messages are in English whatever the browser's language
    Given the browser's language is set to Turkish
    And no video is loaded
    When I upload "res_1920x1080.mp4"
    Then the upload is refused
    And the error message is the same English text as when the browser's language is English
    And its numbers are written the English way (2,073,600 and not 2.073.600)
```


```gherkin
Feature: US-6 Step through the video frame by frame

  # Ordinal words (first, second, 90th) name frames by their place in the
  # video. On screen the first frame is number 1 (OQ-16, AC-6.10a).
  Scenario: AC-6.1 The first frame is shown after a successful upload
    Given no video is loaded
    When I upload REF-A ("ref_720p.mp4")
    Then the picture shown is the first frame of REF-A
    And the position indicator shows the first of 90 frames

  Scenario: AC-6.2 Stepping forward shows the next frame
    Given REF-A is loaded and the first frame is shown
    When I step forward one frame
    Then the picture shown is the second frame of REF-A
    And the position indicator shows the second of 90 frames

  Scenario: AC-6.3 Stepping backward shows the previous frame
    Given REF-A is loaded and I have stepped forward 5 times from the first frame
    When I step backward one frame
    Then the picture shown is the fifth frame of REF-A
    And the position indicator shows the fifth of 90 frames

  Scenario: AC-6.4 Every frame can be reached, in order, with no skips or repeats
    Given REF-A is loaded and the first frame is shown
    When I step forward 89 times, waiting for each picture
    Then each step showed the next frame of REF-A, none skipped and none shown twice
    And the picture shown at the end is the 90th and last frame of REF-A

  Scenario: AC-6.5 Going forward and back returns to exactly the same frame
    Given REF-A is loaded and I have stepped forward to the 40th frame
    When I step forward 10 times and then backward 10 times
    Then the picture shown is the 40th frame of REF-A
    And the position indicator shows the 40th of 90 frames

  Scenario: AC-6.6 Picture and position indicator agree after rapid stepping
    Given REF-A is loaded and the first frame is shown
    When I step forward 30 times in quick succession without waiting
    Then, once the display has settled, the picture shown is the frame named by the position indicator

  Scenario: AC-6.7 (rejection) Navigation is unavailable when no video is loaded
    Given no video is loaded
    When I look at the navigation controls
    Then they cannot be used and no picture or position is shown
    And a request for a frame made anyway is refused with a message saying no video is loaded

  Scenario: AC-6.8 (rejection) Navigation stays unavailable after a refused upload
    Given no video is loaded
    When I upload "notes.txt" and it is refused
    Then no picture is shown
    And the navigation controls cannot be used

  # From OQ-7: variable-frame-rate videos are accepted, so stepping has to
  # work on them frame by frame, whatever length of time each frame lasts.
  Scenario: AC-6.12a Every frame of a variable-frame-rate video can be reached in order
    Given REF-V is loaded and the first frame is shown
    When I step forward 59 times, waiting for each picture
    Then each step showed the next frame of REF-V, none skipped and none shown twice
    And the picture shown at the end is the 60th and last frame of REF-V

  # From OQ-15: besides single steps there is a slider. Its left end is the
  # first frame, its right end is the last frame, and it has one position
  # for every frame.
  Scenario: AC-6.9a Moving the slider shows the frame at that position
    Given REF-A is loaded and the first frame is shown
    When I move the slider to the position of the 45th frame
    Then the picture shown is the 45th frame of REF-A
    And the position indicator shows the 45th of 90 frames

  Scenario Outline: AC-6.9b The ends of the slider are the first and the last frame
    Given REF-A is loaded and I have moved the slider to the 45th frame
    When I move the slider to its <end> end
    Then the picture shown is the <frame> frame of REF-A

    Examples:
      | end   | frame |
      | left  | first |
      | right | 90th  |

  Scenario: AC-6.9c The slider follows single steps
    Given REF-A is loaded and the first frame is shown
    When I step forward 10 times
    Then the slider stands at the position of the 11th frame

  Scenario: AC-6.9d Stepping continues from where the slider was put
    Given REF-A is loaded and I have moved the slider to the 45th frame
    When I step forward one frame
    Then the picture shown is the 46th frame of REF-A
    And the position indicator shows the 46th of 90 frames

  Scenario: AC-6.9e Picture and slider agree after fast dragging
    Given REF-A is loaded and the first frame is shown
    When I drag the slider quickly across many positions and let go
    Then, once the display has settled, the picture shown is the frame at the slider's position
    And the position indicator names the same frame

  Scenario: AC-6.9f (rejection) The slider cannot be used when no video is loaded
    Given no video is loaded
    When I look at the slider
    Then it cannot be moved

  Scenario: AC-6.9g (rejection) Moving the slider onto a frame that cannot be read gives a warning
    Given REF-X ("damaged_720p.mp4") is loaded and the first frame is shown
    When I move the slider to its right end
    Then a warning says the file is damaged and this frame cannot be read
    And the application keeps running

  # From OQ-16: on screen frames are counted from 1, and the time of the
  # current frame is shown next to its number. A frame's time is the moment
  # it starts: (frame number - 1) / FPS, written as a clock (OQ-13).
  Scenario Outline: AC-6.10a The position shows the frame number, counted from 1, and the frame's time
    Given REF-A is loaded (30 frames per second, 90 frames)
    When the <which> frame is shown
    Then the position indicator reads frame <number> of 90
    And the time shown is "<time>"

    Examples:
      | which | number | time      |
      | first | 1      | 00:00.000 |
      | 2nd   | 2      | 00:00.033 |
      | 45th  | 45     | 00:01.467 |
      | 90th  | 90     | 00:02.967 |

  Scenario: AC-6.10b The frame's time follows the video's frame rate
    Given REF-B is loaded (25 frames per second, 50 frames)
    When the 50th frame is shown
    Then the position indicator reads frame 50 of 50
    And the time shown is "00:01.960"

  # Follows OQ-7: for such a video times are approximate and use the average.
  Scenario: AC-6.10c In a variable-frame-rate video the frame's time uses the average frame rate
    Given REF-V is loaded (average 20 frames per second, 60 frames)
    When the 60th frame is shown
    Then the position indicator reads frame 60 of 60
    And the time shown is "00:02.950"

  # From OQ-17: at either end the position stays, and the step button that
  # would leave the video is shown as inactive. After the warning for a frame
  # that cannot be read, the position stays on the last frame shown.
  Scenario: AC-6.11a (rejection) No step back from the first frame
    Given REF-A is loaded and the first frame is shown
    Then the step-back button is shown as inactive and the step-forward button as active
    When I try to step back anyway
    Then the picture shown is still the first frame of REF-A
    And the position indicator still reads frame 1 of 90

  Scenario: AC-6.11b (rejection) No step forward from the last frame
    Given REF-A is loaded and I have moved the slider to its right end
    Then the step-forward button is shown as inactive and the step-back button as active
    When I try to step forward anyway
    Then the picture shown is still the 90th frame of REF-A
    And the position indicator still reads frame 90 of 90

  Scenario Outline: AC-6.11c One step away from an end both buttons are active
    Given REF-A is loaded
    When the <which> frame is shown
    Then the step-back button and the step-forward button are both shown as active

    Examples:
      | which |
      | 2nd   |
      | 89th  |

  Scenario: AC-6.11d After the warning the position stays on the last frame shown
    Given REF-X ("damaged_720p.mp4") is loaded and the first frame is shown
    When I step forward until the warning says a frame cannot be read
    Then the picture shown is the last frame that could be read
    And the position indicator and the slider both name that frame

  Scenario: AC-6.11e The slider returns after being moved onto a frame that cannot be read
    Given REF-X is loaded and I have stepped forward to the 5th frame
    When I move the slider to its right end and the warning appears
    Then the picture shown is still the 5th frame of REF-X
    And the position indicator reads frame 5 of 90
    And the slider stands at the position of the 5th frame again
```


## Edge Cases & Failure Scenarios

| # | Case | How it happens in real use | Covered by |
|---|---|---|---|
| EC-1 | Wrong kind of file (image, text, PDF) | Wrong file picked in the chooser | AC-2.2 |
| EC-2 | Video in another container (AVI, MKV, WebM) | Footage exported from another tool | AC-2.3 |
| EC-3 | MP4 with H.265/HEVC video | Many newer drones and phones record HEVC by default | AC-2.4 |
| EC-4 | Non-video file renamed to `.mp4` | Mistake, or deliberate bad input | AC-2.5 |
| EC-5 | MP4 with audio only | Audio export with an `.mp4` name | AC-2.6 |
| EC-6 | Empty file (0 bytes) | Failed copy from an SD card | AC-3.2 |
| EC-7 | Recording cut off, index missing | Battery died or the copy was interrupted | AC-5.2 |
| EC-8 | Header readable, frames damaged later | Partly corrupted SD card | AC-4.5, AC-5.7 |
| EC-9 | Unusual extension: `.MP4`, `.m4v`, `.mov`, `.txt`, none | DJI drones name files `DJI_0001.MP4`; files get renamed | AC-2.7a |
| EC-10 | H.264 the browser cannot play | 10-bit or 4:2:2 recording modes | AC-2.8b |
| EC-11 | Variable frame rate | Phone recordings, screen recordings | AC-4.4a, AC-4.4b, AC-6.12a |
| EC-12 | Header frame count differs from decodable frames | Edited or damaged files | AC-4.5, AC-5.7, AC-6.11d |
| EC-13 | Video stored with a rotation note (90°, 180°, 270°) | Phone held upright or upside down | AC-4.6 |
| EC-14 | Extra tracks (audio, telemetry, second video, preview picture) | Normal for camera and drone files | AC-2.9a, AC-2.9b |
| EC-15 | Too large, too long, too short, too big or too small a picture | Raw 4K footage, long flights, tiny clips | AC-3.3a, AC-3.3b (size); AC-3.4a to AC-3.4c (length); AC-3.5a to AC-3.5c, AC-3.5f (picture size) |
| EC-16 | Frame rate that is not a whole number (29.97) | Common camera setting | AC-4.7a, AC-4.7c |
| EC-17 | File names with spaces or non-English letters | Normal file naming | AC-1.3 |
| EC-18 | Upload interrupted | Tab closed or page reloaded mid-upload | AC-5.4 |
| EC-19 | Upload while a video is loaded; two uploads at once | Double click, second browser tab | AC-5.8a to AC-5.8e |
| EC-20 | Several things wrong with one file | e.g. a 1080p phone clip filmed upside down | AC-5.6a |
| EC-21 | Upload with no file; chooser cancelled | Empty submit, changed mind | AC-1.4, AC-1.5 |
| EC-22 | Stepping when no video is loaded, or after a refused upload | Controls clicked too early | AC-6.7, AC-6.8 |
| EC-23 | Picture is one frame off after many steps, or after going forward and back | Seeking by time lands on a neighbouring frame | AC-6.4, AC-6.5 |
| EC-24 | Picture and frame number disagree | Step key held down; pictures arrive out of order | AC-6.6 |
| EC-25 | Stepping past either end of the video | Step button pressed again at the end | AC-6.11a to AC-6.11c |
| EC-26 | Invalid frame number typed (0, negative, past the end, text, decimal) | Typing mistake | Does not arise in this round: no typed frame number (OQ-15) |
| EC-27 | Very long video (many minutes) | Whole flight recorded in one file | AC-3.4a |
| EC-28 | Video with a single frame | Still image saved as MP4, recording stopped at once | AC-3.4c |
| EC-29 | Portrait video stored upright (no rotation flag) | Vertical export for social media; the task document's example clip is portrait | AC-3.5d |
| EC-30 | 1080p or 4K footage straight from the drone | Default recording settings | AC-3.5b |
| EC-31 | Square video | Cropped export | AC-3.5e, AC-3.5f |
| EC-32 | Very wide video (wider than 1280 px, few pixels in total) | Cinema-format or cropped export | AC-3.5e, AC-3.5f |
| EC-33 | QuickTime file (`.mov`) | iPhones and some cameras write QuickTime, often with HEVC video | AC-2.7b, AC-2.7c |
| EC-34 | 3GP phone video (H.264, or the older H.263) | Older phones | AC-2.10a, AC-2.10b |
| EC-35 | Ordinary 8-bit 4:2:0 video saved with full colour range | Some phones and action cameras | AC-2.8a |
| EC-36 | Browser set to another language (numbers written 2.073.600) | Operator's computer is set to Turkish | AC-5.6c |
| EC-37 | Sound track longer than the picture | Recording software pads the sound | AC-2.9a |
| EC-38 | Cover picture kept in the file's tag area, not as a track | Downloaded or tagged videos | Stage 2 note 12 |
| EC-39 | Duration of one hour or more | Long recording at a low data rate | AC-4.7b |
| EC-40 | Slider dragged quickly; pictures arrive out of order | Normal use on a long video | AC-6.9e |
| EC-41 | Slider moved onto a frame that cannot be read | Damaged file (REF-X) | AC-6.9g, AC-6.11e |

**Notes handed to Stage 2 (not decisions):** (1) a file name can contain path parts such as `../`; how the application names what it stores is an architecture matter. (2) How the reference videos are produced (generated when tests run, or small committed files) is open; the under-5 MB repository rule applies either way. In a trial, a file like REF-D came to about 1 MB but took about a minute to generate. (3) The size limit is 1,073,741,824 bytes (OQ-2). Its boundary tests need files of about 1 GB that are created during the test run and never committed, and uploads of that size should not have to fit in memory; how to keep these tests fast is an architecture matter. (4) How a frame gets on screen (the browser seeking inside the video, or single frames delivered by the backend) decides how exact and how fast stepping is; the options need a benefits/drawbacks comparison. (5) Accepted pictures are not all 16:9: square and very wide pictures pass (OQ-18), so the player area and box coordinates cannot assume one shape. (6) Because the file name plays no part (OQ-5), the file chooser must not hide or block files by extension. (7) QuickTime-type files are accepted (OQ-5); whether the browser's player shows them in every supported browser has to be verified. OQ-6 refuses files the browser cannot play, so a QuickTime file that turns out not to play would need a decision. (8) AC-4.4a and AC-4.4b use clear cases only. The exact rule that separates constant from variable frame rate (how much difference between frame lengths counts) is not fixed here and has to be raised as an architecture question, with its boundary defined. (9) The header's numbers are trusted and the video is not read in full at upload (OQ-8). A file can still be checked for completeness without reading every frame (does the index point past the end of the file?); whether to do that is open. (10) Whether the confirmation of OQ-10 is asked before the new file is sent or after it has passed its checks is not fixed; AC-5.8c holds either way. (11) The exact wording of each message is not fixed (OQ-11 fixes its content and language). One list of all messages should be defined so that the application and the tests use the same text. (12) Some files keep a cover picture in their tag area rather than as a track, and some tools still list it as an extra picture stream. The scenarios do not cover this case; how picture tracks are counted, and whether such a cover counts, has to be raised as an architecture question. (13) On screen frames are numbered from 1 (OQ-16); OpenCV numbers them from 0. Where the two meet should be one clearly defined place, the same for the counter, the slider, the timeline and later the lock report. (14) A file with a rotation note is always refused (AC-4.6). Whether its orientation is additionally judged on the stored or on the shown picture is not specified; AC-5.6a uses a 180-degree note, for which both give the same answer.

**Note handed to Feature 3's requirements round (not a decision):** with no maximum duration (OQ-3), processing a long video can take a long time. Whether progress has to be shown and whether a run can be cancelled should be asked there. Because the header's frame count is trusted (OQ-8), tracking can also meet a frame that cannot be read before the promised end; what tracking and the lock times do then should be asked there as well. Play/pause was left out of this round (OQ-15) and has to be specified there, where playback with boxes is defined.

**Note handed to Features 2 to 6 (not a decision):** replacing the loaded video (OQ-10) also discards whatever later features attach to it (target box, tracking results, lock periods). Each of those features should state this in its own requirements.

## Open Questions

| ID | Question | Raised By | Status | Resolution |
|---|---|---|---|---|
| OQ-1 | Scope of this round. Brief §2 lists "extract video metadata" and "frame-by-frame navigation" under Feature 1, but §7 makes "frame extraction and video navigation" a separate priority 2 and §9 says "Video Upload and Validation ONLY". Is metadata display (US-4) part of this round, and is frame-by-frame navigation deferred to round 2? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "Metadata and navigation both now". Applied: US-4 confirmed for this round; US-6 and AC-6.1 to AC-6.8 added; scope table updated; OQ-15 to OQ-17 raised. |
| OQ-2 | What is the maximum accepted file size, and is a file of exactly that size accepted? (The 5 MB rule in brief §3 is for test videos in the repository, not for uploads.) | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: maximum size "1 GB"; 1 MB means "1,048,576 bytes (1024 × 1024)"; a file of exactly the limit is "Accepted". Applied: limit = 1024 MB = 1,073,741,824 bytes, inclusive; AC-3.3a and AC-3.3b written. |
| OQ-3 | What are the maximum and minimum accepted durations, and is a video of exactly the limit accepted? (30 s is the performance benchmark, not a stated limit.) | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: maximum duration "No maximum"; minimum length "At least 2 frames"; a video of exactly the maximum is "Accepted" (not applicable, because there is no maximum). Applied: AC-3.4a to AC-3.4c written; REF-D added; note for Feature 3 recorded. |
| OQ-4 | What are the maximum and minimum accepted resolutions, and are portrait videos (taller than wide) accepted? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: maximum resolution "Up to and including 1280 × 720"; portrait videos "No, landscape only"; minimum resolution "No minimum". Applied: AC-3.5a to AC-3.5d written; OQ-18 raised for square videos and for how the maximum is applied. |
| OQ-5 | How is "this is an MP4" decided: by the file's content, by its extension, or both? Is valid H.264 MP4 content accepted when named `DJI_0001.MP4`, `clip.m4v`, `clip.mov` or with no extension? Is a QuickTime `.mov` file with H.264 video accepted? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: file names "Any name; only the content counts"; QuickTime-type content with H.264 video is "Accepted like MP4". Applied: AC-2.7a to AC-2.7c written; OQ-19 raised for 3GP files. |
| OQ-6 | Some valid H.264 MP4 files cannot be played by web browsers (10-bit colour, 4:2:2 or 4:4:4). Refuse them, accept them with a warning, or accept them and prepare a browser-friendly working copy? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "do it yourself as wrote in the docx". Read as handing this choice to the agent, which the task document allows on condition that the decision is written down. Decision written down: refuse with a clear message; only H.264 with 8-bit colour and 4:2:0 sampling is accepted. Reason: see the OQ-6 brief. The operator can overturn this before approving. Applied: AC-2.8a and AC-2.8b written. |
| OQ-7 | Variable-frame-rate videos: refuse, accept with a warning, or accept fully? Which FPS value is shown for them? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "Accept, show average FPS, warn". Applied: AC-4.4a, AC-4.4b and AC-6.12a written; REF-V added; note 8 handed to Stage 2. |
| OQ-8 | Which number is the truth for total frames and duration: the one written in the file header, or the count of frames that can actually be decoded? What happens when they differ? Does validation read only the header, or decode the whole video to catch damage in the middle? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20. First reply: "i dont know"; the question was explained again with an example. Then: which count to use, "The header's number (fast)"; if the app counts and the two numbers differ, "Show a warning". Applied: total frames and duration come from the header and the video is not read in full at upload; because nothing is counted at upload, the warning is shown at the moment the application meets a frame it cannot read. AC-4.5 and AC-5.7 written; REF-X added; OQ-17 extended; notes for Stage 2 and Feature 3 recorded. |
| OQ-9 | Rotated videos (picture stored sideways plus a "rotate" flag): is resolution shown and validated as displayed (e.g. 1080 × 1920) or as stored (1920 × 1080), or are such videos refused? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "Refuse videos with a turn note". Applied: AC-4.6 written; the navigation stub for rotated videos (AC-6.12b) is no longer needed and was removed. |
| OQ-10 | Is exactly one video loaded at a time? If a video is loaded and a new one is uploaded: replace silently, ask for confirmation, or refuse until the first is cleared? If the new upload is refused, does the previous video stay loaded? What if two uploads start at the same time? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: a new upload while a video is loaded, "Ask me to confirm first"; if the new file is refused, the loaded video "Stays loaded"; a second upload started while one is still uploading is "Allowed; the last one wins". Applied: AC-5.8a to AC-5.8e written ("last" taken as the upload that was started last); notes 10 and the note for Features 2 to 6 recorded. |
| OQ-11 | Error reporting. When a file fails several checks, show only the first failure or all of them? Must a message include the detected and the allowed value (e.g. "codec HEVC found; only H.264 is supported")? English only, or Turkish as well? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: several problems, "All problems it can find"; numbers in the message, "Yes, include found and allowed values"; language, "English only". Applied: AC-5.6a to AC-5.6c written; reading note on messages updated; note 11 handed to Stage 2. |
| OQ-12 | Extra tracks. Are audio and data/telemetry tracks accepted and ignored? If a file has more than one video track, is the first used or is the file refused? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "Ignore sound/data; refuse 2+ picture tracks". Applied: AC-2.9a and AC-2.9b written; note 12 handed to Stage 2. |
| OQ-13 | Metadata display format: how many decimals for FPS (29.97 vs 30), and duration as seconds (12.345 s) or as clock time (00:12.345)? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "[No preference]" for the frame rate and "[No preference]" for the duration. Read as leaving both choices to the agent, which the task document allows on condition that the decision is written down. Decision written down: frame rate always with two decimals; duration as a clock, minutes:seconds.milliseconds, rounded to the nearest millisecond, with hours in front from one hour on. Reason: see the OQ-13 brief. The operator can overturn this before approving. Applied: AC-4.7a to AC-4.7c written. |
| OQ-14 | Process question, blocks Stage 3 only. Path of the implementation log: the brief says `docs/IMPLEMENTATION_LOG.md`; the senior-developer skill writes `docs/implementation/IMPLEMENTATION_LOG.md`. Which one is used? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "[No preference]". Read as leaving the choice to the agent, which the task document allows on condition that the decision is written down. Decision written down: `docs/implementation/IMPLEMENTATION_LOG.md`, the path the senior-developer skill writes. Reason: see the OQ-14 brief. The operator can overturn this before approving. Applied: no scenario is affected; the path takes effect in Stage 3. |
| OQ-15 | Navigation controls. Stepping one frame forward and one frame back is given. Which other ways of moving are required in this round: jump to a typed frame number, first/last frame buttons, a slider to drag, larger steps (e.g. 10 frames), keyboard keys, play/pause? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "[No preference]". Read as leaving the choice to the agent, which the task document allows on condition that the decision is written down. Decision written down: single steps plus a slider with one position for every frame; no typed frame number, first/last buttons, keyboard keys, larger steps or play/pause in this round. Reason: see the OQ-15 brief. The operator can overturn this before approving. Applied: AC-6.9a to AC-6.9g written; play/pause noted for Feature 3. |
| OQ-16 | Frame numbers on screen: is the first frame called 1 (as in the task document's example image, "Frame 1/358") or 0 (as OpenCV counts)? Is the time of the current frame shown next to its number? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: what the first frame is called, "[No preference]"; time next to the number, "Yes, show the time". The first part is read as leaving the choice to the agent, which the task document allows on condition that the decision is written down. Decision written down: on screen frames are counted from 1. Reason: see the OQ-16 brief. The operator can overturn this before approving. Applied: AC-6.10a to AC-6.10c written; note 13 handed to Stage 2. |
| OQ-17 | Ends of the video: when I step back on the first frame or forward on the last frame, does the position stay where it is, or wrap around to the other end? Added 2026-11-20 after OQ-8: in a damaged file the last frame that can be read comes before the header's last frame; after the warning of AC-5.7, where does the position stand? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "[No preference]" for the ends of the video and "[No preference]" for the position after the warning. Read as leaving both choices to the agent, which the task document allows on condition that the decision is written down. Decision written down: at either end the position stays and the step button that would leave the video is shown as inactive; after the warning the position stays on the last frame shown. Reason: see the OQ-17 brief. The operator can overturn this before approving. Applied: AC-6.11a to AC-6.11e written. |
| OQ-18 | Follow-up to OQ-4. (a) Is a square video (width equal to height, e.g. 720 × 720) accepted under "landscape only"? (b) Is the maximum applied to each side separately (width at most 1280 and height at most 720), or to the total number of pixels (at most 921,600), which would accept e.g. 1440 × 480? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: a square video is "Accepted"; the maximum is applied "By pixel count: at most 921,600 pixels". Applied: rule is width × height at most 921,600 and width at least equal to height; AC-3.5e and AC-3.5f written; AC-3.5a to AC-3.5d checked against the rule and unchanged. |
| OQ-19 | Follow-up to OQ-5. 3GP phone videos (`.3gp`, `.3g2`) belong to the same family of formats as MP4 and QuickTime. With H.264 video, are they accepted like MP4 or refused? | requirement-analysis | Resolved | Operator, in chat, 2026-11-20: "[No preference]". Read as leaving the choice to the agent, which the task document allows on condition that the decision is written down. Decision written down: 3GP files with H.264 video are accepted like MP4. Reason: see the OQ-19 brief. The operator can overturn this before approving. Applied: AC-2.10a and AC-2.10b written. |

### Open Question briefs

Background for each question, in plain language, with the realistic options. These are not decisions; the operator decides and the answer is copied into the Resolution column above.

**OQ-1 — Round scope.** The pipeline handles one feature per round, and the brief names the same items under two headings. Validation already has to read frame rate, resolution and duration in order to check them, so showing them adds little. Stepping through frames needs a way to fetch and show single frames, which is new work. *Options:* (a) metadata now, navigation in round 2; (b) both now; (c) neither now, US-4 moves to round 2. *Answered 2026-11-20: (b).*

**OQ-2 — File size.** A size limit protects the laptop's disk and memory and gives a quick, clear refusal. Set too low, it refuses real footage: 30 seconds of 720p is typically tens of MB, and a clip straight from a drone at 1080p or 4K can be several hundred MB. *Options:* (a) about 100 MB; (b) about 500 MB; (c) another value. Also needed: is a file of exactly the limit accepted? *Answered 2026-11-20: 1 GB (1,073,741,824 bytes), exactly the limit accepted.*

**OQ-3 — Duration.** Processing time grows with length. The stated target is 30 s of video in under 60 s; at that pace a 5-minute video could take up to 10 minutes. At the short end, tracking compares one frame with the next, so a one-frame file cannot be tracked. *Options, maximum:* 60 s, 120 s, 5 min, or no maximum. *Options, minimum:* at least 2 frames, or at least 1 second. *Answered 2026-11-20: no maximum; at least 2 frames.*

**OQ-4 — Resolution.** More pixels mean slower tracking: 1080p has 2.25 times the pixels of 720p, 4K has 9 times. The performance target is stated only for 720p. The example in the task document is a portrait clip (433 × 712), so not all footage is landscape. *Options, maximum:* 1280 × 720, 1920 × 1080, or 3840 × 2160. *Options, minimum:* none, or a floor such as 320 × 240. *Portrait:* yes or no. Whether large videos are shrunk internally for speed is a Stage 2 matter. *Answered 2026-11-20: up to and including 1280 × 720; landscape only; no minimum.*

**OQ-5 — Recognising an MP4.** The extension is only part of the name and can be wrong; the content is what the tracker reads. Checking content alone accepts a correct video with an odd name. Also requiring the extension is stricter and easy to explain, but refuses drone files named `.MP4` unless upper and lower case are treated alike. MP4 and QuickTime (`.mov`) are sibling formats that tools often report as one family, so separating them needs an explicit rule. *Options:* (a) content only; (b) content plus extension `.mp4`, ignoring case; (c) as (b), also allowing `.m4v` and `.mov`. *Answered 2026-11-20: content only; QuickTime-type content accepted like MP4.*

**OQ-6 — H.264 the browser cannot play.** The task's tip is to play the original file in the browser and draw the boxes over it. Browsers reliably play ordinary H.264 (8-bit colour, 4:2:0). Some cameras record H.264 with 10-bit colour or 4:2:2; OpenCV can read these but browsers generally cannot, which would leave boxes drawn over a blank player. *Options:* (a) refuse with a clear message; (b) accept and warn; (c) accept and create a browser-friendly working copy (the original stays untouched; costs processing time and complexity). *Decided 2026-11-20 by delegation to the agent: (a).* *Reason in plain words:* the application shows the video with the browser's own player and draws the boxes on top. A file that the player cannot show would leave the operator with boxes over an empty picture and no way to select the target, so it is refused at upload with a clear message instead of failing later. Converting such files was not chosen because it adds a processing step and waiting time for a kind of file that is rare in drone footage.

**OQ-7 — Variable frame rate.** In a constant-frame-rate video every frame lasts the same time, so time = frame number ÷ FPS. In a variable-frame-rate video (common from phones and screen recorders) frames last different times, "FPS" is only an average, and that formula drifts. Lock durations are reported in seconds later, so this decides how accurate they can be. *Options:* (a) refuse; (b) accept, show the average FPS and warn that times are approximate; (c) accept and use each frame's own timestamp (most accurate, more work in tracking and analytics). *Answered 2026-11-20: (b).*

**OQ-8 — Truth for frame count and duration.** The header's frame count is a claim; the frames that decode are the reality. They differ in damaged or unusually edited files. Total frames drives the frame counter, the timeline and lock durations. Counting for real means reading the whole file once at upload, which takes longer than reading the header. *Options:* (a) trust the header (fast, can be wrong); (b) count decodable frames and show that number, accepting the file even if the header disagrees; (c) as (b), but warn or refuse on a mismatch. *Answered 2026-11-20: (a), with a warning when a frame turns out to be unreadable.*

**OQ-9 — Rotation.** A phone held upright stores a sideways picture plus a flag saying "rotate when showing". Browsers apply the flag; OpenCV may or may not, depending on version and settings. If the two disagree, a box drawn in the browser lands on the wrong place for the tracker. Fixing one coordinate system now prevents that in Features 2 to 4. *Options:* (a) always use the as-displayed orientation; (b) always use the as-stored orientation; (c) refuse rotated videos. *Answered 2026-11-20: (c).*

**OQ-10 — One video at a time.** Later features attach a target box, tracking results and lock periods to the loaded video; replacing the video discards them. *Options for a new upload while one is loaded:* (a) replace silently; (b) ask for confirmation first; (c) refuse until the current video is cleared. *Answered 2026-11-20: (b); a refused new file leaves the loaded video in place; of two overlapping uploads the last wins.*

**OQ-11 — Error reporting.** "Clear" has to be testable. Showing only the first failure is simpler, and some checks cannot run once an earlier one fails (a text file has no codec). Showing all failures saves repeat attempts. Including the detected value helps the operator fix the file. *Options:* first failure or all; with or without detected and allowed values; English, or English and Turkish. *Answered 2026-11-20: all problems; with values; English only.*

**OQ-12 — Extra tracks.** Most real videos have sound, and drone files often carry a telemetry data track; tracking needs only the picture. More than one video track is rare. *Options:* (a) ignore all non-video tracks and use the first video track; (b) ignore audio and data, refuse files with more than one video track; (c) accept only files with exactly one video track and nothing else (refuses most footage with sound). *Answered 2026-11-20: (b).*

**OQ-13 — Display format.** Many cameras record 29.97 frames per second (exactly 30000 ÷ 1001), not 30. The acceptance criteria need one exact expected text to be testable. *Options, FPS:* whole number, 2 decimals, or 3 decimals. *Options, duration:* seconds with milliseconds, or minutes:seconds.milliseconds. *Decided 2026-11-20 by delegation to the agent: two decimals; clock.* *Reason in plain words:* two decimals is the fewest that shows 29.97 correctly, and using the same number of decimals for every video keeps the panel steady. A clock stays readable for long videos, which matter because there is no maximum duration, and it matches what video players show.

**OQ-14 — Implementation log path.** Two instructions disagree, and the reviewers will look for the file. *Options:* (a) `docs/IMPLEMENTATION_LOG.md` as in the brief; (b) `docs/implementation/IMPLEMENTATION_LOG.md` as the skill writes it. *Decided 2026-11-20 by delegation to the agent: (b).* *Reason in plain words:* the skill creates and updates the file at that path, the skill repository's README lists it there, and other skills link to it, so the reviewers will look for it there. The brief's section 8 names a different path for this one file; this entry records why the skill's path is used.

**OQ-15 — Navigation controls.** "Frame-by-frame" guarantees single steps only. A 30-second video has about 900 frames, so reaching the middle with single steps takes hundreds of presses; a slider or a jump box solves that, but each control adds behaviour to specify and test (a typed number needs rules for 0, negatives, numbers past the end, text). Playback is needed at the latest when tracking results are shown in Feature 3. *Options:* (a) single steps only; (b) single steps, jump to a frame number, first/last; (c) as (b) plus a slider; (d) everything, including keyboard keys and play/pause. *Decided 2026-11-20 by delegation to the agent: single steps plus a slider.* *Reason in plain words:* with no maximum duration a video can have tens of thousands of frames, so single steps alone are not usable. A slider is the one control that reaches any part of the video quickly and needs the fewest new rules; a typed frame number would need rules for every kind of wrong input. Play/pause belongs with Feature 3, where playback with boxes is specified.

**OQ-16 — Frame numbers on screen.** People count from 1; most programming tools, OpenCV included, count from 0. Whatever is chosen has to be the same on the frame counter, the timeline and the lock-period report, because mixing the two produces off-by-one errors. How frames are numbered inside the code is a Stage 2 matter. *Options:* (a) show 1 to N; (b) show 0 to N − 1. *Time next to the number:* yes or no. *Numbering decided 2026-11-20 by delegation to the agent: (a). Time answered by the operator: yes.* *Reason for counting from 1, in plain words:* it is how an operator counts, and it is what the task document's own example image shows ("Frame 1/358"). The last frame then carries the same number as the total, so "90 of 90" reads naturally.

**OQ-17 — Ends of the video.** Staying put makes "I am at the end" obvious. Wrapping around lets the operator loop, but makes it easy to lose one's place. *Options:* (a) stay, and show the control as inactive; (b) stay, with no visible change; (c) wrap around to the other end. *Decided 2026-11-20 by delegation to the agent: (a); after the warning for an unreadable frame the position stays on the last frame shown.* *Reason in plain words:* an inactive button tells the operator "this is the end" before they press it, and it matches the slider, which cannot go past its ends either. Staying on the last frame shown keeps the picture and the frame number in agreement and always leaves a valid picture on screen.

**OQ-18 — Square videos and how the maximum is applied.** "Landscape only" draws a line between wider-than-tall and taller-than-wide; a square picture sits exactly on that line, so the rule has to say which side it falls on. Separately, "at most 1280 × 720" can be read per side or as a pixel budget. The two readings agree for ordinary 16:9 footage and differ only for unusually wide pictures: 1440 × 480 is wider than 1280 px but has fewer pixels than 1280 × 720. Tracking cost follows the pixel count; a per-side rule is simpler to state and to explain. *Options (a):* square accepted, or square refused. *Options (b):* per side, or by pixel count. *Answered 2026-11-20: square accepted; by pixel count.*

**OQ-19 — 3GP files.** MP4, QuickTime and 3GP share one underlying layout, and inspection tools report them as a single family; each file carries a short label saying which member it is. Accepting every member that holds H.264 video is the simplest rule. Refusing 3GP needs a check of that label and its own tests. *Options:* (a) accepted like MP4; (b) refused. *Decided 2026-11-20 by delegation to the agent: (a).* *Reason in plain words:* the operator already chose that only the content counts and that QuickTime files are accepted like MP4 (OQ-5). Treating the third member of the same family differently would need an extra check for no benefit; the codec rule still refuses 3GP files that do not hold H.264.
