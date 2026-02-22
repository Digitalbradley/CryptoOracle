import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react';
import type { SymbolId, Timeframe } from '../types/api';

interface SymbolState {
  symbol: SymbolId;
  setSymbol: (s: SymbolId) => void;
  timeframe: Timeframe;
  setTimeframe: (tf: Timeframe) => void;
}

const SymbolContext = createContext<SymbolState | undefined>(undefined);

export function SymbolProvider({ children }: { children: ReactNode }) {
  const [symbol, setSymbol] = useState<SymbolId>('BTC-USDT');
  const [timeframe, setTimeframe] = useState<Timeframe>('1h');

  return (
    <SymbolContext.Provider value={{ symbol, setSymbol, timeframe, setTimeframe }}>
      {children}
    </SymbolContext.Provider>
  );
}

export function useSymbol() {
  const ctx = useContext(SymbolContext);
  if (!ctx) throw new Error('useSymbol must be used within SymbolProvider');
  return ctx;
}
