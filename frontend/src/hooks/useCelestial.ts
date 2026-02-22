import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { CelestialResponse } from '../types/api';

export function useCelestial() {
  return useQuery<CelestialResponse>({
    queryKey: ['celestial'],
    queryFn: async () => {
      const { data } = await api.get<CelestialResponse>('/api/celestial/current');
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
