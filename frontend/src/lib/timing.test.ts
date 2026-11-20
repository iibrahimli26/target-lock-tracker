// AC-9.2 (which frame is on screen during playback), AC-6.10a-c (frame number and time).
import { describe, expect, it } from "vitest";
import { formatClock } from "./format";
import { frameAtTime, frameNumber, frameStartTimes, frameTime } from "./timing";

const constant30 = { timescale: 15360, runs: [[90, 512]] as [number, number][] };
// REF-V: frames alternately last 1024 and 512 ticks of 1/15360 s
const refV = { timescale: 15360, runs: Array.from({ length: 60 }, (_, k) => [1, k % 2 === 0 ? 1024 : 512] as [number, number]) };

describe("AC-9.2 during playback the box belongs to the frame on screen", () => {
  const cfr = frameStartTimes(constant30), vfr = frameStartTimes(refV);
  it.each([[0.0, 1], [0.033, 1], [0.034, 2], [1.5, 46], [2.999, 90], [99, 90], [-1, 1]])(
    "30 fps constant: at %f s frame %i is on screen", (seconds, frame) => expect(frameNumber(frameAtTime(cfr, seconds))).toBe(frame));
  it.each([[0.06, 1], [0.07, 2], [0.11, 3], [0.0, 1], [2.96, 60]])(
    "REF-V: at %f s frame %i is on screen", (seconds, frame) => expect(frameNumber(frameAtTime(vfr, seconds))).toBe(frame));
  it("lists one start time per frame", () => {
    expect(cfr.length).toBe(90);
    expect(vfr.length).toBe(60);
    expect(vfr[1]).toBeCloseTo(1024 / 15360, 9);
    expect(vfr[2]).toBeCloseTo(1536 / 15360, 9);
  });
});

describe("AC-6.10 the position shows the frame number from 1 and the frame's time", () => {
  it("counts frames from 1 on screen (OQ-16)", () => {
    expect(frameNumber(0)).toBe(1);
    expect(frameNumber(89)).toBe(90);
  });
  it.each([[0, "00:00.000"], [1, "00:00.033"], [44, "00:01.467"], [89, "00:02.967"]])(
    "AC-6.10a REF-A: frame index %i starts at %s", (index, text) => expect(formatClock(frameTime(index, 30, 1))).toBe(text));
  it("AC-6.10b follows the video's frame rate", () => expect(formatClock(frameTime(49, 25, 1))).toBe("00:01.960"));
  it("AC-6.10c uses the average frame rate for a variable-frame-rate video", () => expect(formatClock(frameTime(59, 20, 1))).toBe("00:02.950"));
});
