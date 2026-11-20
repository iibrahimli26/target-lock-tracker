// The picture area. Three layers: the browser's video player (shown while
// playing), the exact frame decoded by the backend (shown while stopped), and
// a canvas on top for the lock zone, the boxes and drawing with the mouse.
import { type PointerEvent, type RefObject, useCallback, useEffect, useRef, useState } from "react";
import type { Video } from "../api";
import type { Status } from "../lib/flow";
import { type Box, type Handle, type Point, boxFromDrag, clampPoint, hitTest, moveBox, resizeBox, toPicture, toScreen } from "../lib/geometry";
import { STATUS_COLOR, STATUS_TEXT } from "./Panels";

export type Tool = "target" | "zone";
const ZONE_COLOR = "#9FB7D6";

interface Props {
  video: Video | null;
  videoRef: RefObject<HTMLVideoElement>;
  fileUrl: string | null;
  frameUrl: string | null;
  playing: boolean;
  trackedBox: Box | null;       // the tracker's box for the frame on screen
  status: Status;
  targetBox: Box | null;        // the operator's box, when it belongs to the frame on screen
  zone: Box | null;
  tool: Tool;
  canDraw: boolean;
  onBox: (tool: Tool, box: Box) => void;
  onEnded: () => void;
  onOpen: () => void;
}

type Drag = { kind: "draw"; anchor: Point } | { kind: Handle; origin: Box; from: Point };

export function Stage(p: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const drag = useRef<Drag | null>(null);
  const [draft, setDraft] = useState<Box | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const picture = p.video ? { width: p.video.metadata.width, height: p.video.metadata.height } : { width: 16, height: 9 };
  const scale = size.width / picture.width || 1;

  useEffect(() => {
    if (!wrap.current) return;
    const observer = new ResizeObserver(([entry]) => setSize({ width: entry.contentRect.width, height: entry.contentRect.height }));
    observer.observe(wrap.current);
    return () => observer.disconnect();
  }, [p.video?.id]);

  const editable = p.tool === "target" ? p.targetBox : p.zone;

  const draw = useCallback(() => {
    const c = canvas.current;
    if (!c) return;
    const ratio = window.devicePixelRatio || 1;
    c.width = Math.round(size.width * ratio);
    c.height = Math.round(size.height * ratio);
    const g = c.getContext("2d")!;
    g.setTransform(ratio, 0, 0, ratio, 0, 0);
    g.clearRect(0, 0, size.width, size.height);
    g.font = '11px "B612", Verdana, sans-serif';
    g.textBaseline = "bottom";

    const rect = (box: Box, color: string, dash: number[], width: number) => {
      const s = toScreen(box, scale);
      g.setLineDash(dash); g.lineWidth = width; g.strokeStyle = color;
      g.strokeRect(Math.round(s.x) + 0.5, Math.round(s.y) + 0.5, Math.round(s.w), Math.round(s.h));
      g.setLineDash([]);
      return s;
    };
    const corners = (s: Box, color: string, arm: number) => {      // corner brackets, as on a head-up display
      g.strokeStyle = color; g.lineWidth = 2; g.beginPath();
      for (const [cx, cy, dx, dy] of [[s.x, s.y, 1, 1], [s.x + s.w, s.y, -1, 1], [s.x, s.y + s.h, 1, -1], [s.x + s.w, s.y + s.h, -1, -1]]) {
        g.moveTo(cx + dx * arm, cy); g.lineTo(cx, cy); g.lineTo(cx, cy + dy * arm);
      }
      g.stroke();
    };
    const label = (s: Box, text: string, color: string) => {
      const w = g.measureText(text).width + 8;
      const y = s.y >= 16 ? s.y : s.y + s.h + 16;
      g.fillStyle = "rgba(21,24,27,0.85)"; g.fillRect(s.x, y - 15, w, 15);
      g.fillStyle = color; g.fillText(text, s.x + 4, y - 2);
    };

    const zone = p.tool === "zone" && draft ? draft : p.zone;
    if (zone) { const s = rect(zone, ZONE_COLOR, [6, 4], 1); corners(s, ZONE_COLOR, 12); label(s, "Lock zone", ZONE_COLOR); }
    if (p.trackedBox && !(p.tool === "target" && draft)) {
      const color = STATUS_COLOR[p.status];
      const s = rect(p.trackedBox, color, [], 2); corners(s, color, 8); label(s, STATUS_TEXT[p.status], color);
    }
    const target = p.tool === "target" && draft ? draft : p.targetBox;
    if (target && !p.playing) {
      const s = rect(target, "#FFFFFF", p.trackedBox ? [3, 3] : [], 1);
      g.fillStyle = "#FFFFFF";
      for (const [cx, cy] of [[s.x, s.y], [s.x + s.w, s.y], [s.x, s.y + s.h], [s.x + s.w, s.y + s.h]]) g.fillRect(cx - 3, cy - 3, 6, 6);
      if (!p.trackedBox) label(s, "Target", "#FFFFFF");
    }
  }, [size, scale, draft, p.zone, p.trackedBox, p.targetBox, p.status, p.tool, p.playing]);

  useEffect(draw, [draw]);

  const point = (e: PointerEvent): Point => {
    const r = canvas.current!.getBoundingClientRect();
    return clampPoint(toPicture({ x: e.clientX - r.left, y: e.clientY - r.top }, scale), picture);
  };
  const down = (e: PointerEvent) => {
    if (!p.canDraw) return;
    const at = point(e);
    const handle = editable ? hitTest(editable, at, 10 / scale) : null;
    drag.current = handle && editable ? { kind: handle, origin: editable, from: at } : { kind: "draw", anchor: at };
    canvas.current!.setPointerCapture(e.pointerId);
  };
  const move = (e: PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    const at = point(e);
    if (d.kind === "draw") setDraft(boxFromDrag(d.anchor, at));
    else if (d.kind === "move") setDraft(moveBox(d.origin, at.x - d.from.x, at.y - d.from.y, picture));
    else setDraft(resizeBox(d.origin, d.kind, at, picture));
  };
  const up = () => {
    if (drag.current && draft && (draft.w > 0 || draft.h > 0)) p.onBox(p.tool, draft);
    drag.current = null;
    setDraft(null);
  };

  if (!p.video) {
    return (
      <div className="panel flex min-h-[320px] flex-1 flex-col items-center justify-center gap-3 px-6 text-center" data-testid="stage-empty">
        <p className="text-[15px]">Open a drone video to begin.</p>
        <p className="max-w-md text-graphite-400">MP4 with H.264 video, landscape or square, up to 921,600 pixels per frame (for example 1280 × 720) and 1 GB.</p>
        <button className="btn" onClick={p.onOpen}>Open video…</button>
      </div>
    );
  }
  return (
    <div className="flex justify-center bg-graphite-950 border border-graphite-600">
      <div ref={wrap} data-testid="stage" className="relative w-full select-none"
           style={{ aspectRatio: `${picture.width} / ${picture.height}`, maxWidth: `calc(58vh * ${picture.width / picture.height})` }}>
        <video ref={p.videoRef} src={p.fileUrl ?? undefined} muted playsInline preload="auto" onEnded={p.onEnded}
               className="absolute inset-0 h-full w-full" data-testid="player" />
        {p.frameUrl && !p.playing && (
          <img src={p.frameUrl} alt="" draggable={false} className="absolute inset-0 h-full w-full" data-testid="frame-image" />
        )}
        <canvas ref={canvas} data-testid="overlay" className="absolute inset-0 h-full w-full touch-none"
                style={{ cursor: p.canDraw ? "crosshair" : "default" }}
                onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} />
      </div>
    </div>
  );
}
