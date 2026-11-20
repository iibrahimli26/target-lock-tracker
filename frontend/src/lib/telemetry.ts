// US-16: numbers about the tracked box on the frame shown. Descriptive only:
// LOCKED / LOST are decided by the server; these explain why.
import { formatCount } from "./format";

type Result = [number, number, number, number] | "lost" | null;

export interface Telemetry { cx: number; cy: number; w: number; h: number; area: number; change: number | null; margin: number | null }

export function telemetry(box: Result, previous: Result, zone: [number, number, number, number] | null): Telemetry | null {
  if (!Array.isArray(box)) return null;
  const [x, y, w, h] = box;
  const area = w * h;
  const change = Array.isArray(previous) && previous[2] * previous[3] > 0 ? area / (previous[2] * previous[3]) - 1 : null;
  // Smallest distance from a box edge to the matching zone edge; >= 0 means inside (edges inclusive, like AC-11.1).
  const margin = zone ? Math.min(x - zone[0], y - zone[1], zone[0] + zone[2] - (x + w), zone[1] + zone[3] - (y + h)) : null;
  const r = (v: number) => Math.round(v * 100) / 100;
  return { cx: r(x + w / 2), cy: r(y + h / 2), w: r(w), h: r(h), area: r(area), change, margin: margin === null ? null : r(margin) };
}

export function formatChange(change: number | null): string {
  if (change === null) return "—";
  const percent = Math.round(change * 1000) / 10;
  if (percent === 0) return "0.0 %";
  return `${percent > 0 ? "+" : "−"}${Math.abs(percent).toFixed(1)} %`;
}

export function formatMargin(margin: number | null, zoneExists: boolean): string {
  if (!zoneExists) return "No lock zone";
  if (margin === null) return "—";
  return margin >= 0 ? `${formatCount(margin)} px inside` : `${formatCount(-margin)} px outside`;
}
