// Operator-UI test only: the banking app is visible exclusively as desktop pixels.
import { chromium } from '../../apps/bank-fixture/node_modules/playwright/index.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const output = resolve(process.argv[2] || 'tmp/m3-operator-ui');
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
const poll = async (check) => {
  for (let i = 0; i < 150; i++) {
    if (await check()) return;
    await page.waitForTimeout(100);
  }
  throw Error('UI checkpoint deadline');
};
const state = (text) => poll(async () => (await page.locator('#state').innerText()).includes(text));
const ready = () => poll(() => page.locator('#send').isEnabled());
const clickDesktop = async (x, y) => {
  await ready();
  const screen = page.locator('#screen');
  await screen.scrollIntoViewIfNeeded();
  const box = await screen.boundingBox();
  await page.mouse.click(
    box.x + 3 + (x / 1280) * (box.width - 6),
    box.y + 3 + (y / 800) * (box.height - 6),
  );
  await page.waitForTimeout(150);
  await ready();
};
try {
  await page.goto('http://127.0.0.1:6081/');
  await state('idle');
  await page.getByRole('button', { name: 'Start lookup', exact: true }).click();
  await state('awaiting human');
  if (
    !(await page.locator('#diagnostic').innerText()).includes('search-member') ||
    !(await page.locator('#diagnostic').innerText()).includes('intervention_required')
  )
    throw Error('Missing pause diagnostic');
  await page.getByRole('button', { name: 'Take control', exact: true }).click();
  await state('human · human');
  await page.getByRole('button', { name: 'Verify & resume', exact: true }).click();
  await poll(async () => (await page.locator('#message').innerText()).includes('Resume rejected'));
  await clickDesktop(600, 390);
  await page.getByLabel('Text to send').fill('demo');
  await page.getByRole('button', { name: 'Send text', exact: true }).click();
  await ready();
  await clickDesktop(640, 450);
  await page.getByRole('button', { name: 'Verify & resume', exact: true }).click();
  await state('success');
  if (!(await page.locator('#diagnostic').innerText()).includes('read-balance'))
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
