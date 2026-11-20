import type { Analytics, Message, Run, Video } from "../api";
import { type Segment, type Status, markerPosition } from "../lib/flow";
import { formatClock, formatCount, formatFps, formatSeconds } from "../lib/format";
import { frameNumber } from "../lib/timing";

export const STATUS_TEXT: Record<Status, string> = { locked: "LOCKED", unlocked: "UNLOCKED", lost: "LOST", not_tracked: "Not tracked" };
export const STATUS_COLOR: Record<Status, string> = { locked: "#46B978", unlocked: "#E3A53A", lost: "#E5534B", not_tracked: "#5E666F" };

export function Messages({ problems, warnings }: { problems: Message[]; warnings: Message[] }) {
  if (problems.length === 0 && warnings.length === 0) return null;
  return (
    <section aria-live="polite" className="space-y-1">
      {problems.length > 0 && (
        <div className="panel border-l-4 border-l-lost px-3 py-2" role="alert">
          <p className="text-graphite-200">{problems.length === 1 ? "The file was not loaded:" : `The file was not loaded. ${problems.length} problems were found:`}</p>
          <ul className="mt-1 space-y-1">
            {problems.map((p) => <li key={p.code} data-testid="problem" data-code={p.code}>{p.message}</li>)}
          </ul>
        </div>
      )}
      {warnings.map((w) => (
        <div key={w.code} className="panel border-l-4 border-l-unlocked px-3 py-2" data-testid="warning" data-code={w.code}>{w.message}</div>
      ))}
    </section>
  );
}

export function StatusPanel({ status, run, zone, videoLoaded }: { status: Status; run: Run | null; zone: [number, number, number, number] | null; videoLoaded: boolean }) {
  const percent = run && run.total_frames > 0 && run.current_frame !== null ? Math.round(((run.current_frame + 1) / run.total_frames) * 100) : 0;
  const runText: Record<Run["state"], string> = {
    idle: "Not started", running: "Tracking", completed: "Tracking finished", lost: "Target lost, waiting for a new box", stopped: "Stopped at a damaged frame",
  };
  return (
    <section className="panel">
      <h2 className="panel-title">Lock status of this frame</h2>
      <p className="px-3 pt-2 pb-1 font-mono text-[30px] leading-none tracking-wide" style={{ color: STATUS_COLOR[status] }}
         data-testid="status" data-status={status}>{STATUS_TEXT[status]}</p>
      {videoLoaded && (zone ? (
        <p className="px-3 pb-1 text-graphite-400" data-testid="zone-state" data-zone="drawn">
          Lock zone: <span className="readout text-graphite-200">{Math.round(zone[2])} × {Math.round(zone[3])}</span> px at{" "}
          <span className="readout text-graphite-200">{Math.round(zone[0])}, {Math.round(zone[1])}</span>
        </p>
      ) : (
        <p className="mx-3 mb-1 border-l-4 border-l-unlocked bg-graphite-700 px-2 py-1.5" data-testid="zone-state" data-zone="none">
          No lock zone is drawn, so no frame can be LOCKED. Choose <b>Lock zone</b> under the picture and drag a rectangle.
        </p>
      ))}
      <dl className="pb-2">
        <div className="row"><dt>Tracking run</dt><dd data-testid="run-state" data-state={run?.state ?? "idle"}>{runText[run?.state ?? "idle"]}</dd></div>
        {run && run.state !== "idle" && (
          <>
            <div className="row"><dt>Frame processed</dt>
              <dd data-testid="run-progress">{formatCount(frameNumber(run.current_frame ?? 0))} / {formatCount(run.total_frames)} ({percent} %)</dd></div>
            <div className="row"><dt>Processing speed</dt><dd data-testid="run-fps">{run.processing_fps.toFixed(1)} FPS</dd></div>
            <div className="mx-3 mt-1 h-[3px] bg-graphite-600" aria-hidden="true">
              <div className="h-full bg-graphite-200" style={{ width: `${percent}%` }} />
            </div>
          </>
        )}
      </dl>
      {run?.lost_message && (
        <p className="border-t border-graphite-600 px-3 py-2" style={{ color: STATUS_COLOR.lost }} data-testid="lost-message">{run.lost_message}</p>
      )}
    </section>
  );
}

export function AnalyticsPanel({ analytics }: { analytics: Analytics | null }) {
  const amount = (a?: { frames: number; seconds: number }) => (a ? `${formatSeconds(a.seconds)}  (${formatCount(a.frames)} fr)` : "—");
  return (
    <section className="panel">
      <h2 className="panel-title">Lock analytics</h2>
      <dl className="py-1">
        <div className="row"><dt>Total locked</dt><dd data-testid="total-locked" style={{ color: STATUS_COLOR.locked }}>{amount(analytics?.locked)}</dd></div>
        <div className="row"><dt>Total unlocked</dt><dd data-testid="total-unlocked" style={{ color: STATUS_COLOR.unlocked }}>{amount(analytics?.unlocked)}</dd></div>
        <div className="row"><dt>Total lost</dt><dd data-testid="total-lost" style={{ color: STATUS_COLOR.lost }}>{amount(analytics?.lost)}</dd></div>
        <div className="row"><dt>Lock periods</dt><dd data-testid="lock-periods">{analytics ? formatCount(analytics.lock_periods) : "—"}</dd></div>
        <div className="row"><dt>Longest lock</dt><dd data-testid="longest-lock">{analytics ? formatSeconds(analytics.longest_lock.seconds) : "—"}</dd></div>
        <div className="row"><dt>Average lock</dt><dd data-testid="average-lock">{analytics ? formatSeconds(analytics.average_lock.seconds) : "—"}</dd></div>
      </dl>
      {analytics && analytics.periods.length > 0 && (
        <div className="max-h-40 overflow-y-auto border-t border-graphite-600">
          <table className="readout w-full" data-testid="period-list">
            <thead>
              <tr className="text-graphite-400">
                <th className="px-3 py-1 text-left font-normal">Period</th>
                <th className="py-1 text-right font-normal">Frames</th>
                <th className="px-3 py-1 text-right font-normal">Lasted</th>
              </tr>
            </thead>
            <tbody>
              {analytics.periods.map((p, i) => (
                <tr key={p.start}>
                  <td className="px-3 py-0.5">{i + 1}</td>
                  <td className="whitespace-nowrap py-0.5 text-right">{formatCount(frameNumber(p.start))} to {formatCount(frameNumber(p.end))}</td>
                  <td className="whitespace-nowrap px-3 py-0.5 text-right">{formatSeconds(p.seconds)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function MetadataPanel({ video }: { video: Video | null }) {
  const m = video?.metadata;
  return (
    <section className="panel">
      <h2 className="panel-title">Video</h2>
      <dl className="py-1">
        <div className="row"><dt>File</dt><dd className="truncate !font-sans" data-testid="meta-name" title={video?.name}>{video?.name ?? "—"}</dd></div>
        <div className="row"><dt>Resolution</dt><dd data-testid="meta-resolution">{m ? `${m.width} × ${m.height}` : "—"}</dd></div>
        <div className="row"><dt>{m?.variable_frame_rate ? "Frame rate (average)" : "Frame rate"}</dt>
          <dd data-testid="meta-fps">{m ? formatFps(m.fps.num, m.fps.den) : "—"}</dd></div>
        <div className="row"><dt>Duration</dt><dd data-testid="meta-duration">{m ? formatClock(m.duration_seconds) : "—"}</dd></div>
        <div className="row"><dt>Total frames</dt><dd data-testid="meta-frames">{m ? formatCount(m.frame_count) : "—"}</dd></div>
      </dl>
    </section>
  );
}

export function Timeline({ segments, frameCount, index, duration }: { segments: Segment[]; frameCount: number; index: number; duration: number }) {
  const shown: Segment[] = segments.length > 0 ? segments : frameCount > 0 ? [["not_tracked", 0, frameCount - 1]] : [];
  return (
    <div data-testid="timeline">
      <div className="relative h-6 border border-graphite-600 bg-graphite-950">
        <div className="flex h-full">
          {shown.map(([status, start, end]) => (
            <div key={start} data-testid="timeline-segment" data-status={status} data-start={start} data-end={end}
                 title={`${STATUS_TEXT[status as Status]}: frames ${formatCount(frameNumber(start))} to ${formatCount(frameNumber(end))}`}
                 style={{ width: `${((end - start + 1) / frameCount) * 100}%`, background: STATUS_COLOR[status as Status], opacity: status === "not_tracked" ? 0.35 : 1 }} />
          ))}
        </div>
        {frameCount > 0 && (
          <div data-testid="timeline-marker" className="absolute -top-1 -bottom-1 w-px bg-white" style={{ left: `${markerPosition(index, frameCount) * 100}%` }} />
        )}
      </div>
      <div className="mt-1 flex justify-between text-graphite-400 readout text-[11px]">
        <span>{formatClock(0)}</span>
        <span className="flex gap-3 font-sans">
          {(["locked", "unlocked", "lost"] as Status[]).map((s) => (
            <span key={s} className="flex items-center gap-1"><i className="inline-block h-2 w-2" style={{ background: STATUS_COLOR[s] }} />{STATUS_TEXT[s].toLowerCase()}</span>
          ))}
        </span>
        <span>{formatClock(duration)}</span>
      </div>
    </div>
  );
}
