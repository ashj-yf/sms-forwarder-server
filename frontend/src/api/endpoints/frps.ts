import { apiRequest } from '../client';
import type { FrpsDeviceListOut } from '../types';

export function listFrpsDevices(connectedOnly: boolean): Promise<FrpsDeviceListOut> {
  const params = new URLSearchParams({ connected_only: String(connectedOnly) });
  return apiRequest<FrpsDeviceListOut>(`/frps/devices?${params.toString()}`);
}
