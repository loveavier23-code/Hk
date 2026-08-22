import { Activity, Pause, Play, ShieldAlert, Wifi, WifiOff, XOctagon, RotateCcw } from "lucide-react";
import type { Snapshot } from "../types";
import { actions } from "../lib/api";
import { fmtClock } from "../lib/format";

export default function Header({ s, ws }: { s: Snapshot; ws: boolean }) {
  const live = s.mode === "live";
  return (
    <header className="panel panel-pad mb-4 flex flex-wrap items-center gap-3 sm:gap-4">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-sky-500 to-emerald-500 text-white shadow-lg shadow-sky-500/30">
          <Activity className="h-6 w-6" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-lg font-extrabold leading-tight tracking-tight">AutoTrader</h1>
          <p className="text-[11px] uppercase tracking-widest text-slate-400">Binance Futures · Autonomous Bot</p>
        </div>
      </div>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        {/* Mode badge */}
        <span
          className={`chip ${
            live ? "bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30" : "bg-amber-500/15 text-amber-300 ring-1 ring-amber-500/30"
          }`}
          title={live ? "Trading on Binance Futures testnet" : "Simulated market — Binance unreachable from this host"}
        >
          {live ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          {live ? "LIVE · TESTNET" : "SIMULATION"}
        </span>

        {/* WS link */}
        <span className={`chip ${ws ? "bg-sky-500/10 text-sky-300" : "bg-rose-500/10 text-rose-300"}`}>
          <span className={`h-2 w-2 rounded-full ${ws ? "bg-sky-400 animate-pulseDot" : "bg-rose-400"}`} />
          {ws ? "stream" : "offline"}
        </span>

        {/* Bot running state */}
        {s.halted ? (
          <span className="chip bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/30">
            <ShieldAlert className="h-3.5 w-3.5" /> HALTED · DD
          </span>
        ) : s.running ? (
          <span className="chip bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulseDot" /> RUNNING
          </span>
        ) : (
          <span className="chip bg-slate-500/15 text-slate-300 ring-1 ring-slate-500/30">PAUSED</span>
        )}

        <span className="num hidden text-xs text-slate-400 sm:inline">{fmtClock(s.server_time)} UTC</span>

        <div className="ml-1 flex items-center gap-1.5">
          {s.running ? (
            <button className="btn-ghost" onClick={actions.stop} title="Pause trading">
              <Pause className="h-4 w-4" /> Pause
            </button>
          ) : (
            <button className="btn-primary" onClick={actions.start} title="Resume trading">
              <Play className="h-4 w-4" /> Start
            </button>
          )}
          <button className="btn-ghost" onClick={actions.closeAll} title="Flatten all positions">
            <XOctagon className="h-4 w-4" /> Close All
          </button>
          {!live && (
            <button className="btn-ghost" onClick={actions.reset} title="Reset simulated account">
              <RotateCcw className="h-4 w-4" /> Reset
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
