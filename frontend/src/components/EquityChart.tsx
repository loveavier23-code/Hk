import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, YAxis, XAxis, ReferenceLine } from "recharts";
import type { Snapshot } from "../types";
import { fmtUsd, fmtClock } from "../lib/format";

export default function EquityChart({ s }: { s: Snapshot }) {
  const data = useMemo(
    () => s.equity_curve.map((p) => ({ t: p.t, equity: p.equity })),
    [s.equity_curve]
  );
  const init = s.account.initial_equity || 10000;
  const min = data.length ? Math.min(...data.map((d) => d.equity), init) : init;
  const max = data.length ? Math.max(...data.map((d) => d.equity), init) : init;
  const pad = (max - min) * 0.15 || init * 0.02;
  const up = s.account.equity >= init;

  return (
    <div className="panel panel-pad">
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-100">Equity Curve</h2>
          <p className="text-[11px] text-slate-400">wallet equity over time</p>
        </div>
        <div className="text-right">
          <div className={`num text-xl font-bold ${up ? "text-emerald-400" : "text-rose-400"}`}>{fmtUsd(s.account.equity)}</div>
          <div className={`num text-xs ${up ? "text-emerald-400" : "text-rose-400"}`}>
            {s.account.roi_pct >= 0 ? "+" : ""}
            {s.account.roi_pct.toFixed(2)}%
          </div>
        </div>
      </div>
      <div className="h-44">
        {data.length < 2 ? (
          <div className="grid h-full place-items-center text-sm text-slate-500">Collecting data…</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 6, right: 6, left: 6, bottom: 0 }}>
              <defs>
                <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={up ? "#34d399" : "#fb7185"} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={up ? "#34d399" : "#fb7185"} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="t" tickFormatter={(t) => fmtClock(t).slice(0, 5)} tick={{ fill: "#64748b", fontSize: 10 }} stroke="#1b2236" minTickGap={40} />
              <YAxis domain={[min - pad, max + pad]} tick={{ fill: "#64748b", fontSize: 10 }} stroke="#1b2236" width={52} tickFormatter={(v) => fmtUsd(v, 0)} />
              <ReferenceLine y={init} stroke="#475569" strokeDasharray="4 4" />
              <Tooltip
                contentStyle={{ background: "#0b0f1a", border: "1px solid #1b2236", borderRadius: 10, fontSize: 12 }}
                labelFormatter={(t) => fmtClock(Number(t))}
                formatter={(v: number) => [fmtUsd(v), "Equity"]}
              />
              <Area type="monotone" dataKey="equity" stroke={up ? "#34d399" : "#fb7185"} strokeWidth={2} fill="url(#eq)" isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
