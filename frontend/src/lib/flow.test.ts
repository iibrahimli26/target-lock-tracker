// AC-5.8a/b/e (confirm before replacing), AC-6.6 / AC-6.9e (only the newest answer is shown),
// AC-14.4 (status of the frame shown), AC-6.11 (step buttons at the ends), AC-15.3.
import { describe, expect, it } from "vitest";
import { canStep, decideUpload, latestOnly, markerPosition, statusAt } from "./flow";

describe("AC-5.8 confirmation before replacing the loaded video (asked before the file is sent, AQ-8)", () => {
  it("AC-5.8e no confirmation when nothing is loaded", () => {
    let asked = 0;
    expect(decideUpload(false, () => { asked++; return true; })).toBe("upload");
    expect(asked).toBe(0);
  });
  it("AC-5.8a asks, and uploads when confirmed", () => {
    let asked = 0;
    expect(decideUpload(true, () => { asked++; return true; })).toBe("upload");
    expect(asked).toBe(1);
  });
  it("AC-5.8b keeps everything when declined", () => expect(decideUpload(true, () => false)).toBe("keep"));
});

describe("AC-6.6 / AC-6.9e / AC-5.8d only the newest request counts", () => {
  it("drops answers that arrive after a newer request was made", () => {
    const gate = latestOnly();
    const first = gate.begin(), second = gate.begin(), third = gate.begin();
    expect(gate.isCurrent(first)).toBe(false);
    expect(gate.isCurrent(second)).toBe(false);
    expect(gate.isCurrent(third)).toBe(true);
  });
});

describe("AC-14.4 the current status is the status of the frame shown", () => {
  const s1: [string, number, number][] = [["unlocked", 0, 9], ["locked", 10, 39], ["unlocked", 40, 44], ["locked", 45, 59], ["lost", 60, 62], ["locked", 63, 69]];
  it.each([[4, "unlocked"], [19, "locked"], [61, "lost"], [9, "unlocked"], [10, "locked"], [39, "locked"], [40, "unlocked"], [69, "locked"]])(
    "frame index %i is %s", (index, status) => expect(statusAt(s1, index)).toBe(status));
  it("is 'not_tracked' when there is nothing for that frame", () => {
    expect(statusAt([], 5)).toBe("not_tracked");
    expect(statusAt(s1, 70)).toBe("not_tracked");
  });
});

describe("AC-6.11 step buttons at the ends of the video (OQ-17)", () => {
  it.each([
    [0, 90, false, true], [1, 90, true, true], [88, 90, true, true], [89, 90, true, false], [0, 2, false, true], [1, 2, true, false],
  ])("at frame index %i of %i: back %s, forward %s", (index, count, back, forward) =>
    expect(canStep(index, count)).toEqual({ back, forward }));
  it("nothing can be stepped when no video is loaded", () => expect(canStep(0, 0)).toEqual({ back: false, forward: false }));
});

describe("AC-15.3 the current frame is marked on the timeline", () => {
  it("frame 30 of 70 stands 29/70 of the way along", () => expect(markerPosition(29, 70)).toBeCloseTo(29 / 70, 9));
  it("is 0 for an empty video", () => expect(markerPosition(0, 0)).toBe(0));
});
