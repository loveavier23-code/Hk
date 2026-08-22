// Shape of the snapshot pushed by the backend over /ws (subset we use).
export interface Position {
  symbol: string;
  side: "LONG" | "SHORT";
  qty: number;
  entry: number;
  price: number;
  leverage: number;
  unrealized: number;
  pnl_pct: number;
  strategy: string;
  opened_at: number;
  stop_loss: number | null;
  take_profit: number | null;
}

export interface Trade {
  id: number;
  symbol: string;
  side: string;
  action: "OPEN" | "CLOSE";
  qty: number;
  price: number;
  pnl: number;
  reason: string;
  strategy: string;
  t: number;
}

export interface LogEntry {
  t: number;
  level: string;
  msg: string;
  source: string;
}

export interface SignalInfo {
  side: "long" | "short" | "flat";
  strength: number;
  reason: string;
  strategy: string;
  t: number;
}

export interface Account {
  balance: number;
  equity: number;
  initial_equity: number;
  unrealized: number;
  realized: number;
  peak_equity: number;
  drawdown_pct: number;
  roi_pct: number;
}

export interface Snapshot {
  version: string;
  mode: "live" | "sim";
  connected: boolean;
  running: boolean;
  halted: boolean;
  auto_strategy: boolean;
  strategy: string;
  symbols: string[];
  started_at: number;
  server_time: number;
  account: Account;
  positions: Position[];
  trades: Trade[];
  logs: LogEntry[];
  equity_curve: { t: number; equity: number }[];
  prices: Record<string, number>;
  candles: Record<string, number[][]>;
  signals: Record<string, SignalInfo>;
  active_strategy: Record<string, string>;
}
