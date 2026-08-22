import { TrendingUp, TrendingDown, Wallet, LineChart, Percent, Gauge, BarChart3, Target } from "lucide-react";
import type { Snapshot } from "../types";
import { fmtUsd, fmtPct, fmtSigned } from "../lib/format";

function Card({
  label,
  value,
  sub,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "up" | "down" | "neutral" | "sky";
  icon: React.ReactNode;
}) {
  const toneCls =
    tone === "up"
      ? "text-emerald-400"
      : tone === "down"
      ? "text-rose-400"
      : tone === "sky"
      ? "text-sky-400"
      : "text-slate-100";
  return (
    <div className="panel panel-pad">
      <div className="flex items-center justify-between">
        <span className="label">{label}</span>
        <span className="text-slate-500">{icon}</span>
      </div>
      <div className={`num mt-2 text-2xl font-bold ${toneCls}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

export default function StatCards({ s }: { s: Snapshot }) {
  const a = s.account;
  const closes = s.trades.filter((t) => t.action === "CLOSE");
  const wins = closes.filter((t) => t.pnl > 0).length;
  const winRate = closes.length ? (wins / closes.length) * 100 : 0;
  const upnlTone = a.unrealized >= 0 ? "up" : "down";
  const realTone = a.realized >= 0 ? "up" : "down";
  const roiTone = a.roi_pct >= 0 ? "up" : "down";

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
      <Card label="Equity" value={fmtUsd(a.equity)} sub={`Start ${fmtUsd(a.initial_equity)}`} tone="sky" icon={<Wallet className="h-4 w-4" />} />
      <Card
        label="Unrealized PnL"
        value={fmtSigned(a.unrealized)}
        sub="open positions"
        tone={upnlTone}
        icon={a.unrealized >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
      />
      <Card
        label="Realized PnL"
        value={fmtSigned(a.realized)}
        sub={`${closes.length} closed trades`}
        tone={realTone}
        icon={<LineChart className="h-4 w-4" />}
      />
      <Card label="Return (ROI)" value={fmtPct(a.roi_pct)} sub={`Peak ${fmtUsd(a.peak_equity)}`} tone={roiTone} icon={<Percent className="h-4 w-4" />} />
      <Card label="Drawdown" value={`-${a.drawdown_pct.toFixed(2)}%`} sub={`limit -${0}%`} tone="down" icon={<Gauge className="h-4 w-4" />} />
      <Card
        label="Win Rate"
        value={`${winRate.toFixed(0)}%`}
        sub={`${wins}/${closes.length} · ${s.positions.length} open`}
        tone="neutral"
        icon={<Target className="h-4 w-4" />}
      />
    </div>
  );
}

export function MiniStat({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-ink-700 bg-ink-900/50 px-3 py-1.5">
      <span className="text-slate-400">{icon}</span>
      <div>
        <div className="label">{label}</div>
        <div className="num text-sm font-semibold text-slate-100">{value}</div>
      </div>
    </div>
  );
}
