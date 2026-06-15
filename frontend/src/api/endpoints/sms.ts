import { apiRequest } from '../client';
import type { QueryResult, SmsQueryRequest } from '../types';

export function querySms(deviceId: string, payload: SmsQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, SmsQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/sms/query`, {
    method: 'POST',
    body: payload,
  });
}
