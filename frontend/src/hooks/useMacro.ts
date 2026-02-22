import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { MacroSignalResponse } from '../types/api';

export function useMacro() {
  return useQuery<MacroSignalResponse>({
    queryKey: ['macro'],
    queryFn: async () => {
      const { data } = await api.get<MacroSignalResponse>(
        '/api/macro/signal',
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
