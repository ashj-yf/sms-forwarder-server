import { apiRequest } from '../client';
import type { LocationQueryRequest, QueryResult } from '../types';

export function queryLocation(deviceId: string, payload: LocationQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, LocationQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/location/query`, {
    method: 'POST',
    body: payload,
  });
}
