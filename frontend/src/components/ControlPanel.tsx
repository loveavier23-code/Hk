import { useEffect, useState } from "react";
import { Sliders, Check, Pencil } from "lucide-react";
import type { Snapshot } from "../types";
import { actions } from "../lib/api";

const STRATEGIES = [
  { id: "auto", label: "Auto (dynamic)" },
  { id: "ema_cross", label: "EMA Cross" },
  { id: "rsi_momentum", label: "RSI Momentum" },
  { id: "macd", label: "MACD" },
  { id: "mean_reversion", label: "Mean Reversion" },
  { id: "grid", label: "Grid" },
];

interface Form {
  leverage: number;
  risk_per_trade_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  trailing_stop_pct: number;
  max_positions: number;
  max_drawdown_pct: number;
  symbols: string;
}

export default function ControlPanel({ s, config }: { s: Snapshot; config: any }) {
  const [form, setForm] = useState<Form>({
    leverage: config?.leverage ?? 10,
    risk_per_trade_pct: config?.risk_per_trade_pct ?? 2,
    stop_loss_pct: config?.stop_loss_pct ?? 2.5,
    take_profit_pct: config?.take_profit_pct ?? 5,
    trailing_stop_pct: config?.trailing_stop_pct ?? 0,
    max_positions: config?.max_positions ?? 3,
    max_drawdown_pct: config?.max_drawdown_pct ?? 12,
    symbols: (config?.symbols ?? s.symbols).join(", "),
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!config) return;
    setForm((f) => ({
      ...f,
      leverage: config.leverage,
      risk_per_trade_pct: config.risk_per_trade_pct,
      stop_loss_pct: config.stop_loss_pct,
      take_profit_pct: config.take_profit_pct,
      trailing_stop_pct: config.trailing_stop_pct,
      max_positions: config.max_positions,
      max_drawdown_pct: config.max_drawdown_pct,
    }));
  }, [config]);

  const set = (k: keyof Form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const apply = async () => {
    await actions.updateConfig({
      leverage: Number(form.leverage),
      risk_per_trade_pct: Number(form.risk_per_trade_pct),
      stop_loss_pct: Number(form.stop_loss_pct),
      take_profit_pct: Number(form.take_profit_pct),
      trailing_stop_pct: Number(form.trailing_stop_pct),
      max_positions: Number(form.max_positions),
      max_drawdown_pct: Number(form.max_drawdown_pct),
      symbols: form.symbols.split(",").map((x) => x.trim().toUpperCase()).filter(Boolean),
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const numField = (k: keyof Form, label: string, step = "0.5") => (
    <label className="block">
      <span className="label">{label}</span>
      <input
        type="number"
        step={step}
        className="input num mt-1"
        value={form[k]}
        onChange={(e) => set(k, e.target.value)}
      />
    </label>
  );

  return (
    <div className="panel panel-pad">
      <div className="mb-3 flex items-center gap-2">
        <Sliders className="h-4 w-4 text-sky-400" />
        <h2 className="text-sm font-bold">Strategy &amp; Risk</h2>
      </div>

      {/* Strategy */}
      <div className="mb-4">
        <span className="label">Active Strategy</span>
        <div className="mt-1.5 grid grid-cols-2 gap-1.5">
          {STRATEGIES.map((st) => {
            const active = s.strategy === st.id;
            return (
              <button
                key={st.id}
                onClick={() => actions.updateConfig({ strategy: st.id })}
                className={`rounded-lg border px-2.5 py-2 text-left text-xs font-semibold transition ${
                  active
                    ? "border-sky-500/60 bg-sky-500/15 text-sky-200"
                    : "border-ink-700 bg-ink-900/50 text-slate-300 hover:border-ink-600"
                }`}
              >
                {st.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Risk grid */}
      <div className="grid grid-cols-2 gap-2.5">
        {numField("leverage", "Leverage (x)", "1")}
        {numField("risk_per_trade_pct", "Risk / Trade %", "0.5")}
        {numField("stop_loss_pct", "Stop Loss %", "0.5")}
        {numField("take_profit_pct", "Take Profit %", "0.5")}
        {numField("trailing_stop_pct", "Trailing Stop %", "0.5")}
        {numField("max_positions", "Max Positions", "1")}
        {numField("max_drawdown_pct", "Max Drawdown %", "1")}
        <label className="col-span-2 block">
          <span className="label inline-flex items-center gap-1"><Pencil className="h-3 w-3" /> Symbols (comma separated)</span>
          <input className="input num mt-1" value={form.symbols} onChange={(e) => set("symbols", e.target.value)} />
        </label>
      </div>

      <button className={`mt-3 w-full ${saved ? "btn-ghost" : "btn-primary"}`} onClick={apply}>
        {saved ? (
          <>
            <Check className="h-4 w-4" /> Applied
          </>
        ) : (
          "Apply Configuration"
        )}
      </button>
      <p className="mt-2 text-[11px] text-slate-500">
        Changes apply live. Trailing stop only activates above 0%. The bot auto-trades within these limits.
      </p>
    </div>
  );
}
