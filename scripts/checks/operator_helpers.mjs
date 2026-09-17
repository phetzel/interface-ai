// Trusted panel harness utilities. Never inspect the banking application's DOM.
export function operatorControls(page) {
  async function poll(check) {
    for (let i = 0; i < 200; i++) {
      if (await check()) return;
      await page.waitForTimeout(100);
    }
    throw Error('Operator UI checkpoint deadline');
  }
  const phase = (text) =>
    poll(async () => (await page.locator('#state').innerText()).includes(text));
  const ready = () => poll(() => page.locator('#send').isEnabled());
  async function clickDesktop(x, y) {
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
  }
  return { poll, phase, ready, clickDesktop };
}
