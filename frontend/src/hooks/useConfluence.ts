import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { ConfluenceResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useConfluence() {
  const { symbol, timeframe } = useSymbol();

  return useQuery<ConfluenceResponse>({
    queryKey: ['confluence', symbol, timeframe],
    queryFn: async () => {
      const { data } = await api.get<ConfluenceResponse>(
        `/api/confluence/${symbol}`,
        { params: { timeframe } },
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
