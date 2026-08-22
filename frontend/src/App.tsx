import { useEffect, useState } from "react";
import { useBotState } from "./lib/api";
import Header from "./components/Header";
import StatCards from "./components/StatCards";
import EquityChart from "./components/EquityChart";
import CandleChart from "./components/CandleChart";
import PositionsTable from "./components/PositionsTable";
import TradesTable from "./components/TradesTable";
import LogFeed from "./components/LogFeed";
import ControlPanel from "./components/ControlPanel";
import SignalCards from "./components/SignalCards";

export default function App() {
  const { snapshot: s, connected } = useBotState();
  const [symbol, setSymbol] = useState<string>("");
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    if (!s || symbol || s.symbols.length === 0) return;
    setSymbol(s.symbols[0]);
  }, [s, symbol]);

  const cfgKey = s ? `${s.strategy}|${s.symbols.join(",")}` : "";
  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => {});
  }, [cfgKey]);

  if (!s) {
    return (
      <div className="grid min-h-screen place-items-center">
        <div className="text-center">
          <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
          <p className="text-sm text-slate-400">Connecting to AutoTrader engine…</p>
        </div>
      </div>
    );
  }

  const candles = s.candles[symbol] ?? [];
  const price = s.prices[symbol] ?? 0;

  return (
    <div className="mx-auto max-w-[1600px] px-3 py-4 sm:px-5 sm:py-5">
      <Header s={s} ws={connected} />

      <div className="mb-4">
        <StatCards s={s} />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* main column */}
        <div className="flex flex-col gap-4 xl:col-span-2">
          <EquityChart s={s} />

          {/* price chart */}
          <div className="panel panel-pad">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <h2 className="text-sm font-bold">Price · {symbol}</h2>
              <div className="ml-auto flex flex-wrap gap-1">
                {s.symbols.map((sym) => (
                  <button
                    key={sym}
                    onClick={() => setSymbol(sym)}
                    className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                      sym === symbol ? "bg-sky-500 text-sky-950" : "bg-ink-800 text-slate-300 hover:bg-ink-700"
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[300px] w-full">
              <CandleChart candles={candles} price={price} symbol={symbol} />
            </div>
          </div>

          <SignalCards s={s} />
          <PositionsTable s={s} />
          <TradesTable s={s} />
        </div>

        {/* side column */}
        <div className="flex flex-col gap-4">
          <ControlPanel s={s} config={config} />
          <LogFeed s={s} />
        </div>
      </div>

      <footer className="mt-6 flex flex-wrap items-center justify-between gap-2 pb-4 text-[11px] text-slate-500">
        <span>
          AutoTrader v{s.version} · {s.mode === "live" ? "Binance Futures Testnet" : "Simulation Engine"} ·
          {s.auto_strategy ? " dynamic strategy rotation" : ` strategy: ${s.strategy}`}
        </span>
        <span className="num">started {new Date(s.started_at).toLocaleTimeString()}</span>
      </footer>
    </div>
  );
}
