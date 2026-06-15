import { apiRequest } from '../client';
import type { CurrentUserOut, LoginRequest, TokenOut } from '../types';

export function login(payload: LoginRequest): Promise<TokenOut> {
  return apiRequest<TokenOut, LoginRequest>('/auth/login', {
    method: 'POST',
    body: payload,
  });
}

export function getCurrentUser(): Promise<CurrentUserOut> {
  return apiRequest<CurrentUserOut>('/auth/me');
}
