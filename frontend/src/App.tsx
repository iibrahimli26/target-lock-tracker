import { useCallback, useEffect, useLayoutEffect, useMemo, useReducer, useRef, useState } from "react";
import { type FrameResult, type Message, type Tracking, type Video, api } from "./api";
import { AnalyticsPanel, Messages, MetadataPanel, StatusPanel, Timeline } from "./components/Panels";
import { Stage, type Tool } from "./components/Stage";
import { canStep, decideUpload, latestOnly, statusAt } from "./lib/flow";
import { formatClock, formatCount } from "./lib/format";
import type { Box } from "./lib/geometry";
import { frameAtTime, frameNumber, frameStartTimes, frameTime } from "./lib/timing";

const toBox = (b: [number, number, number, number]): Box => ({ x: b[0], y: b[1], w: b[2], h: b[3] });

export default function App() {
  const [video, setVideo] = useState<Video | null>(null);
  const [problems, setProblems] = useState<Message[]>([]);
  const [notice, setNotice] = useState<Message | null>(null);        // frame or box message
  const [busy, setBusy] = useState(false);
  const [index, setIndex] = useState(0);                             // frame on screen, counted from 0
  const [pending, setPending] = useState<number | null>(null);       // frame asked for but not shown yet
  const [frameUrl, setFrameUrl] = useState<string | null>(null);
  const [tool, setTool] = useState<Tool>("target");
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [playing, setPlaying] = useState(false);
  const [, redraw] = useReducer((n: number) => n + 1, 0);

  const player = useRef<HTMLVideoElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const results = useRef<FrameResult[]>([]);
  const known = useRef({ revision: -1, upto: 0 });
  const current = useRef<{ id: string | null; index: number; pending: number | null }>({ id: null, index: 0, pending: null });
  const frames = useRef(latestOnly());
  const uploads = useRef(latestOnly());
  const jumpedFor = useRef(-1);
  const playingNow = useRef(false);

  const meta = video?.metadata ?? null;
  const count = meta?.frame_count ?? 0;
  const times = useMemo(() => (meta ? frameStartTimes(meta.timing) : new Float64Array()), [meta]);

  // --- frames -----------------------------------------------------------------
  const showFrame = useCallback(async (id: string, wanted: number) => {
    const ticket = frames.current.begin();
    current.current.pending = wanted;
    setPending(wanted);
    const answer = await api.frame(id, wanted);
    if (!frames.current.isCurrent(ticket) || current.current.id !== id) return;     // a newer request exists
    current.current.pending = null;
    setPending(null);
    if (answer.ok) {
      const url = URL.createObjectURL(answer.value);
      setFrameUrl((old) => { if (old) URL.revokeObjectURL(old); return url; });
      current.current.index = wanted;
      setIndex(wanted);
      setNotice(null);
    } else {
      setNotice(answer.problems[0]);          // OQ-17: the position stays on the last frame shown
    }
  }, []);

  const step = (delta: number) => {
    if (!video) return;
    const from = current.current.pending ?? current.current.index;
    const to = Math.min(Math.max(from + delta, 0), count - 1);
    if (to !== from) void showFrame(video.id, to);
  };

  // --- tracking state ---------------------------------------------------------
  const refresh = useCallback(async (id: string) => {
    const answer = await api.tracking(id, known.current.upto, known.current.revision);
    if (!answer.ok || current.current.id !== id) return;
    const t = answer.value;
    if (t.results.from === 0) results.current = new Array(t.run.total_frames).fill(null);
    t.results.items.forEach((item, k) => { results.current[t.results.from + k] = item; });
    known.current = { revision: t.run.revision, upto: t.run.state === "running" ? t.run.current_frame ?? 0 : 0 };
    setTracking({ ...t, results: { from: 0, items: [] } });
    redraw();
  }, []);

  const load = useCallback((v: Video) => {
    player.current?.pause();
    playingNow.current = false;
    setPlaying(false);
    current.current = { id: v.id, index: 0, pending: null };
    results.current = new Array(v.metadata.frame_count).fill(null);
    known.current = { revision: -1, upto: 0 };
    jumpedFor.current = -1;
    setVideo(v); setProblems([]); setNotice(null); setTracking(null); setTool("target"); setIndex(0); setFrameUrl(null);
    void showFrame(v.id, 0);
    void refresh(v.id);
  }, [showFrame, refresh]);

  useEffect(() => { void api.currentVideo().then((answer) => { if (answer.ok) load(answer.value); }); }, [load]);

  const runState = tracking?.run.state ?? "idle";
  useEffect(() => {
    if (!video || runState !== "running") return;
    const timer = window.setInterval(() => void refresh(video.id), 250);
    return () => window.clearInterval(timer);
  }, [video, runState, refresh]);

  // When tracking is lost, go to the frame of the loss so a new box can be drawn there.
  useEffect(() => {
    const run = tracking?.run;
    if (!video || !run || run.lost_at === null || jumpedFor.current === run.revision) return;
    jumpedFor.current = run.revision;
    setTool("target");
    void showFrame(video.id, run.state === "stopped" ? Math.max(run.lost_at - 1, 0) : run.lost_at);
  }, [video, tracking, showFrame]);

  // --- upload -----------------------------------------------------------------
  const onFile = async (file: File | undefined) => {
    if (fileInput.current) fileInput.current.value = "";
    if (!file) return;
    const ask = () => window.confirm(`Replace the loaded video?\n\nThe target box, the lock zone and the tracking results of "${video?.name}" will be discarded.`);
    if (decideUpload(video !== null, ask) === "keep") return;
    const ticket = uploads.current.begin();
    setBusy(true);
    const answer = await api.upload(file);
    if (!uploads.current.isCurrent(ticket)) return;        // a later upload was started: it wins
    setBusy(false);
    if (answer.ok) load(answer.value);
    else setProblems(answer.problems);                     // the loaded video, if any, stays as it was
  };

  // --- boxes and tracking -----------------------------------------------------
  const onBox = async (which: Tool, box: Box) => {
    if (!video) return;
    const answer = which === "target" ? await api.setTarget(video.id, current.current.index, box) : await api.setZone(video.id, box);
    setNotice(answer.ok ? null : answer.problems[0]);
    await refresh(video.id);
  };

  const track = async () => {
    if (!video) return;
    const answer = await api.startTracking(video.id);
    if (!answer.ok) { setNotice(answer.problems[0]); return; }
    known.current = { revision: -1, upto: 0 };
    await refresh(video.id);
  };

  // --- playback ---------------------------------------------------------------
  // The frame number as it is painted on screen right now (updated when React commits).
  const painted = useRef(0);
  useLayoutEffect(() => { painted.current = index; }, [index]);

  // Pause keeps exactly the frame whose number the operator is looking at. It comes from the
  // browser's per-frame notices, not from the player's clock, which can lag on some machines.
  const stop = useCallback(() => {
    const element = player.current;
    if (!element || !video) return;
    playingNow.current = false;                    // ignore any per-frame notice that arrives after this
    element.pause();
    setPlaying(false);
    void showFrame(video.id, Math.min(painted.current, count - 1));
  }, [video, count, showFrame]);

  const play = async () => {
    const element = player.current;
    if (!element || !video) return;
    element.currentTime = (times[index] ?? 0) + 0.001;
    try { await element.play(); playingNow.current = true; setPlaying(true); } catch { setPlaying(false); }
  };

  useEffect(() => {
    const element = player.current;
    if (!playing || !element) return;
    let alive = true;
    const onFrame = (mediaTime: number) => {
      if (!alive || !playingNow.current) return;
      const now = frameAtTime(times, mediaTime);
      if (now !== current.current.index) { current.current.index = now; setIndex(now); }
      schedule();
    };
    const perFrame = typeof (element as any).requestVideoFrameCallback === "function";
    const schedule = () => {
      if (perFrame) (element as any).requestVideoFrameCallback((_: number, info: { mediaTime: number }) => onFrame(info.mediaTime));
      else requestAnimationFrame(() => onFrame(element.currentTime));
    };
    schedule();
    return () => { alive = false; };
  }, [playing, times]);

  // --- what is on screen ------------------------------------------------------
  const result = results.current[index];
  const trackedBox = Array.isArray(result) ? toBox(result) : null;
  const status = tracking ? statusAt(tracking.segments, index) : "not_tracked";
  const targetBox = tracking?.target && tracking.target.frame === index ? toBox(tracking.target.box) : null;
  const zone = tracking?.zone ? toBox(tracking.zone) : null;
  const steps = canStep(pending ?? index, playing ? 0 : count);
  const running = runState === "running";
  const trackLabel = runState === "lost" || runState === "stopped" ? "Resume tracking from this box" : runState === "completed" ? "Track again from the box" : "Start tracking";
  const warnings = [...(video?.warnings ?? []), ...(notice ? [notice] : [])];

  return (
    <div className="flex min-h-full flex-col">
      <header className="flex items-center gap-4 border-b border-graphite-600 bg-graphite-950 px-4 py-2">
        <h1 className="text-[15px] font-bold tracking-wide">Target-lock tracker</h1>
        <span className="truncate text-graphite-400" data-testid="loaded-name">{video ? video.name : "No video loaded"}</span>
        <span className="ml-auto text-graphite-400" data-testid="busy">{busy ? "Uploading and checking the file…" : ""}</span>
        <button className="btn" data-testid="open-video" onClick={() => fileInput.current?.click()}>{video ? "Replace video…" : "Open video…"}</button>
        <input ref={fileInput} type="file" className="hidden" data-testid="upload-input" onChange={(e) => void onFile(e.target.files?.[0])} />
      </header>

      <main className="grid flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex min-w-0 flex-col gap-2">
          <Messages problems={problems} warnings={warnings} />
          <Stage video={video} videoRef={player} fileUrl={video ? api.fileUrl(video.id) : null} frameUrl={frameUrl} playing={playing}
                 trackedBox={trackedBox} status={status} targetBox={targetBox} zone={zone} tool={tool}
                 canDraw={video !== null && !playing && !running} onBox={(t, b) => void onBox(t, b)} onEnded={stop}
                 onOpen={() => fileInput.current?.click()} />

          <div className="panel flex flex-wrap items-center gap-x-4 gap-y-2 px-3 py-2">
            <div className="flex items-center gap-1">
              <button className="btn" data-testid="step-back" disabled={!steps.back} onClick={() => step(-1)}>Step back</button>
              <button className="btn w-16" data-testid="play" disabled={!video} onClick={() => (playing ? stop() : void play())}>{playing ? "Pause" : "Play"}</button>
              <button className="btn" data-testid="step-forward" disabled={!steps.forward} onClick={() => step(1)}>Step forward</button>
            </div>
            <p className="readout" data-testid="position" data-index={video ? index : ""}>
              {video ? <>Frame <span data-testid="frame-number">{formatCount(frameNumber(index))}</span> / <span data-testid="frame-total">{formatCount(count)}</span>
                <span className="ml-3 text-graphite-400" data-testid="frame-time">{formatClock(frameTime(index, meta!.fps.num, meta!.fps.den))}</span></> : "No frame"}
            </p>
            <div className="ml-auto flex items-center gap-1">
              <span className="mr-1 text-graphite-400">Draw</span>
              <button className="btn" data-testid="tool-target" aria-pressed={tool === "target"} disabled={!video} onClick={() => setTool("target")}>Target box</button>
              <button className="btn" data-testid="tool-zone" aria-pressed={tool === "zone"} disabled={!video} onClick={() => setTool("zone")}>Lock zone</button>
              <button className="btn ml-3" data-testid="track" disabled={!video || !tracking?.target || running} onClick={() => void track()}>{trackLabel}</button>
            </div>
            <input type="range" className="scrub basis-full" data-testid="slider" aria-label="Frame" min={0} max={Math.max(count - 1, 0)} step={1}
                   value={pending ?? index} disabled={!video || playing} onChange={(e) => video && void showFrame(video.id, Number(e.target.value))} />
          </div>

          <Timeline segments={tracking?.segments ?? []} frameCount={count} index={index} duration={meta?.duration_seconds ?? 0} />
        </div>

        <aside className="flex flex-col gap-3">
          <StatusPanel status={status} run={tracking?.run ?? null} />
          <AnalyticsPanel analytics={tracking?.analytics ?? null} />
          <MetadataPanel video={video} />
        </aside>
      </main>
    </div>
  );
}
