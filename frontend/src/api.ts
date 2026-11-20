// Talks to the Python backend. Messages come from the backend's one message
// list and are shown unchanged (Stage 1 note 11).
import type { Box } from "./lib/geometry";
import type { Segment } from "./lib/flow";
import type { Timing } from "./lib/timing";

export interface Message { code: string; message: string; found: string | null; allowed: string | null }
export interface Metadata {
  width: number; height: number; frame_count: number; duration_seconds: number;
  fps: { num: number; den: number; value: number }; variable_frame_rate: boolean; timing: Timing;
}
export interface Video { id: string; name: string; size: number; metadata: Metadata; warnings: Message[] }
export type FrameResult = [number, number, number, number] | "lost" | null;
export interface Amount { frames: number; seconds: number }
export interface Analytics {
  total_frames: number; locked: Amount; unlocked: Amount; lost: Amount; not_tracked: Amount;
  lock_periods: number; longest_lock: Amount; average_lock: Amount;
  periods: { start: number; end: number; frames: number; seconds: number }[];
}
export interface Run {
  state: "idle" | "running" | "lost" | "completed" | "stopped"; revision: number;
  start_frame: number | null; current_frame: number | null; processed_frames: number; total_frames: number;
  processing_fps: number; lost_at: number | null; lost_reason: string | null; lost_message: string | null;
}
export interface Tracking {
  target: { frame: number; box: [number, number, number, number] } | null;
  zone: [number, number, number, number] | null;
  run: Run; results: { from: number; items: FrameResult[] }; analytics: Analytics; segments: Segment[];
}
export type Outcome<T> = { ok: true; value: T } | { ok: false; problems: Message[] };

const unreachable: Message = { code: "unreachable", message: "The application did not answer. Check that it is still running.", found: null, allowed: null };

async function outcome<T>(request: Promise<Response>, read: (r: Response) => Promise<T>): Promise<Outcome<T>> {
  try {
    const response = await request;
    if (response.ok) return { ok: true, value: await read(response) };
    const body = await response.json().catch(() => null);
    return { ok: false, problems: body?.problems ?? [unreachable] };
  } catch {
    return { ok: false, problems: [unreachable] };
  }
}

const json = (body: unknown): RequestInit => ({ headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
const asArray = (b: Box): number[] => [b.x, b.y, b.w, b.h];

export const api = {
  upload: (file: File) => outcome(
    fetch("/api/upload", { method: "POST", body: file, headers: { "X-File-Name": encodeURIComponent(file.name) } }),
    async (r) => (await r.json()).video as Video),
  currentVideo: () => outcome(fetch("/api/video"), async (r) => (await r.json()).video as Video),
  frame: (id: string, index: number) => outcome(fetch(`/api/video/${id}/frames/${index}`), (r) => r.blob()),
  fileUrl: (id: string) => `/api/video/${id}/file`,
  tracking: (id: string, since = 0, revision?: number) => outcome(
    fetch(`/api/video/${id}/tracking?since=${since}${revision === undefined ? "" : `&revision=${revision}`}`),
    (r) => r.json() as Promise<Tracking>),
  setTarget: (id: string, frame: number, box: Box) => outcome(
    fetch(`/api/video/${id}/target`, { method: "PUT", ...json({ frame, box: asArray(box) }) }), (r) => r.json()),
  setZone: (id: string, box: Box) => outcome(
    fetch(`/api/video/${id}/zone`, { method: "PUT", ...json({ box: asArray(box) }) }), (r) => r.json()),
  startTracking: (id: string) => outcome(fetch(`/api/video/${id}/tracking`, { method: "POST" }), (r) => r.json() as Promise<Tracking>),
};
