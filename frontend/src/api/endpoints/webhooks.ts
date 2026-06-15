import { apiRequest } from '../client';
import type { WebhookOut } from '../types';

export function createWebhook(deviceId: string): Promise<WebhookOut> {
  return apiRequest<WebhookOut>(`/devices/${encodeURIComponent(deviceId)}/webhook`, {
    method: 'POST',
  });
}

export function rotateWebhook(deviceId: string): Promise<WebhookOut> {
  return apiRequest<WebhookOut>(`/devices/${encodeURIComponent(deviceId)}/webhook/rotate`, {
    method: 'POST',
  });
}
