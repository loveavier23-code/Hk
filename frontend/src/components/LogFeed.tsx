import { useEffect, useRef } from "react";
import type { Snapshot } from "../types";
import { fmtClock } from "../lib/format";

const levelColor: Record<string, string> = {
  INFO: "text-sky-300",
  WARNING: "text-amber-300",
  ERROR: "text-rose-300",
  DEBUG: "text-slate-500",
};

export default function LogFeed({ s }: { s: Snapshot }) {
  const ref = useRef<HTMLDivElement>(null);
  const logs = s.logs;
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = 0;
  }, [logs.length]);

  return (
    <div className="panel panel-pad flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold">Activity Log</h2>
        <span className="chip bg-ink-700/60 text-slate-300">{logs.length}</span>
      </div>
      <div ref={ref} className="num h-72 overflow-y-auto pr-1 text-[11px] leading-relaxed lg:h-full lg:max-h-[26rem]">
        {logs.length === 0 ? (
          <div className="py-6 text-center text-slate-500">Waiting for events…</div>
        ) : (
          logs.map((l, i) => (
            <div key={i} className="flex gap-2 border-b border-ink-800/60 py-1">
              <span className="shrink-0 text-slate-500">{fmtClock(l.t)}</span>
              <span className={`shrink-0 font-semibold ${levelColor[l.level] || "text-slate-300"}`}>{l.level.padEnd(7)}</span>
              <span className="text-slate-300">{l.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
