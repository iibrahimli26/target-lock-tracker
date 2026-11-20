// Frames and time. The API, the results and OpenCV count frames from 0 ("index").
// People see frames counted from 1 ("number", OQ-16). frameNumber() is the one
// place where the two meet (Stage 1 note 13).

export interface Timing { timescale: number; runs: [number, number][] }   // (count, ticks) runs from the file header

export function frameNumber(index: number): number {
  return index + 1;
}

/** OQ-16 / OQ-7: a frame's time is the moment it starts, index / FPS (the average FPS). */
export function frameTime(index: number, fpsNum: number, fpsDen: number): number {
  return fpsNum ? (index * fpsDen) / fpsNum : 0;
}

/** Start time in seconds of every frame, from the header's per-frame lengths. */
export function frameStartTimes(timing: Timing): Float64Array {
  const count = timing.runs.reduce((sum, [n]) => sum + n, 0);
  const times = new Float64Array(count);
  let ticks = 0, i = 0;
  for (const [n, length] of timing.runs) {
    for (let k = 0; k < n; k++) {
      times[i++] = ticks / timing.timescale;
      ticks += length;
    }
  }
  return times;
}

/** AQ-14: the frame on screen at media time t is the last frame that has started by then. */
export function frameAtTime(times: Float64Array, seconds: number): number {
  let low = 0, high = times.length - 1;
  if (high < 0) return 0;
  const t = seconds + 1e-6;                       // a frame whose start equals t has started
  while (low < high) {
    const mid = (low + high + 1) >> 1;
    if (times[mid] <= t) low = mid; else high = mid - 1;
  }
  return low;
}
