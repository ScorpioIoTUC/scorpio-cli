import assert from "node:assert/strict";
import test from "node:test";
import { ApiError, requestJson } from "../src/api/http";
import { sshApi } from "../src/api/ssh/sshApi";
import { getSetupStatus, startSetup, subscribeToSetup } from "../src/api/setup/setupApi";
import { getVersion } from "../src/api/version/versionApi";
import { getScorpioTokenSetup, updateScorpioTokenSetup } from "../src/api/token/tokenApi";
import { getScorpioUpdateStatus, updateScorpio } from "../src/api/update/updateApi";
import {
  startInfrastructure,
  stopInfrastructure,
  rebootHost,
} from "../src/api/infrastructure/infrastructureApi";
import {
  getDiscordSettings,
  setupDiscord,
  setDiscordChannel,
  setDiscordAlertGap,
  removeDiscord,
} from "../src/api/discord/discordApi";
import { subscribeToDockerLogs } from "../src/api/logs/logsApi";
import { FakeEventSource, mockBrowser } from "./fakes";

test("API calls preserve paths, methods, bodies and configured JSON base URL", async (t) => {
  mockBrowser(t);
  const requests: any[] = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    requests.push({ url, ...options });
    return new Response(JSON.stringify({ message: "ok" }));
  });
  const credentials = { hostname: "pi", username: "user", password: "test-only" };
  const cases = [
    [() => sshApi.login(credentials), "/ssh/login", "POST", credentials],
    [sshApi.logout, "/ssh/logout", "POST", {}],
    [getSetupStatus, "/scorpio/setup/status", "GET", undefined],
    [startSetup, "/scorpio/setup", "POST", {}],
    [getVersion, "/version", "GET", undefined],
    [startInfrastructure, "/scorpio/start", "GET", undefined],
    [stopInfrastructure, "/scorpio/stop", "GET", undefined],
    [rebootHost, "/scorpio/reboot", "POST", {}],
    [getScorpioTokenSetup, "/scorpio/setup/token", "GET", undefined],
    [
      () => updateScorpioTokenSetup("test-only", "https://station.test"),
      "/scorpio/setup/token",
      "POST",
      { token: "test-only", api_url: "https://station.test" },
    ],
    [getScorpioUpdateStatus, "/scorpio/update", "GET", undefined],
    [updateScorpio, "/scorpio/update", "POST", {}],
    [getDiscordSettings, "/discord/settings", "GET", undefined],
    [() => setupDiscord("test-only"), "/discord/setup", "POST", { token: "test-only" }],
    [
      () => setDiscordChannel("errors", "42"),
      "/discord/set-channel",
      "POST",
      { tag: "errors", channel_id: "42" },
    ],
    [() => setDiscordAlertGap(5), "/discord/set-alert-gap", "POST", { minutes: 5 }],
    [removeDiscord, "/discord/remove", "POST", {}],
  ] as const;
  for (const [call, path, method, body] of cases) {
    await call();
    const actual = requests.at(-1);
    assert.equal(actual.url, `https://api.example.test${path}`);
    assert.equal(actual.method ?? "GET", method);
    assert.equal(actual.body, body === undefined ? undefined : JSON.stringify(body));
    assert.equal(actual.headers.Accept, "application/json");
    assert.equal(actual.headers["Content-Type"], "application/json");
  }
});

test("HTTP errors retain server messages, status and malformed-JSON fallback", async (t) => {
  mockBrowser(t);
  for (const [body, status, message] of [
    ['{"error":"Denied","message":"ignored"}', 401, "Denied"],
    ['{"message":"Conflict"}', 409, "Conflict"],
    ["not json", 502, "The request could not be completed."],
  ] as const) {
    t.mock.method(globalThis, "fetch", async () => new Response(body, { status }));
    await assert.rejects(requestJson("/test"), (error: unknown) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, status);
      assert.equal(error.message, message);
      return true;
    });
  }
});

test("SSE preserves relative URLs, parsing, error callbacks and close ownership", (t) => {
  mockBrowser(t);
  const received: unknown[] = [];
  let errors = 0;
  const closeSetup = subscribeToSetup(
    (event) => received.push(event),
    () => errors++,
  );
  const closeLogs = subscribeToDockerLogs(
    (event) => received.push(event),
    () => errors++,
  );
  const [setup, logs] = FakeEventSource.instances;
  assert.equal(setup.url, "/scorpio/setup/events");
  assert.equal(logs.url, "/scorpio/logs/live");
  const status = { type: "status", data: { status: "running" } };
  const event = { type: "log", source: "docker", data: { message: "ready" } };
  setup.emit(status);
  logs.emit(event);
  assert.deepEqual(received, [status, event]);
  setup.onmessage?.({ data: "invalid JSON" });
  logs.onerror?.();
  assert.equal(errors, 2);
  closeSetup();
  assert.equal(setup.closed, true);
  assert.equal(logs.closed, false);
  closeLogs();
  assert.equal(logs.closed, true);
});
