import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { InterpretationResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useInterpretation() {
  const { symbol, timeframe } = useSymbol();

  return useQuery<InterpretationResponse>({
    queryKey: ['interpretation', symbol, timeframe],
    queryFn: async () => {
      const { data } = await api.get<InterpretationResponse>(
        `/api/interpretation/${symbol}`,
        { params: { timeframe } },
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
