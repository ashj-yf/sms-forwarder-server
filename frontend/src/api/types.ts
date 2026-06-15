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

export interface TunnelEnableIn {
  local_ip?: string;
  local_port: number;
  remote_port?: number | null;
  sync_device_base_url?: boolean;
  use_encryption?: boolean;
  use_compression?: boolean;
}

export interface TunnelUpdateIn {
  local_ip?: string | null;
  local_port?: number | null;
  use_encryption?: boolean | null;
  use_compression?: boolean | null;
}

export interface TunnelOut {
  enabled: boolean;
  proxy_type: string;
  proxy_name: string;
  local_ip: string;
  local_port: number;
  remote_port: number;
  internal_base_url: string;
  public_base_url: string | null;
  use_encryption: boolean;
  use_compression: boolean;
  status: string;
  last_config_generated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TunnelTokenOut {
  token: string;
}

export interface TunnelFrpcConfigOut {
  filename: string;
  format: string;
  content: string;
}

export interface FrpsDeviceOut {
  device_id: string;
  device_name: string | null;
  channel_type: string;
  base_url: string | null;
  tunnel_enabled: boolean;
  proxy_name: string;
  remote_port: number;
  local_ip: string;
  local_port: number;
  connected: boolean;
  frps_status: string;
  client_version: string | null;
  today_traffic_in: string | null;
  today_traffic_out: string | null;
  last_start_time: string | null;
}

export interface FrpsDeviceListOut {
  items: FrpsDeviceOut[];
  total: number;
  connected: number;
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
