import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { WeightsResponse } from '../types/api';

export function useWeights() {
  return useQuery<WeightsResponse>({
    queryKey: ['weights'],
    queryFn: async () => {
      const { data } = await api.get<WeightsResponse>(
        '/api/confluence/weights',
      );
      return data;
    },
    refetchInterval: 30 * 60_000,
    staleTime: 30 * 60_000,
  });
}
