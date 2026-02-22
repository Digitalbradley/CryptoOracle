import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { SentimentResponse } from '../types/api';
import { useSymbol } from './useSymbol';

export function useSentiment() {
  const { symbol } = useSymbol();

  return useQuery<SentimentResponse>({
    queryKey: ['sentiment', symbol],
    queryFn: async () => {
      const { data } = await api.get<SentimentResponse>(
        `/api/sentiment/${symbol}`,
      );
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}
