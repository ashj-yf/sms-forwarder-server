import { apiRequest } from '../client';
import type { ConfigQueryRequest, QueryResult } from '../types';

export function queryConfig(deviceId: string, payload: ConfigQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, ConfigQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/config/query`, {
    method: 'POST',
    body: payload,
  });
}
