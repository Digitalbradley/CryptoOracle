import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { OnchainResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useOnchain() {
  const { symbol } = useSymbol();

  return useQuery<OnchainResponse>({
    queryKey: ['onchain', symbol],
    queryFn: async () => {
      const { data } = await api.get<OnchainResponse>(
        `/api/onchain/${symbol}`,
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
