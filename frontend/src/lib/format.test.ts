// AC-4.7a, AC-4.7b, AC-5.6c: how numbers are written on screen (OQ-13, OQ-11).
import { describe, expect, it } from "vitest";
import { formatClock, formatCount, formatFps, formatSeconds } from "./format";

describe("AC-4.7a frame rates are written with two decimals", () => {
  it.each([
    [30, 1, "30.00"], [25, 1, "25.00"], [20, 1, "20.00"],
    [30000, 1001, "29.97"], [24000, 1001, "23.98"], [60000, 1001, "59.94"],
  ])("%i/%i reads %s", (num, den, text) => expect(formatFps(num, den)).toBe(text));
});

describe("AC-4.7b durations are written as a clock", () => {
  it.each([
    [3.0, "00:03.000"], [0.0666667, "00:00.067"], [59.999, "00:59.999"], [60.0, "01:00.000"],
    [600.0, "10:00.000"], [3599.999, "59:59.999"], [3600.0, "1:00:00.000"], [3725.5, "1:02:05.500"],
    [3.003, "00:03.003"], [0, "00:00.000"],
  ])("%f s reads %s", (seconds, text) => expect(formatClock(seconds)).toBe(text));
});

describe("AC-5.6c numbers are written the English way whatever the browser's language", () => {
  it("uses commas for thousands", () => {
    expect(formatCount(2073600)).toBe("2,073,600");
    expect(formatCount(18000)).toBe("18,000");
    expect(formatCount(90)).toBe("90");
  });
  it("writes seconds with three decimals and a point", () => {
    expect(formatSeconds(52 / 30)).toBe("1.733 s");
    expect(formatSeconds(0)).toBe("0.000 s");
    expect(formatSeconds(1234.5)).toBe("1,234.500 s");
  });
});
