export const queryKeys = {
  currentUser: ['current-user'] as const,
  devices: {
    list: ['devices'] as const,
    detail: (deviceId: string) => ['devices', deviceId] as const,
  },
};
