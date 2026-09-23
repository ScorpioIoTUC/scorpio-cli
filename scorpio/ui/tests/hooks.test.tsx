import assert from "node:assert/strict";
import test from "node:test";
import { act } from "react-test-renderer";
import { mountHook } from "./hookHarness";
import { useDashboard } from "../src/pages/landing/hooks/useDashboard";
import { useLogFilters } from "../src/pages/landing/hooks/useLogFilters";
import { useSshLogin } from "../src/pages/login/hooks/useSshLogin";
import { useUpdates } from "../src/pages/updates/hooks/useUpdates";
import { FakeEventSource, mockBrowser, completedSetup } from "./fakes";

test("dashboard subscribes after installation, consumes events and closes both streams", async (t) => {
  mockBrowser(t);
  t.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify(completedSetup)));
  const dashboard = await mountHook(useDashboard);
  t.after(dashboard.unmount);
  assert.equal(dashboard.value().setupState, "completed");
  const setup = FakeEventSource.instances.find((stream) => stream.url.endsWith("events"))!;
  const docker = FakeEventSource.instances.find((stream) => stream.url.endsWith("live"))!;
  assert.ok(setup);
  assert.ok(docker);
  const log = { message: "ready", service: "ingest", timestamp: "2026-01-01T12:00:00Z" };
  act(() => docker.emit({ type: "log", source: "docker", data: log }));
  assert.deepEqual(dashboard.value().dockerLogs, [log]);
  act(() => setup.emit({ type: "log", data: { step: 2, total_steps: 4 } }));
  assert.equal(dashboard.value().progress, 50);
  dashboard.unmount();
  assert.equal(setup.closed, true);
  assert.equal(docker.closed, true);
});

test("missing SSH session redirects to login without opening Docker logs", async (t) => {
  mockBrowser(t);
  t.mock.method(
    globalThis,
    "fetch",
    async () =>
      new Response(
        JSON.stringify({
          ...completedSetup,
          ssh_active: false,
        }),
      ),
  );
  const dashboard = await mountHook(useDashboard);
  t.after(dashboard.unmount);
  assert.equal(dashboard.path(), "/login");
  assert.equal(
    FakeEventSource.instances.some((stream) => stream.url.endsWith("live")),
    false,
  );
});

test("stream error keeps dashboard open when the SSH check is inconclusive", async (t) => {
  mockBrowser(t);
  t.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify(completedSetup)));
  const dashboard = await mountHook(useDashboard);
  t.after(dashboard.unmount);
  t.mock.method(globalThis, "fetch", async () => {
    throw new Error("offline");
  });
  await act(async () => FakeEventSource.instances[0].onerror?.());
  assert.equal(dashboard.path(), "/");
  assert.equal(dashboard.value().error, "The connection to the setup logs was temporarily lost.");
});

test("log window timer is removed for all-time and on unmount", async (t) => {
  const { timers } = mockBrowser(t);
  const filters = await mountHook(() => useLogFilters([]));
  t.after(filters.unmount);
  assert.equal(timers.size, 1);
  act(() => filters.value().setTimeRange("all"));
  assert.equal(timers.size, 0);
  act(() => filters.value().setTimeRange("15m"));
  assert.equal(timers.size, 1);
  filters.unmount();
  assert.equal(timers.size, 0);
});

test("login returns a password-free session and keeps server errors visible", async (t) => {
  mockBrowser(t);
  const sessions: unknown[] = [];
  const login = await mountHook(() => useSshLogin((session) => sessions.push(session)));
  t.after(login.unmount);
  const credentials = { hostname: "pi", username: "user", password: "test-only" };
  await act(async () => {
    assert.equal(await login.value().login(credentials), true);
  });
  assert.deepEqual(sessions, [{ hostname: "pi", username: "user" }]);
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response('{"error":"Denied"}', { status: 401 }),
  );
  await act(async () => {
    assert.equal(await login.value().login(credentials), false);
  });
  assert.equal(login.value().isLoading, false);
  assert.equal(login.value().error, "Denied");
  assert.equal(sessions.length, 1);
});

test("updates load both contracts and reflect the installed version after upgrade", async (t) => {
  mockBrowser(t);
  t.mock.method(globalThis, "fetch", async (url, options) => {
    const body =
      options?.method === "POST"
        ? {
            message: "Updated",
            installed_version: "2.0",
            previous_version: "1.0",
            restart_required: true,
          }
        : String(url).endsWith("/version")
          ? { scorpio_cli: "1.0", scorpio_project: "v1" }
          : {
              current_version: "1.0",
              latest_version: "2.0",
              need_to_update: true,
              upload_time: "unknown",
            };
    return new Response(JSON.stringify(body));
  });
  const updates = await mountHook(useUpdates);
  t.after(updates.unmount);
  assert.equal(updates.value().loading, false);
  assert.equal(updates.value().currentCliVersion, "1.0");
  await act(async () => updates.value().handleUpdate());
  assert.equal(updates.value().updating, false);
  assert.equal(updates.value().currentCliVersion, "2.0");
  assert.equal(updates.value().status?.need_to_update, false);
  assert.equal(updates.value().result?.restart_required, true);
});
