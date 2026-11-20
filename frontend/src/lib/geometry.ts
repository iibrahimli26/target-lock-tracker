// Boxes on the picture. Everything stored or sent is in picture pixels; only
// toPicture() and toScreen() know about the size the picture is shown at.

export interface Point { x: number; y: number }
export interface Box { x: number; y: number; w: number; h: number }
export interface Size { width: number; height: number }
export type Handle = "move" | "nw" | "ne" | "sw" | "se";

const round = (v: number) => Math.round(v * 100) / 100;

export function toPicture(screen: Point, scale: number): Point {
  return { x: round(screen.x / scale), y: round(screen.y / scale) };
}

export function toScreen(box: Box, scale: number): Box {
  return { x: box.x * scale, y: box.y * scale, w: box.w * scale, h: box.h * scale };
}

export function clampPoint(point: Point, picture: Size): Point {
  return { x: Math.min(Math.max(point.x, 0), picture.width), y: Math.min(Math.max(point.y, 0), picture.height) };
}

/** The box between two corners, whichever way the drag went. */
export function boxFromDrag(a: Point, b: Point): Box {
  return { x: Math.min(a.x, b.x), y: Math.min(a.y, b.y), w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) };
}

/** What the pointer is over: a corner (within `reach` picture pixels), the inside, or nothing. */
export function hitTest(box: Box, point: Point, reach: number): Handle | null {
  const corners: [Handle, number, number][] = [
    ["nw", box.x, box.y], ["ne", box.x + box.w, box.y], ["sw", box.x, box.y + box.h], ["se", box.x + box.w, box.y + box.h],
  ];
  for (const [handle, cx, cy] of corners) {
    if (Math.abs(point.x - cx) <= reach && Math.abs(point.y - cy) <= reach) return handle;
  }
  const inside = point.x >= box.x && point.x <= box.x + box.w && point.y >= box.y && point.y <= box.y + box.h;
  return inside ? "move" : null;
}

export function moveBox(box: Box, dx: number, dy: number, picture: Size): Box {
  return {
    x: round(Math.min(Math.max(box.x + dx, 0), picture.width - box.w)),
    y: round(Math.min(Math.max(box.y + dy, 0), picture.height - box.h)),
    w: box.w, h: box.h,
  };
}

/** Drag one corner to `point`; the opposite corner stays where it is. */
export function resizeBox(box: Box, handle: Exclude<Handle, "move">, point: Point, picture: Size): Box {
  const fixed: Point = {
    x: handle === "nw" || handle === "sw" ? box.x + box.w : box.x,
    y: handle === "nw" || handle === "ne" ? box.y + box.h : box.y,
  };
  return boxFromDrag(fixed, clampPoint(point, picture));
}
