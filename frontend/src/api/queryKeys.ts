export const queryKeys = {
  currentUser: ['current-user'] as const,
  devices: {
    list: ['devices'] as const,
    detail: (deviceId: string) => ['devices', deviceId] as const,
    tunnel: (deviceId: string) => ['devices', deviceId, 'tunnel'] as const,
  },
  frps: {
    devices: (connectedOnly: boolean) => ['frps', 'devices', connectedOnly] as const,
  },
};
