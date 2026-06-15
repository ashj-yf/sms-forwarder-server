import { apiRequest } from '../client';
import type { DeviceCreate, DeviceListOut, DeviceOut, DeviceUpdate } from '../types';

export function listDevices(): Promise<DeviceListOut> {
  return apiRequest<DeviceListOut>('/devices');
}

export function getDevice(deviceId: string): Promise<DeviceOut> {
  return apiRequest<DeviceOut>(`/devices/${encodeURIComponent(deviceId)}`);
}

export function createDevice(payload: DeviceCreate): Promise<DeviceOut> {
  return apiRequest<DeviceOut, DeviceCreate>('/devices', {
    method: 'POST',
    body: payload,
  });
}

export function updateDevice(deviceId: string, payload: DeviceUpdate): Promise<DeviceOut> {
  return apiRequest<DeviceOut, DeviceUpdate>(`/devices/${encodeURIComponent(deviceId)}`, {
    method: 'PUT',
    body: payload,
  });
}
