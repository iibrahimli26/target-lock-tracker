// AC-7.1 to AC-7.4, AC-7.7: drawing, scaling and adjusting a box on the picture.
import { describe, expect, it } from "vitest";
import { boxFromDrag, clampPoint, hitTest, moveBox, resizeBox, toPicture, toScreen } from "./geometry";

const picture = { width: 1280, height: 720 };

describe("drawing a box", () => {
  it("AC-7.1 a drag gives the box between its two corners", () =>
    expect(boxFromDrag({ x: 592, y: 328 }, { x: 688, y: 392 })).toEqual({ x: 592, y: 328, w: 96, h: 64 }));
  it("AC-7.2 dragging in the opposite direction gives the same box", () => {
    expect(boxFromDrag({ x: 688, y: 392 }, { x: 592, y: 328 })).toEqual({ x: 592, y: 328, w: 96, h: 64 });
    expect(boxFromDrag({ x: 688, y: 328 }, { x: 592, y: 392 })).toEqual({ x: 592, y: 328, w: 96, h: 64 });
  });
  it("AC-7.3 screen points are converted to picture pixels by the display scale", () => {
    const scale = 640 / 1280;       // the 1280-wide picture is shown 640 wide
    expect(boxFromDrag(toPicture({ x: 296, y: 164 }, scale), toPicture({ x: 344, y: 196 }, scale)))
      .toEqual({ x: 592, y: 328, w: 96, h: 64 });
    expect(toScreen({ x: 592, y: 328, w: 96, h: 64 }, scale)).toEqual({ x: 296, y: 164, w: 48, h: 32 });
  });
  it("AC-7.7 drawing stops at the edge of the picture", () => {
    expect(clampPoint({ x: 1400, y: -30 }, picture)).toEqual({ x: 1280, y: 0 });
    expect(clampPoint({ x: 640, y: 800 }, picture)).toEqual({ x: 640, y: 720 });
    expect(boxFromDrag(clampPoint({ x: 1200, y: 650 }, picture), clampPoint({ x: 1500, y: 900 }, picture)))
      .toEqual({ x: 1200, y: 650, w: 80, h: 70 });
  });
});

describe("AC-7.4 adjusting a box", () => {
  const box = { x: 100, y: 100, w: 200, h: 100 };
  it("finds what is under the pointer", () => {
    expect(hitTest(box, { x: 200, y: 150 }, 8)).toBe("move");
    expect(hitTest(box, { x: 101, y: 99 }, 8)).toBe("nw");
    expect(hitTest(box, { x: 300, y: 200 }, 8)).toBe("se");
    expect(hitTest(box, { x: 297, y: 104 }, 8)).toBe("ne");
    expect(hitTest(box, { x: 103, y: 196 }, 8)).toBe("sw");
    expect(hitTest(box, { x: 400, y: 400 }, 8)).toBeNull();
  });
  it("moves the box and keeps it inside the picture", () => {
    expect(moveBox(box, 50, -20, picture)).toEqual({ x: 150, y: 80, w: 200, h: 100 });
    expect(moveBox(box, -500, -500, picture)).toEqual({ x: 0, y: 0, w: 200, h: 100 });
    expect(moveBox(box, 5000, 5000, picture)).toEqual({ x: 1080, y: 620, w: 200, h: 100 });
  });
  it("resizes from a corner; the opposite corner stays where it is", () => {
    expect(resizeBox(box, "se", { x: 350, y: 260 }, picture)).toEqual({ x: 100, y: 100, w: 250, h: 160 });
    expect(resizeBox(box, "nw", { x: 60, y: 90 }, picture)).toEqual({ x: 60, y: 90, w: 240, h: 110 });
    expect(resizeBox(box, "se", { x: 5000, y: 5000 }, picture)).toEqual({ x: 100, y: 100, w: 1180, h: 620 });
    expect(resizeBox(box, "se", { x: 50, y: 50 }, picture)).toEqual({ x: 50, y: 50, w: 50, h: 50 });   // dragged past the opposite corner
  });
});
