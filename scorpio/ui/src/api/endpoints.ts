/** Backend paths. Preserve verbs in each API module, including legacy GET actions. */
export const endpoints = {
  version: "/version",
  ssh: { login: "/ssh/login", logout: "/ssh/logout" },
  setup: {
    start: "/scorpio/setup",
    status: "/scorpio/setup/status",
    events: "/scorpio/setup/events",
    token: "/scorpio/setup/token",
  },
  infrastructure: {
    start: "/scorpio/start",
    stop: "/scorpio/stop",
    reboot: "/scorpio/reboot",
    logs: "/scorpio/logs/live",
  },
  update: "/scorpio/update",
  discord: {
    settings: "/discord/settings",
    setup: "/discord/setup",
    channel: "/discord/set-channel",
    alertGap: "/discord/set-alert-gap",
    remove: "/discord/remove",
  },
} as const;
