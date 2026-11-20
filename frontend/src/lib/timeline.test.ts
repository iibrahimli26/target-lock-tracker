// US-18 timeline with a time scale (AC-18.1, AC-18.2) and US-17 (AC-17.1, AC-17.2).
import { describe, expect, it } from "vitest";
import { canPlay, displayStatus, periodNumbers, tickLabel, timeTicks } from "./flow";

describe("AC-18.1 time marks at a readable step, at most 10 steps", () => {
  it.each([
    [3.0, 0.5, 7], [24.258, 5, 5], [600, 60, 11], [30, 5, 7], [5, 0.5, 11], [5.01, 1, 6], [3600, 600, 7],
  ])("%f s -> every %f s, %i marks", (duration, step, count) => {
    const ticks = timeTicks(duration);
    expect(ticks.step).toBe(step);
    expect(ticks.times.length).toBe(count);
    expect(ticks.times[0]).toBe(0);
    expect(ticks.times[ticks.times.length - 1]).toBeLessThanOrEqual(duration + 1e-9);
  });
  it("has no marks for an empty video", () => expect(timeTicks(0).times).toEqual([]));
  it.each([[1.5, 0.5, 3, "1.5 s"], [20, 5, 24.3, "20 s"], [120, 60, 600, "2:00"], [3600, 600, 3600, "1:00:00"]])(
    "labels %f s (step %f, duration %f) as %s", (t, step, duration, text) => expect(tickLabel(t, step, duration)).toBe(text));
});

describe("AC-18.2 lock periods numbered as in the analytics list", () => {
  it("numbers locked segments in order", () => {
    const segments: [string, number, number][] = [["unlocked", 0, 9], ["locked", 10, 39], ["lost", 40, 44], ["locked", 45, 59], ["unlocked", 60, 69]];
    expect(periodNumbers(segments)).toEqual(new Map([[10, 1], [45, 2]]));
  });
});

describe("AC-17.1 Play waits while tracking runs", () => {
  it.each([["idle", true], ["running", false], ["completed", true], ["lost", true], ["stopped", true]])(
    "run state %s: play %s", (state, ok) => expect(canPlay(state)).toBe(ok));
});

describe("AC-17.2 frames the tracker has not reached are 'Not tracked yet'", () => {
  const run = { state: "running", start_frame: 10, current_frame: 20 };
  it.each([[60, "not_tracked", "not_tracked_yet"], [21, "not_tracked", "not_tracked_yet"], [5, "not_tracked", "not_tracked"],
           [20, "locked", "locked"], [15, "unlocked", "unlocked"]])(
    "frame index %i (%s) is shown as %s", (index, status, shown) => expect(displayStatus(status, index, run)).toBe(shown));
  it("after the run ends nothing is 'yet'", () =>
    expect(displayStatus("not_tracked", 60, { ...run, state: "completed" })).toBe("not_tracked"));
});
