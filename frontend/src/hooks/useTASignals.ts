import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { TAResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useTASignals() {
  const { symbol, timeframe } = useSymbol();

  return useQuery<TAResponse>({
    queryKey: ['ta', symbol, timeframe],
    queryFn: async () => {
      const { data } = await api.get<TAResponse>(
        `/api/signals/ta/${symbol}`,
        { params: { timeframe } },
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
