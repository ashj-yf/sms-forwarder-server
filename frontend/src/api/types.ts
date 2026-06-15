export type QueryMode = 'realtime' | 'cache';

export interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
  request_id: string;
  timestamp: number;
}

export interface ApiErrorPayload {
  code: number;
  msg: string;
  data?: Record<string, unknown>;
  request_id?: string;
  timestamp?: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
}

export interface CurrentUserOut {
  id: number;
  username: string;
  display_name: string | null;
}

export interface DeviceCreate {
  device_name?: string | null;
  channel_type: string;
  base_url?: string | null;
  sign_secret?: string | null;
}

export interface DeviceUpdate {
  device_name?: string | null;
  channel_type?: string | null;
  base_url?: string | null;
  sign_secret?: string | null;
}

export interface DeviceOut {
  device_id: string;
  device_name: string | null;
  channel_type: string;
  base_url: string | null;
  status: string;
  is_active: boolean;
  last_seen_at: string | null;
  last_webhook_at: string | null;
  webhook_count: number;
}

export interface DeviceListOut {
  items: DeviceOut[];
  total: number;
}

export interface WebhookOut {
  webhook_url: string;
  webhook_token: string;
}

export interface QueryModeRequest {
  mode: QueryMode;
}

export interface PagedQueryRequest extends QueryModeRequest {
  page_num: number;
  page_size: number;
}

export interface SmsQueryRequest extends PagedQueryRequest {
  type?: number | null;
  keyword?: string | null;
}

export interface CallQueryRequest extends PagedQueryRequest {
  type?: number | null;
  phone_number?: string | null;
}

export interface ContactQueryRequest extends PagedQueryRequest {
  phone_number?: string | null;
  name?: string | null;
}

export type BatteryQueryRequest = QueryModeRequest;
export type LocationQueryRequest = QueryModeRequest;
export type ConfigQueryRequest = QueryModeRequest;

export interface QueryResult<T = unknown> {
  request_id: string;
  mode: QueryMode;
  result: T;
}

export interface PagedResult<T = Record<string, unknown>> {
  items: T[];
  total: number;
  page_num: number;
  page_size: number;
}
