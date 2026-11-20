LEARNING

OQ-8: Which number is the truth for total frames and duration: the header's, or the frames that can really be read?

What it means:
It asks whether the video information should be based on the numbers written in the file header or on the frames the program can actually read.

Your final answer:
The program will use the numbers from the video header as the main source of information. However, if some frames cannot be read, it will show a warning to inform the user.

Where it was decided:
DESIGN.md


OQ-6: What happens to H.264 files the browser cannot play (10-bit, 4:2:2, 4:4:4)?

What it means:
It asks what the program should do when a video uses a format that the browser does not support.

Your final answer:
The program will refuse to process these files and inform the user that the video format is not supported.

Where it was decided:
DESIGN.md


OQ-7: What happens to variable-frame-rate videos?

What it means:
It asks how the program handles videos where the time between frames is not always the same.

Your final answer:
The program will accept variable-frame-rate videos and calculate their average FPS. It will also display a warning to inform the user that the video has a variable frame rate.

Where it was decided:
DESIGN.md


OQ-18: Is the maximum resolution applied per side or as a pixel count?

What it means:
It asks how the maximum video resolution limit is calculated: by checking the width and height separately or by checking the total number of pixels.

Your final answer:
The maximum resolution will be determined by the total pixel count rather than limiting the width and height separately.

Where it was decided:
DESIGN.md


OQ-9: What happens to videos saved with a "turn when showing" note?

What it means:
It asks whether the program should automatically rotate videos that contain rotation information in their metadata.

Your final answer:
The program will refuse videos that contain rotation metadata instead of trying to rotate them automatically.

Where it was decided:
DESIGN.md


OQ-13: How are frame rate and duration written on screen?

What it means:
It asks how FPS and video duration should be displayed so users can easily understand them.

Your final answer:
FPS will be displayed with two decimal places, and the duration will be displayed in a clock format.

Where it was decided:
DESIGN.md


OQ-15: Which ways of moving through the video are needed?

What it means:
It asks how users should be able to move between different parts of the video.

Your final answer:
Users will be able to navigate through the video using step-by-step frame controls and a slider to move to different positions.

Where it was decided:
DESIGN.md


OQ-23: Does touching the edge of the lock zone count as inside?

What it means:
It asks whether an object that touches the boundary of the restricted area should be considered inside or outside it.

Your final answer:
Touching the boundary of the lock zone will count as being inside the zone.

Where it was decided:
DESIGN_e64c4e2.md


OQ-28: What is the 50% area change measured against, and is exactly 50% a loss?

What it means:
It asks how the program measures changes in an object's bounding box and whether a change of exactly 50% should be considered a loss.

Your final answer:
The area change will be measured against the bounding box from the previous frame. A change must be greater than 50% to count as a loss, so exactly 50% will not be considered a loss.

Where it was decided:
DESIGN_e64c4e2.md


AQ-3: What exactly separates constant from variable frame rate?

What it means:
It asks how the program decides whether a video has a constant or variable frame rate.

Your final answer:
The program will compare the timing between frames to determine whether the frame rate is constant or variable, using the defined threshold in the architecture.

Where it was decided:
ARCHITECTURE.md


AQ-11: Which OpenCV tracker, and why?

What it means:
It asks which tracking algorithm should be used to follow an object and why it is the best choice.

Your final answer:
The program will use the CSRT tracker because it provides good tracking accuracy. Its performance will also be evaluated through measurements.

Where it was decided:
ARCHITECTURE_e64c4e2.md


AQ-2: How does a frame get on screen when stopped and when playing?

What it means:
It asks how the program displays video frames when the user pauses the video or when it is playing.

Your final answer:
When the video is paused, the program will display the selected frame directly. During playback, frames will be displayed continuously according to the playback process and timing.

Where it was decided:
ARCHITECTURE.md