import { apiRequest } from '../client';
import type { ContactQueryRequest, QueryResult } from '../types';

export function queryContacts(deviceId: string, payload: ContactQueryRequest): Promise<QueryResult> {
  return apiRequest<QueryResult, ContactQueryRequest>(`/devices/${encodeURIComponent(deviceId)}/contacts/query`, {
    method: 'POST',
    body: payload,
  });
}
