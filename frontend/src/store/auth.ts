const TOKEN_KEY = 'sms-forwarder-token';

export function getStoredToken(): string | null {
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.sessionStorage.removeItem(TOKEN_KEY);
}
