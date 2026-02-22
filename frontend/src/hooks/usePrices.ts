import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { PriceResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function usePrices(limit = 100) {
  const { symbol, timeframe } = useSymbol();

  return useQuery<PriceResponse>({
    queryKey: ['prices', symbol, timeframe, limit],
    queryFn: async () => {
      const { data } = await api.get<PriceResponse>(
        `/api/prices/${symbol}`,
        { params: { timeframe, limit } },
      );
      return data;
    },
    refetchInterval: 60_000,
  });
}
