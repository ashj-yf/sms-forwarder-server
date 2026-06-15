import { clearStoredToken, getStoredToken } from '../store/auth';
import { createRequestId } from '../utils/format';
import type { ApiEnvelope, ApiErrorPayload } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1';

export class ApiError extends Error {
  readonly code: number;
  readonly requestId?: string;
  readonly details?: Record<string, unknown>;
  readonly retryAfter?: number;

  constructor(payload: ApiErrorPayload, retryAfter?: number) {
    super(payload.msg || 'request failed');
    this.name = 'ApiError';
    this.code = payload.code;
    this.requestId = payload.request_id;
    this.details = payload.data;
    this.retryAfter = retryAfter;
  }
}

interface RequestOptions<TBody> {
  method?: 'GET' | 'POST' | 'PUT';
  body?: TBody;
  signal?: AbortSignal;
}

function readRetryAfter(response: Response): number | undefined {
  const value = response.headers.get('Retry-After');
  if (!value) {
    return undefined;
  }
  const seconds = Number(value);
  return Number.isFinite(seconds) ? seconds : undefined;
}

async function parseJson<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  return JSON.parse(text) as T;
}

export async function apiRequest<TData, TBody = unknown>(
  path: string,
  options: RequestOptions<TBody> = {},
): Promise<TData> {
  const headers = new Headers({
    Accept: 'application/json',
    'X-Request-ID': createRequestId(),
  });
  const token = getStoredToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });
  const envelope = await parseJson<ApiEnvelope<TData> | ApiErrorPayload>(response);

  if (!response.ok || envelope.code >= 400) {
    const payload = envelope as ApiErrorPayload;
    if (payload.code === 401) {
      clearStoredToken();
    }
    throw new ApiError(payload, readRetryAfter(response));
  }

  return (envelope as ApiEnvelope<TData>).data;
}
