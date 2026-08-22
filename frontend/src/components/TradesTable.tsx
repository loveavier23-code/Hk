import type { Snapshot } from "../types";
import { fmtPrice, fmtSigned, fmtClock } from "../lib/format";

export default function TradesTable({ s }: { s: Snapshot }) {
  const rows = s.trades.slice(0, 40);
  return (
    <div className="panel panel-pad">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold">Trade History</h2>
        <span className="chip bg-ink-700/60 text-slate-300">{s.trades.length}</span>
      </div>
      <div className="max-h-80 overflow-y-auto">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-ink-850/95">
            <tr className="border-b border-ink-700 text-[11px] uppercase tracking-wider text-slate-400">
              <th className="py-2 pr-3 font-semibold">Time</th>
              <th className="py-2 pr-3 font-semibold">Symbol</th>
              <th className="py-2 pr-3 font-semibold">Action</th>
              <th className="py-2 pr-3 text-right font-semibold">Qty</th>
              <th className="py-2 pr-3 text-right font-semibold">Price</th>
              <th className="py-2 pr-3 text-right font-semibold">PnL</th>
              <th className="py-2 font-semibold">Reason</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500">No trades yet.</td>
              </tr>
            ) : (
              rows.map((t) => {
                const open = t.action === "OPEN";
                const win = t.pnl > 0;
                return (
                  <tr key={t.id} className="border-b border-ink-800 last:border-0 hover:bg-ink-800/40">
                    <td className="num py-2 pr-3 text-xs text-slate-400">{fmtClock(t.t)}</td>
                    <td className="py-2 pr-3 font-semibold text-slate-200">{t.symbol}</td>
                    <td className="py-2 pr-3">
                      <span className={`chip text-[10px] ${open ? "bg-sky-500/15 text-sky-300" : win ? "bg-emerald-500/15 text-emerald-300" : "bg-rose-500/15 text-rose-300"}`}>
                        {t.action} {t.side}
                      </span>
                    </td>
                    <td className="num py-2 pr-3 text-right text-slate-300">{t.qty}</td>
                    <td className="num py-2 pr-3 text-right text-slate-300">{fmtPrice(t.price)}</td>
                    <td className={`num py-2 pr-3 text-right font-semibold ${t.action === "OPEN" ? "text-slate-500" : win ? "text-emerald-400" : "text-rose-400"}`}>
                      {t.action === "CLOSE" ? fmtSigned(t.pnl) : "—"}
                    </td>
                    <td className="py-2 text-xs text-slate-400">{t.reason}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
