import { useCallback, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { InterpretationResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useInterpretation() {
  const { symbol, timeframe } = useSymbol();
  const [forceKey, setForceKey] = useState(0);

  const query = useQuery<InterpretationResponse>({
    queryKey: ['interpretation', symbol, timeframe, forceKey],
    queryFn: async () => {
      const params: Record<string, string> = { timeframe };
      if (forceKey > 0) params.force = 'true';
      const { data } = await api.get<InterpretationResponse>(
        `/api/interpretation/${symbol}`,
        { params },
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });

  const refresh = useCallback(() => setForceKey((k) => k + 1), []);

  return { ...query, refresh };
}
