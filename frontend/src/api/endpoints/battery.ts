import { apiRequest } from '../client';
import type { BatteryQueryRequest, QueryResult } from '../types';

export function queryBattery(deviceId: string, payload: BatteryQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, BatteryQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/battery/query`, {
    method: 'POST',
    body: payload,
  });
}
