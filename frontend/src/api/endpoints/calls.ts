import { apiRequest } from '../client';
import type { CallQueryRequest, QueryResult } from '../types';

export function queryCalls(deviceId: string, payload: CallQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, CallQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/calls/query`, {
    method: 'POST',
    body: payload,
  });
}
