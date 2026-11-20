// US-16 live target telemetry (AC-16.1 to AC-16.5).
import { describe, expect, it } from "vitest";
import { formatChange, formatMargin, telemetry } from "./telemetry";

const zone: [number, number, number, number] = [100, 100, 200, 200];

describe("AC-16.1 telemetry of a tracked frame", () => {
  it("gives centre, size, area and change", () => {
    const t = telemetry([180, 292, 96, 66], [172, 292, 96, 66], null);
    expect(t).toMatchObject({ cx: 228, cy: 325, w: 96, h: 66, area: 6336, change: 0, margin: null });
    expect(formatChange(t!.change)).toBe("0.0 %");
  });
});

describe("AC-16.2 area change against the previous frame, signed", () => {
  it.each([[150, "+50.0 %"], [40, "−60.0 %"], [100, "0.0 %"], [150.01, "+50.0 %"]])(
    "width %f of 100 x 100 reads %s", (w, text) =>
      expect(formatChange(telemetry([0, 0, w, 100], [0, 0, 100, 100], null)!.change)).toBe(text));
  it("reports the exact ratio so the 50 % limit can be judged", () => {
    expect(telemetry([0, 0, 150, 100], [0, 0, 100, 100], null)!.change).toBeCloseTo(0.5, 12);
    expect(telemetry([0, 0, 40, 100], [0, 0, 100, 100], null)!.change).toBeCloseTo(-0.6, 12);
  });
});

describe("AC-16.3 no change without a box on the frame before", () => {
  it.each([[null], ["lost"]])("previous frame %s", (previous) => {
    const t = telemetry([0, 0, 50, 50], previous as null | "lost", null);
    expect(t!.change).toBeNull();
    expect(formatChange(t!.change)).toBe("—");
  });
});

describe("AC-16.4 margin to the lock zone (same edges as AC-11.1)", () => {
  it.each([
    [150, 50, "50 px inside"], [100, 0, "0 px inside"], [99, -1, "1 px outside"],
    [250, 0, "0 px inside"], [251, -1, "1 px outside"],
  ])("box at x %i: margin %i", (x, margin, text) => {
    const t = telemetry([x, 150, 50, 50], null, zone)!;
    expect(t.margin).toBe(margin);
    expect(formatMargin(t.margin, true)).toBe(text);
  });
  it("is the smallest of the four distances", () => {
    expect(telemetry([110, 290, 50, 5], null, zone)!.margin).toBe(5);       // bottom edge is closest
    expect(telemetry([90, 90, 220, 220], null, zone)!.margin).toBe(-10);    // larger than the zone
  });
});

describe("AC-16.5 nothing to show", () => {
  it("has no telemetry for a frame without a box", () => {
    expect(telemetry(null, null, zone)).toBeNull();
    expect(telemetry("lost", [0, 0, 10, 10], zone)).toBeNull();
  });
  it("says when there is no lock zone", () => expect(formatMargin(null, false)).toBe("No lock zone"));
});
