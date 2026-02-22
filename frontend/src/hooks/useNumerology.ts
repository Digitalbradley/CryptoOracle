import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { NumerologyResponse } from '../types/api';

export function useNumerology() {
  return useQuery<NumerologyResponse>({
    queryKey: ['numerology'],
    queryFn: async () => {
      const { data } = await api.get<NumerologyResponse>('/api/numerology/current');
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
