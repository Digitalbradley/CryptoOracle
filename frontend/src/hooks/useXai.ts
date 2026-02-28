import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type { XaiScoreResponse, XaiCalendarResponse } from '../types/api';

export function useXaiScore() {
  return useQuery<XaiScoreResponse>({
    queryKey: ['xai-score'],
    queryFn: async () => {
      const { data } = await api.get<XaiScoreResponse>('/api/xai/score');
      return data;
    },
    refetchInterval: 5 * 60_000,
  });
}

export function useXaiCalendar() {
  return useQuery<XaiCalendarResponse>({
    queryKey: ['xai-calendar'],
    queryFn: async () => {
      const { data } = await api.get<XaiCalendarResponse>('/api/xai/calendar');
      return data;
    },
    refetchInterval: 30 * 60_000,
  });
}
