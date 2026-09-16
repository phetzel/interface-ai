import { defineConfig } from "@playwright/test";

const scenarios = [
  "default",
  "delayed",
  "blocked",
  "duplicate",
  "unreadable",
  "translated",
  "policy",
];
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 3,
  retries: 0,
  timeout: 15_000,
  expect: { timeout: 5_000 },
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: {
    browserName: "chromium",
    baseURL: "http://127.0.0.1:4180",
    viewport: { width: 1280, height: 800 },
    locale: "en-US",
    timezoneId: "UTC",
    trace: "off",
    screenshot: "only-on-failure",
  },
  webServer: scenarios.map((name, index) => ({
    command: "node server/index.mjs",
    env: {
      HOST: "127.0.0.1",
      PORT: String(4180 + index),
      FIXTURE_SCENARIO: name,
    },
    url: `http://127.0.0.1:${4180 + index}/healthz`,
    timeout: 10_000,
    reuseExistingServer: false,
  })),
});
