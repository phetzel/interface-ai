// Trusted operator-UI acceptance on a fresh expired scenario. No bank DOM access.
import assert from 'node:assert/strict';
import { chromium } from '../../apps/bank-fixture/node_modules/playwright/index.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const output = resolve(process.argv[2] || 'tmp/m3-operator-stop');
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
const poll = async (check) => {
  for (let i = 0; i < 200; i++) {
    if (await check()) return;
    await page.waitForTimeout(100);
  }
  throw Error('Operator UI checkpoint deadline');
};
const phase = (text) => poll(async () => (await page.locator('#state').innerText()).includes(text));
try {
  await page.goto('http://127.0.0.1:6081/');
  await phase('idle');
  const session = await page.locator('#session').innerText();
  await page.locator('#start').click();
  await phase('awaiting human');
  await page.locator('#takeover').click();
  await phase('human · human');
  const screen = page.locator('#screen');
  await screen.scrollIntoViewIfNeeded();
  const box = await screen.boundingBox();
  await page.mouse.click(
    box.x + 3 + (600 / 1280) * (box.width - 6),
    box.y + 3 + (390 / 800) * (box.height - 6),
  );
  await poll(() => page.locator('#send').isEnabled());
  await page.locator('#text').fill('x'.repeat(256));
  const inputRequest = page.waitForRequest(
    (r) => r.url().endsWith('/action') && r.method() === 'POST',
  );
  let inputFinished = false;
  const inputResponse = page
    .waitForResponse((r) => r.url().endsWith('/action') && r.request().method() === 'POST')
    .then((response) => {
      inputFinished = true;
      return response;
    });
  await page.locator('#send').click();
  await inputRequest;
  await page.waitForTimeout(200);
  assert.equal(inputFinished, false, 'Input finished before Stop could be exercised');
  assert.equal(await page.locator('#stop').isEnabled(), true, 'Stop disabled during input');
  const stopResponse = page.waitForResponse((r) => r.url().endsWith('/stop'));
  const started = Date.now();
  await page.locator('#stop').click();
  const response = await stopResponse;
  assert.equal(response.status(), 200);
  const stopResponseMs = Date.now() - started;
  const interrupted = await inputResponse;
  assert.equal(interrupted.status(), 409);
  assert.equal((await interrupted.json()).code, 'stopped');
  await phase('stopped · stopped');
  assert.equal(await page.locator('#session').innerText(), session);
  for (const id of ['send', 'resume', 'takeover', 'start'])
    assert.equal(await page.locator('#' + id).isEnabled(), false);
  await page.reload();
  await phase('stopped · stopped');
  assert.equal(await page.locator('#send').isEnabled(), false);
  assert.equal(await page.locator('#resume').isEnabled(), false);
  await poll(() =>
    page.locator('#screen').evaluate((img) => img.complete && img.naturalWidth === 1280),
  );
  assert.deepEqual(errors, []);
  await page.screenshot({ path: resolve(output, 'operator-stopped.png'), fullPage: true });
  await writeFile(
    resolve(output, 'summary.json'),
    JSON.stringify(
      {
        status: 'passed',
        provenance: 'automated-operator-ui-test',
        realHumanWitnessed: false,
        panelStopDuringPendingInput: true,
        inputRejectedAsStopped: true,
        stopResponseMs,
        sameSession: true,
        stoppedAfterReload: true,
        controlsDisabled: true,
        pageErrors: 0,
        modelCalls: 0,
      },
      null,
      2,
    ) + '\n',
  );
} finally {
  await browser.close();
}
