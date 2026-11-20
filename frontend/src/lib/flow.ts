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
