import { X } from "lucide-react";
import type { Snapshot } from "../types";
import { actions } from "../lib/api";
import { fmtUsd, fmtPrice, fmtSigned } from "../lib/format";

export default function PositionsTable({ s }: { s: Snapshot }) {
  const rows = s.positions;
  return (
    <div className="panel panel-pad">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold">Open Positions</h2>
        <span className="chip bg-ink-700/60 text-slate-300">{rows.length}</span>
      </div>
      {rows.length === 0 ? (
        <div className="py-8 text-center text-sm text-slate-500">Flat — no open positions. The bot is scanning for setups.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink-700 text-[11px] uppercase tracking-wider text-slate-400">
                <th className="py-2 pr-3 font-semibold">Symbol</th>
                <th className="py-2 pr-3 font-semibold">Side</th>
                <th className="py-2 pr-3 text-right font-semibold">Size</th>
                <th className="py-2 pr-3 text-right font-semibold">Entry</th>
                <th className="py-2 pr-3 text-right font-semibold">Mark</th>
                <th className="py-2 pr-3 text-right font-semibold">uPnL</th>
                <th className="py-2 pr-3 font-semibold">Strat</th>
                <th className="py-2 pr-3 text-right font-semibold">SL / TP</th>
                <th className="py-2 text-right font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => {
                const up = p.unrealized >= 0;
                return (
                  <tr key={p.symbol} className="border-b border-ink-800 last:border-0 hover:bg-ink-800/40">
                    <td className="py-2.5 pr-3 font-semibold text-slate-100">{p.symbol}</td>
                    <td className="py-2.5 pr-3">
                      <span className={`chip ${p.side === "LONG" ? "bg-emerald-500/15 text-emerald-300" : "bg-rose-500/15 text-rose-300"}`}>
                        {p.side} {p.leverage}x
                      </span>
                    </td>
                    <td className="num py-2.5 pr-3 text-right text-slate-200">{p.qty}</td>
                    <td className="num py-2.5 pr-3 text-right text-slate-300">{fmtPrice(p.entry)}</td>
                    <td className="num py-2.5 pr-3 text-right text-slate-300">{fmtPrice(p.price)}</td>
                    <td className={`num py-2.5 pr-3 text-right font-semibold ${up ? "text-emerald-400" : "text-rose-400"}`}>
                      {fmtSigned(p.unrealized)}
                      <div className="text-[11px] opacity-80">{fmtSigned(p.pnl_pct)}%</div>
                    </td>
                    <td className="py-2.5 pr-3 text-xs text-slate-400">{p.strategy}</td>
                    <td className="num py-2.5 pr-3 text-right text-[11px] text-slate-400">
                      {p.stop_loss ? fmtPrice(p.stop_loss) : "—"} / {p.take_profit ? fmtPrice(p.take_profit) : "—"}
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        className="rounded-md border border-rose-500/40 bg-rose-500/10 p-1.5 text-rose-300 transition hover:bg-rose-500/20"
                        title={`Close ${p.symbol}`}
                        onClick={() => actions.closePosition(p.symbol)}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
