import { useMemo } from "react";
import { useState } from "react";

interface Props {
  candles: number[][]; // [t,o,h,l,c,v][]
  price: number;
  symbol: string;
}

const VIEW_W = 720;
const VIEW_H = 300;
const PAD_R = 62;

export default function CandleChart({ candles, price, symbol }: Props) {
  const [hover, setHover] = useState<number | null>(null);

  const view = useMemo(() => {
    const all = candles.slice(-90);
    if (!all.length) return null;
    const highs = all.map((c) => c[2]);
    const lows = all.map((c) => c[3]);
    const max = Math.max(...highs);
    const min = Math.min(...lows);
    const range = max - min || 1;
    const pad = range * 0.12;
    const top = max + pad;
    const bot = min - pad;
    const span = top - bot;
    const chartW = VIEW_W - PAD_R;
    const cw = chartW / all.length;
    const bodyW = Math.max(cw * 0.62, 1.5);
    const y = (p: number) => ((top - p) / span) * (VIEW_H - 16) + 8;

    const bars = all.map((c, i) => {
      const [t, o, h, l, cl] = c;
      const up = cl >= o;
      const x = i * cw + cw / 2;
      return {
        x, o, h, l, c: cl, up, t,
        yO: y(o), yC: y(cl), yH: y(h), yL: y(l),
        bodyW, bodyTop: y(Math.max(o, cl)), bodyH: Math.max(Math.abs(y(o) - y(cl)), 1),
      };
    });
    // gridlines (5)
    const grid = Array.from({ length: 5 }, (_, i) => {
      const p = top - (span * i) / 4;
      return { y: y(p), p };
    });
    return { bars, grid, top, bot, y, priceY: y(price) };
  }, [candles, price]);

  if (!view) {
    return <div className="grid h-full place-items-center text-sm text-slate-500">No chart data</div>;
  }

  const lastUp = view.bars[view.bars.length - 1].up;

  return (
    <div className="relative h-full w-full">
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        preserveAspectRatio="none"
        className="h-full w-full"
        onMouseLeave={() => setHover(null)}
      >
        {/* grid */}
        {view.grid.map((g, i) => (
          <g key={i}>
            <line x1={0} x2={VIEW_W - PAD_R} y1={g.y} y2={g.y} stroke="#141a2b" strokeWidth={1} />
            <text x={VIEW_W - PAD_R + 6} y={g.y + 3} fill="#64748b" fontSize={10} className="num">
              {g.p >= 1000 ? g.p.toFixed(0) : g.p.toFixed(g.p < 1 ? 4 : 2)}
            </text>
          </g>
        ))}

        {/* candles */}
        {view.bars.map((b, i) => {
          const color = b.up ? "#34d399" : "#fb7185";
          return (
            <g
              key={i}
              onMouseEnter={() => setHover(i)}
            >
              <line x1={b.x} x2={b.x} y1={b.yH} y2={b.yL} stroke={color} strokeWidth={1} />
              <rect
                x={b.x - b.bodyW / 2}
                y={b.bodyTop}
                width={b.bodyW}
                height={b.bodyH}
                fill={color}
                opacity={hover === null || hover === i ? 1 : 0.55}
              />
            </g>
          );
        })}

        {/* last price line */}
        <line x1={0} x2={VIEW_W - PAD_R} y1={view.priceY} y2={view.priceY} stroke={lastUp ? "#34d399" : "#fb7185"} strokeWidth={1} strokeDasharray="3 3" opacity={0.7} />
        <rect x={VIEW_W - PAD_R} y={view.priceY - 9} width={PAD_R} height={18} fill={lastUp ? "#10b981" : "#e11d48"} />
        <text x={VIEW_W - PAD_R + 5} y={view.priceY + 4} fill="#06121c" fontSize={11} fontWeight={700} className="num">
          {price >= 1000 ? price.toFixed(2) : price.toFixed(price < 1 ? 4 : 3)}
        </text>
      </svg>

      {hover !== null && view.bars[hover] && (
        <div className="pointer-events-none absolute left-2 top-2 rounded-lg border border-ink-600 bg-ink-900/90 px-3 py-2 text-[11px] shadow-lg">
          <div className="num">
            <span className="text-slate-400">O</span> {view.bars[hover].o.toFixed(2)}{"  "}
            <span className="text-slate-400">H</span> {view.bars[hover].h.toFixed(2)}{"  "}
            <span className="text-slate-400">L</span> {view.bars[hover].l.toFixed(2)}{"  "}
            <span className="text-slate-400">C</span> {view.bars[hover].c.toFixed(2)}
          </div>
        </div>
      )}
    </div>
  );
}
