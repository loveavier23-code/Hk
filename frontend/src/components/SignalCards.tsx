import { ArrowDownRight, ArrowUpRight, Minus, Radar } from "lucide-react";
import type { Snapshot } from "../types";
import { fmtPrice, fmtSigned } from "../lib/format";

export default function SignalCards({ s }: { s: Snapshot }) {
  const symbols = s.symbols;
  return (
    <div className="panel panel-pad">
      <div className="mb-3 flex items-center gap-2">
        <Radar className="h-4 w-4 text-sky-400" />
        <h2 className="text-sm font-bold">Market Scanner &amp; Signals</h2>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {symbols.map((sym) => {
          const price = s.prices[sym] ?? 0;
          const candles = s.candles[sym] ?? [];
          const lookback = candles.slice(-25);
          const ref = lookback[0]?.[4] ?? price;
          const chg = ref ? ((price - ref) / ref) * 100 : 0;
          const sig = s.signals[sym];
          const strat = s.active_strategy[sym] ?? s.strategy;
          const side = sig?.side ?? "flat";
          const SideIcon = side === "long" ? ArrowUpRight : side === "short" ? ArrowDownRight : Minus;
          const sideColor = side === "long" ? "text-emerald-400" : side === "short" ? "text-rose-400" : "text-slate-400";
          const barColor = side === "long" ? "bg-emerald-400" : side === "short" ? "bg-rose-400" : "bg-slate-500";
          const strength = sig?.strength ?? 0;
          return (
            <div key={sym} className="rounded-xl border border-ink-700 bg-ink-900/50 p-3">
              <div className="flex items-center justify-between">
                <div className="font-bold text-slate-100">{sym}</div>
                <div className="text-right">
                  <div className="num text-sm font-semibold text-slate-100">{fmtPrice(price)}</div>
                  <div className={`num text-[11px] ${chg >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{fmtSigned(chg)}%</div>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-bold uppercase ${sideColor} bg-ink-800`}>
                  <SideIcon className="h-3 w-3" /> {side}
                </span>
                <span className="chip bg-ink-800 text-[10px] text-slate-300">{strat}</span>
                <div className="ml-auto h-1.5 w-16 overflow-hidden rounded-full bg-ink-700">
                  <div className={`h-full ${barColor}`} style={{ width: `${Math.round(strength * 100)}%` }} />
                </div>
              </div>
              <div className="mt-1.5 line-clamp-2 text-[11px] text-slate-400">{sig?.reason ?? "no signal"}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
