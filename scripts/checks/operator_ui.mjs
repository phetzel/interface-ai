// Operator-UI test only: the banking app is visible exclusively as desktop pixels.
import { chromium } from '../../apps/bank-fixture/node_modules/playwright/index.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { operatorControls } from './operator_helpers.mjs';
const output = resolve(process.argv[2] || 'tmp/operator-ui');
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
const { poll, phase: state, ready, clickDesktop } = operatorControls(page);

try {
  await page.goto('http://127.0.0.1:6081/');
  await page.locator('#run-details > summary').click();
  await state('idle');
  const desktopLayout = await page.locator('.desktop-panel').boundingBox();
  const controlsLayout = await page.locator('.control-panel').boundingBox();
  assert.ok(
    controlsLayout.x > desktopLayout.x + desktopLayout.width,
    'Sidebar is beside the desktop',
  );
  await page.locator('#member').fill('123');
  await page.locator('#start').click();
  await poll(async () =>
    (await page.locator('#message').innerText()).includes('exactly five digits'),
  );
  await state('idle');
  await page.locator('#member').fill('00123');
  await page.getByRole('button', { name: 'Start lookup', exact: true }).click();
  await state('awaiting human');
  if (
    !(await page.locator('#diagnostic').innerText()).includes('action-003') ||
    !(await page.locator('#diagnostic').innerText()).includes('intervention_required')
  )
    throw Error('Missing pause diagnostic');
  await page.getByRole('button', { name: 'Take control', exact: true }).click();
  await state('human · human');
  await page.getByRole('button', { name: 'Verify & resume', exact: true }).click();
  await poll(async () => (await page.locator('#message').innerText()).includes('Resume rejected'));
  await clickDesktop(600, 390);
  await page.getByRole('button', { name: 'Actual size', exact: true }).click();
  await page.setViewportSize({ width: 720, height: 1200 });
  assert.equal(await page.locator('#desktop-size').getAttribute('aria-pressed'), 'true');
  const narrowDesktop = await page.locator('.desktop-panel').boundingBox();
  const narrowControls = await page.locator('.control-panel').boundingBox();
  assert.ok(narrowDesktop.y < narrowControls.y, 'Desktop precedes controls in narrow panes');
  assert.equal((await page.locator('#screen').boundingBox()).width, 1286);
  await page.locator('#desktop-viewport').evaluate((view) => view.scrollTo(180, 120));
  const clickRequest = page.waitForRequest(
    (r) => r.url().endsWith('/action') && r.method() === 'POST',
  );
  await clickDesktop(600, 390);
  const mapped = (await clickRequest).postDataJSON().action;
  assert.equal(mapped.type, 'click');
  assert.ok(Math.abs(mapped.x - 600) <= 1 && Math.abs(mapped.y - 390) <= 1);
  await page.getByLabel('Text to send').fill('demo');
  await page.getByRole('button', { name: 'Send text', exact: true }).click();
  await ready();
  await clickDesktop(640, 450);
  await page.getByRole('button', { name: 'Fit to panel', exact: true }).click();
  await page.setViewportSize({ width: 1000, height: 1200 });
  assert.equal(await page.locator('#desktop-size').getAttribute('aria-pressed'), 'false');
  assert.ok((await page.locator('#screen').boundingBox()).width < 1000);
  await page.getByRole('button', { name: 'Verify & resume', exact: true }).click();
  await state('success');
  if (!(await page.locator('#diagnostic').innerText()).includes('extract-result'))
    throw Error('Missing final step');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: resolve(output, 'operator-success.png'), fullPage: true });
  if (errors.length) throw Error('Operator page script error');
  await writeFile(
    resolve(output, 'summary.json'),
    JSON.stringify(
      {
        status: 'passed',
        provenance: 'automated-operator-ui-test',
        viewport: [1000, 1200],
        scaledDesktopClicks: true,
        actualSizeAtNarrowViewport: true,
        scrolledClickCoordinatesVerified: true,
        fitRestoredAfterResize: true,
        invalidMemberExplained: true,
        prematureResumeRejected: true,
        stepAndReasonVisible: true,
        completed: true,
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
