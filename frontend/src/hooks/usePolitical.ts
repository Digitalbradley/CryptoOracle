import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { PoliticalSignalResponse } from '../types/api';

export function usePolitical() {
  return useQuery<PoliticalSignalResponse>({
    queryKey: ['political'],
    queryFn: async () => {
      const { data } = await api.get<PoliticalSignalResponse>(
        '/api/political/signal',
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
