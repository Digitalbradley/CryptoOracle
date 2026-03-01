import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import type {
  XaiScoreResponse,
  XaiCalendarResponse,
  XaiPoliciesResponse,
  XaiPersonnelResponse,
} from '../types/api';

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

export function useXaiPolicies() {
  return useQuery<XaiPoliciesResponse>({
    queryKey: ['xai-policies'],
    queryFn: async () => {
      const { data } = await api.get<XaiPoliciesResponse>('/api/xai/policies');
      return data;
    },
    refetchInterval: 30 * 60_000,
  });
}

export function useXaiPersonnel() {
  return useQuery<XaiPersonnelResponse>({
    queryKey: ['xai-personnel'],
    queryFn: async () => {
      const { data } = await api.get<XaiPersonnelResponse>('/api/xai/personnel');
      return data;
    },
    refetchInterval: 30 * 60_000,
  });
}

interface XaiPartnershipItem {
  id: number;
  partner_name: string;
  partner_type: string;
  country: string | null;
  pipeline_stage: string;
  stage_score: string | null;
  partner_weight: string | null;
}

interface XaiPartnershipsResponse {
  count: number;
  pipeline_summary: { announced: number; pilot: number; production: number };
  partnerships: XaiPartnershipItem[];
}

export function useXaiPartnerships() {
  return useQuery<XaiPartnershipsResponse>({
    queryKey: ['xai-partnerships'],
    queryFn: async () => {
      const { data } = await api.get<XaiPartnershipsResponse>('/api/xai/partnerships');
      return data;
    },
    refetchInterval: 30 * 60_000,
  });
}
