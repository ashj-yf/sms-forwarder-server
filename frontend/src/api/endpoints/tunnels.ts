import { apiRequest } from '../client';
import type { TunnelEnableIn, TunnelFrpcConfigOut, TunnelOut, TunnelTokenOut, TunnelUpdateIn } from '../types';

export function getTunnel(deviceId: string): Promise<TunnelOut | null> {
  return apiRequest<TunnelOut | null>(`/devices/${encodeURIComponent(deviceId)}/tunnel`);
}

export function enableTunnel(deviceId: string, payload: TunnelEnableIn): Promise<TunnelOut> {
  return apiRequest<TunnelOut, TunnelEnableIn>(`/devices/${encodeURIComponent(deviceId)}/tunnel`, {
    method: 'POST',
    body: payload,
  });
}

export function updateTunnel(deviceId: string, payload: TunnelUpdateIn): Promise<TunnelOut> {
  return apiRequest<TunnelOut, TunnelUpdateIn>(`/devices/${encodeURIComponent(deviceId)}/tunnel`, {
    method: 'PUT',
    body: payload,
  });
}

export function disableTunnel(deviceId: string): Promise<TunnelOut> {
  return apiRequest<TunnelOut>(`/devices/${encodeURIComponent(deviceId)}/tunnel`, {
    method: 'DELETE',
  });
}

export function rotateTunnelToken(deviceId: string): Promise<TunnelTokenOut> {
  return apiRequest<TunnelTokenOut>(`/devices/${encodeURIComponent(deviceId)}/tunnel/rotate-token`, {
    method: 'POST',
  });
}

export function getTunnelFrpcConfig(deviceId: string): Promise<TunnelFrpcConfigOut> {
  return apiRequest<TunnelFrpcConfigOut>(`/devices/${encodeURIComponent(deviceId)}/tunnel/frpc-config`);
}
