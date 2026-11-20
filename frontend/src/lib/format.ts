// How numbers are written on screen. Always the English way, whatever the
// browser's language is (OQ-11): 2,073,600 and 29.97, never 2.073.600 or 29,97.

const english = new Intl.NumberFormat("en-US");

export function formatCount(value: number): string {
  return english.format(Math.round(value));
}

/** OQ-13: always two decimals, so 30 reads "30.00" and 30000/1001 reads "29.97". */
export function formatFps(num: number, den: number): string {
  return den ? (Math.round((num / den) * 100) / 100).toFixed(2) : "0.00";
}

/** OQ-13: minutes:seconds.milliseconds, hours in front from one hour on. */
export function formatClock(seconds: number): string {
  const total = Math.max(0, Math.round(seconds * 1000));
  const ms = total % 1000;
  const s = Math.floor(total / 1000) % 60;
  const m = Math.floor(total / 60000) % 60;
  const h = Math.floor(total / 3600000);
  const pad = (n: number, width = 2) => String(n).padStart(width, "0");
  const tail = `${pad(m)}:${pad(s)}.${pad(ms, 3)}`;
  return h > 0 ? `${h}:${tail}` : tail;
}

/** Durations in the analytics panel: seconds with three decimals. */
export function formatSeconds(seconds: number): string {
  return `${new Intl.NumberFormat("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(seconds)} s`;
}
