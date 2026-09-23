/** Browser boundaries faked locally; tests never contact a host. */
export class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onmessage?: (message: { data: string }) => void;
  onerror?: () => void;
  closed = false;
  constructor(readonly url: string) {
    FakeEventSource.instances.push(this);
  }
  close() {
    this.closed = true;
  }
  emit(event: unknown) {
    this.onmessage?.({ data: JSON.stringify(event) });
  }
}

export function mockBrowser(t: any) {
  FakeEventSource.instances = [];
  t.mock.method(globalThis, "fetch", async () => new Response("{}"));
  const descriptors = ["EventSource", "window", "sessionStorage"].map(
    (key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)] as const,
  );
  const session = new Map<string, string>();
  const timers = new Map<number, () => void>();
  let nextTimer = 1;
  Object.assign(globalThis, {
    EventSource: FakeEventSource,
    sessionStorage: {
      getItem: (key: string) => session.get(key) ?? null,
      setItem: (key: string, value: string) => session.set(key, value),
      removeItem: (key: string) => session.delete(key),
    },
    window: {
      confirm: () => true,
      setInterval: (callback: () => void) => {
        timers.set(nextTimer, callback);
        return nextTimer++;
      },
      clearInterval: (id: number) => timers.delete(id),
      setTimeout: (callback: () => void) => {
        timers.set(nextTimer, callback);
        return nextTimer++;
      },
      clearTimeout: (id: number) => timers.delete(id),
    },
  });
  t.after(() => {
    for (const [key, descriptor] of descriptors) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else Reflect.deleteProperty(globalThis, key);
    }
  });
  return { session, timers };
}

export const completedSetup = {
  status: "completed",
  logs: [],
  lastLog: null,
  error: null,
  startedAt: null,
  finishedAt: null,
  ssh_active: true,
  infrastructure: { status: "running" },
};
