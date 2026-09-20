// The server injects the process token into this script's nonce-protected scope.
const $ = (id) => document.getElementById(id);
let state = null,
  busy = false,
  frameURL = null;
const headers = { 'X-Operator-Token': token };
async function read(path) {
  const r = await fetch(path, { headers, cache: 'no-store' });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    const error = Error('Desktop unavailable');
    error.busy = r.status === 503 && body.code === 'busy';
    throw error;
  }
  return r;
}
function render() {
  if (!state) return;
  const titles = {
    idle: 'Ready to start',
    running: state.runKind === 'discovery' ? 'Discovering the workflow' : 'Running lookup',
    awaiting_human: 'Your help is needed',
    quiescing: 'Giving you control',
    human: 'You have control',
    success: 'Lookup complete',
    failure: 'Lookup failed',
    business_outcome: 'Member not found',
    stopped: 'Stopped',
    probing: 'Testing model connection',
    probe_complete: 'Model action test complete',
    probe_failed: 'Model action test failed',
  };
  $('status-title').textContent = titles[state.phase] || 'Checking desktop';
  $('state').textContent = state.phase.replaceAll('_', ' ') + ' · ' + state.owner;
  $('session').textContent = 'Session ' + state.session;
  $('diagnostic').textContent = [
    state.step ? 'Step: ' + state.step : null,
    state.lastCheckpoint ? 'Last verified checkpoint: ' + state.lastCheckpoint : null,
    state.reason ? 'Reason: ' + state.reason : null,
  ]
    .filter(Boolean)
    .join(' · ');
  const human = state.phase === 'human' && !busy;
  $('lookup-controls').hidden = state.phase !== 'idle';
  $('human-controls').hidden = state.phase !== 'human';
  $('takeover').hidden = !['running', 'awaiting_human', 'quiescing'].includes(state.phase);
  $('resume').hidden = state.phase !== 'human';
  $('start').disabled = busy || state.phase !== 'idle';
  $('member').disabled = state.phase !== 'idle';
  $('takeover').disabled = busy || !['running', 'awaiting_human'].includes(state.phase);
  $('resume').disabled = !human || !state.resumable;
  $('stop').disabled = state.phase === 'stopped';
  for (const id of ['send', 'select', 'text']) $(id).disabled = !human;
  document.querySelectorAll('[data-key]').forEach((b) => (b.disabled = !human));
  $('screen').classList.toggle('human', human);
  $('input-mode').textContent =
    state.phase === 'human' ? (busy ? 'Sending input…' : 'You control this desktop') : 'View only';
  $('input-mode').dataset.human = String(state.phase === 'human');
  $('screen-help').textContent =
    state.phase === 'human'
      ? 'Click in the image to use the desktop. Send text and keys with the panel controls.'
      : 'Watch the same desktop the automation uses. Take control when available to interact.';
  const messages = {
    idle: 'Look up a member’s savings balance on the desktop.',
    running:
      state.runKind === 'discovery'
        ? 'The model is choosing actions from the synthetic desktop. You can request control or stop.'
        : 'Automation owns input. You can request control or stop.',
    awaiting_human: state.resumable
      ? 'Session expired. Take control, restore the workspace with the synthetic code demo, then verify and resume.'
      : 'Verification stopped: ' +
        (state.reason || 'verification failed') +
        '. Take control to inspect; this interruption requires a reset before another run.',
    quiescing: 'Waiting for automation input to drain…',
    human: state.resumable
      ? 'You own control. Restore the workspace, return to the original member overview, then verify and resume.'
      : 'You own control. This interruption has no verified continuation; inspect, then reset the desktop.',
    success:
      'The savings balance is visible on the desktop. Reset the desktop and reload this page for another run.',
    failure:
      'Run stopped: ' +
      (state.reason || 'verification failed') +
      '. Reset the desktop before retrying.',
    business_outcome: 'Member not found. Reset the desktop before another run.',
    stopped: 'Input stopped. Reset the desktop to continue.',
    probing: 'The host is testing one model-selected click. Stop remains available.',
    probe_complete:
      'The transport test finished. See the host report for OpenAI results. Reset before a lookup.',
    probe_failed: 'The transport test ended. See the host report, then reset the desktop.',
  };
  $('guidance').textContent = messages[state.phase] || state.phase;
  if (state.evidenceStatus === 'failed')
    $('guidance').textContent =
      'Input stopped because run evidence could not be saved. Inspect storage and reset the desktop.';
}
function errorMessage(code) {
  const messages = {
    resume_rejected: 'Resume rejected: return to the original member overview.',
    invalid_input: 'Enter exactly five digits for the member ID, including leading zeroes.',
  };
  return messages[code] || code;
}
function desktopPoint(event) {
  const rect = event.target.getBoundingClientRect();
  const border = 3;
  const coordinate = (value, origin, length, pixels) =>
    Math.max(
      0,
      Math.min(
        pixels - 1,
        Math.floor(((value - origin - border) / (length - 2 * border)) * pixels),
      ),
    );
  return {
    x: coordinate(event.clientX, rect.left, rect.width, 1280),
    y: coordinate(event.clientY, rect.top, rect.height, 800),
  };
}
async function command(path, extra = {}) {
  if ((busy && path !== '/stop') || !state) return;
  busy = true;
  render();
  $('message').textContent = '';
  const lease = { session: state.session, epoch: state.epoch };
  try {
    const r = await fetch(path, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ lease, ...extra }),
    });
    const body = await r.json();
    if (!r.ok) throw Error(errorMessage(body.code));
    state = body;
  } catch (e) {
    $('message').textContent = e.message + ' — input was not retried.';
  } finally {
    busy = false;
    try {
      state = await (await read('/status')).json();
    } catch {}
    render();
  }
}
const action = (a) => command('/action', { sequence: state.sequence, action: a });
$('desktop-size').onclick = () => {
  const actual = $('desktop-viewport').classList.toggle('actual-size');
  $('desktop-size').setAttribute('aria-pressed', String(actual));
  $('desktop-size').textContent = actual ? 'Fit to panel' : 'Actual size';
};
$('start').onclick = () => command('/start', { memberId: $('member').value });
$('takeover').onclick = () => command('/takeover');
$('resume').onclick = () => command('/resume');
$('stop').onclick = () => command('/stop');
$('send').onclick = () => {
  const text = $('text').value;
  $('text').value = '';
  if (text) action({ type: 'type', text });
};
document
  .querySelectorAll('[data-key]')
  .forEach((b) => (b.onclick = () => action({ type: 'press', key: b.dataset.key })));
$('select').onclick = () => action({ type: 'hotkey', keys: ['ctrl', 'a'] });
$('screen').onclick = (event) => {
  if (!state || state.phase !== 'human' || busy) return;
  action({ type: 'click', ...desktopPoint(event) });
};
async function refresh() {
  try {
    if (!busy) {
      state = await (await read('/status')).json();
      render();
    }
    const blob = await (await read('/frame')).blob();
    const previous = frameURL;
    frameURL = URL.createObjectURL(blob);
    $('screen').src = frameURL;
    if (previous) URL.revokeObjectURL(previous);
  } catch (e) {
    if (!e.busy) $('message').textContent = e.message;
  } finally {
    setTimeout(refresh, 800);
  }
}
refresh();
