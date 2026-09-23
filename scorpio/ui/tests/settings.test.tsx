import assert from "node:assert/strict";
import test from "node:test";
import { act } from "react-test-renderer";
import { mountHook } from "./hookHarness";
import { mockBrowser } from "./fakes";
import { useSettings } from "../src/pages/settings/hooks/useSettings";
import { useSshLogout } from "../src/pages/landing/hooks/useSshLogout";

test("settings retain loading, trimmed token saves, feedback timeout and cleanup", async (t) => {
  const { timers } = mockBrowser(t);
  const bodies: unknown[] = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    if (options?.method === "POST") {
      bodies.push(JSON.parse(String(options.body)));
      return new Response('{"message":"Saved"}');
    }
    return new Response(
      JSON.stringify(
        String(url).includes("discord")
          ? { configured: false, channels: {}, error_alert_gap_minutes: 5 }
          : { api_url: "https://api.test", token: "old" },
      ),
    );
  });
  const settings = await mountHook(useSettings);
  t.after(settings.unmount);
  assert.equal(settings.value().scorpioApiUrl, "https://api.test");
  act(() => settings.value().setScorpioToken("  new  "));
  const event = { preventDefault() {} } as any;
  await act(async () => settings.value().saveScorpioSetup(event));
  assert.deepEqual(bodies, [{ token: "new", api_url: "https://api.test" }]);
  assert.equal(settings.value().message, "Saved");
  assert.equal(timers.size, 1);
  act(() => [...timers.values()][0]());
  assert.equal(settings.value().message, "");
  act(() => settings.value().setScorpioToken("  "));
  await act(async () => settings.value().saveScorpioSetup(event));
  assert.equal(settings.value().message, "Scorpio API token cannot be empty.");
  assert.equal(bodies.length, 1);
  settings.unmount();
  assert.equal(timers.size, 0);
});

test("logout invokes the caller only after success and retains failure messages", async (t) => {
  mockBrowser(t);
  let disconnected = 0;
  const logout = await mountHook(() => useSshLogout(() => disconnected++));
  t.after(logout.unmount);
  t.mock.method(
    globalThis,
    "fetch",
    async () => new Response('{"error":"No session"}', { status: 400 }),
  );
  await act(async () => logout.value().logout());
  assert.equal(disconnected, 0);
  assert.equal(logout.value().error, "No session");
  t.mock.method(globalThis, "fetch", async () => new Response('{"message":"Bye"}'));
  await act(async () => logout.value().logout());
  assert.equal(disconnected, 1);
  assert.equal(logout.value().isLoading, false);
});
