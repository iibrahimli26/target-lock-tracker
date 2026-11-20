// Small decisions of the page that are worth testing on their own.

export type Status = "locked" | "unlocked" | "lost" | "not_tracked";
export type Segment = [string, number, number];          // [status, first index, last index]

/** OQ-10 / AQ-8: ask before a loaded video is replaced, and before the new file is sent. */
export function decideUpload(videoLoaded: boolean, confirm: () => boolean): "upload" | "keep" {
  return !videoLoaded || confirm() ? "upload" : "keep";
}

/** Only the answer to the newest request may be shown (fast stepping, slider, overlapping uploads). */
export function latestOnly() {
  let newest = 0;
  return {
    begin: () => ++newest,
    isCurrent: (ticket: number) => ticket === newest,
  };
}

export function statusAt(segments: Segment[], index: number): Status {
  let low = 0, high = segments.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    const [status, start, end] = segments[mid];
    if (index < start) high = mid - 1;
    else if (index > end) low = mid + 1;
    else return status as Status;
  }
  return "not_tracked";
}

/** OQ-17: at either end the button that would leave the video is inactive. */
export function canStep(index: number, frameCount: number): { back: boolean; forward: boolean } {
  return { back: frameCount > 0 && index > 0, forward: frameCount > 0 && index < frameCount - 1 };
}

export function markerPosition(index: number, frameCount: number): number {
  return frameCount > 0 ? index / frameCount : 0;
}

// --- US-17 Play waits for tracking ------------------------------------------------
export function canPlay(runState: string): boolean {
  return runState !== "running";
}

/** While a run is going, frames it has not reached yet are "not_tracked_yet" (AQ-19). */
export function displayStatus(status: string, index: number,
                              run: { state: string; start_frame: number | null; current_frame: number | null } | null): string {
  if (status === "not_tracked" && run?.state === "running" && run.start_frame !== null && run.current_frame !== null
      && index >= run.start_frame && index > run.current_frame) return "not_tracked_yet";
  return status;
}

// --- US-18 timeline scale ---------------------------------------------------------
const STEPS = [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600];

/** OQ-39: the smallest step that gives at most 10 steps. */
export function timeTicks(duration: number): { step: number; times: number[] } {
  if (!(duration > 0)) return { step: 0, times: [] };
  const step = STEPS.find((s) => duration / s <= 10) ?? Math.ceil(duration / 10 / 3600) * 3600;
  const times: number[] = [];
  for (let k = 0; k * step <= duration + 1e-9; k++) times.push(Math.round(k * step * 1000) / 1000);
  return { step, times };
}

export function tickLabel(t: number, step: number, duration: number): string {
  if (duration < 60) return `${step < 1 ? t.toFixed(1) : Math.round(t)} s`;
  const total = Math.round(t), h = Math.floor(total / 3600), m = Math.floor(total / 60) % 60, s = total % 60;
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${ss}` : `${m}:${ss}`;
}

/** Locked segments numbered 1, 2, ... in order, keyed by their first frame (same order as the analytics list). */
export function periodNumbers(segments: Segment[]): Map<number, number> {
  const numbers = new Map<number, number>();
  for (const [status, start] of segments) if (status === "locked") numbers.set(start, numbers.size + 1);
  return numbers;
}
