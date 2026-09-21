// The server injects the process token into this script's nonce-protected scope.
const $ = (id) => document.getElementById(id);
let state = null,
  busy = false,
  frameURL = null;
let appInitialized = false;
let workflowInitialized = false;
let pendingJob = null;
let host = null,
  hostBusy = false,
  workflows = [];
const hostURL = 'http://127.0.0.1:6082';
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
  const nativeIdle = state.app === 'native' && state.phase === 'idle';
  $('lookup-controls').hidden = state.phase !== 'idle' || state.app === 'native';
  $('human-controls').hidden = state.phase !== 'human';
  $('takeover').hidden =
    !nativeIdle && !['running', 'awaiting_human', 'quiescing'].includes(state.phase);
  $('resume').hidden = state.phase !== 'human' || state.runKind === 'native_manual';
  $('member').disabled = state.phase !== 'idle';
  $('takeover').disabled =
    busy || (!nativeIdle && !['running', 'awaiting_human'].includes(state.phase));
  $('resume').disabled = !human || !state.resumable;
  $('stop').disabled = state.phase === 'stopped';
  for (const id of ['send', 'select', 'text', 'scroll-up', 'scroll-down']) $(id).disabled = !human;
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
  if (nativeIdle)
    $('guidance').textContent =
      'Take control to try native clicking, typing and scrolling. Saved bank workflows and discovery use Northstar bank.';
  if (state.runKind === 'native_manual' && state.phase === 'human')
    $('guidance').textContent =
      'You control the native test pad. Stop when finished, then choose another app.';
  if (state.evidenceStatus === 'failed')
    $('guidance').textContent =
      'Input stopped because run evidence could not be saved. Inspect storage and reset the desktop.';
  renderLauncher();
}
function renderLauncher() {
  if (!workflowInitialized && state && workflows.length) {
    $('workflow').value = state.capability;
    workflowInitialized = true;
  }
  if (!appInitialized && host && state && $('app-choice').options.length === host.apps.length) {
    $('app-choice').value =
      host.session === state.session && host.job?.app ? host.job.app : state.app;
    appInitialized = true;
  }
  const ready = !!host && !!state && !hostBusy && !busy && !host.active;
  $('start').disabled =
    !state ||
    !workflows.length ||
    busy ||
    hostBusy ||
    host?.active ||
    state.phase !== 'idle' ||
    state.app === 'native';
  const terminal = [
    'idle',
    'success',
    'failure',
    'business_outcome',
    'stopped',
    'probe_complete',
    'probe_failed',
  ].includes(state?.phase);
  $('switch-app').disabled = !ready || !terminal;
  $('discover').disabled = !ready || !terminal;
  if (state) $('stop').disabled = state.phase === 'stopped' && !host?.active;
  $('workflow').disabled =
    !state || state.phase !== 'idle' || state.app !== 'bank' || !workflows.length;
  const selected = workflows.find((w) => w.id === $('workflow').value);
  $('workflow-info').textContent = selected
    ? `${selected.version} · ${selected.provenance} · approved · zero-model replay`
    : 'Loading approved workflows…';
}
async function hostCommand(path, body) {
  if (!host || (hostBusy && path !== '/stop')) return;
  hostBusy = true;
  renderLauncher();
  try {
    const response = await fetch(hostURL + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Host-Token': host.token },
      body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw Error(result.message || 'Launcher rejected this request');
    host = { ...result, token: host.token };
    if (path === '/jobs') pendingJob = host.job.id;
    $('message').textContent = '';
  } catch (error) {
    $('message').textContent = error.message + ' — request was not retried.';
  } finally {
    hostBusy = false;
    renderLauncher();
  }
}
async function refreshHost() {
  try {
    const response = await fetch(hostURL + '/status', { cache: 'no-store' });
    if (!response.ok) throw Error();
    host = await response.json();
    if ($('app-choice').options.length !== host.apps.length) {
      $('app-choice').replaceChildren(...host.apps.map((app) => new Option(app.label, app.id)));
    }
    const job = host.job;
    if (host.active && job?.stage === 'Starting desktop') pendingJob = job.id;
    $('host-status').textContent = job
      ? `${job.stage}${job.evidence ? ' · ' + job.requests + ' model requests · Evidence: ' + job.evidence : ''}`
      : 'Local launcher ready. Your API key stays on the host.';
    // Refresh only a job this page observed replacing its desktop. An old host
    // result must not reload a new page after an unrelated CLI reset.
    if (
      state &&
      job &&
      pendingJob === job.id &&
      job.stage !== 'Starting desktop' &&
      host.session !== state.session
    ) {
      location.reload();
      return;
    }
    renderLauncher();
  } catch {
    host = null;
    $('host-status').textContent =
      'Local launcher unavailable. Run make up from this checkout. Existing desktop controls still work.';
    renderLauncher();
  } finally {
    setTimeout(refreshHost, 1000);
  }
}
async function loadWorkflows() {
  try {
    workflows = await (await read('/workflows')).json();
    $('workflow').replaceChildren(...workflows.map((w) => new Option(w.id, w.id)));
    renderLauncher();
  } catch {
    $('workflow-info').textContent = 'Approved workflows unavailable';
  }
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
$('start').onclick = () =>
  command('/start', { memberId: $('member').value, capability: $('workflow').value });
$('workflow').onchange = renderLauncher;
$('switch-app').onclick = () =>
  hostCommand('/jobs', { kind: 'switch', session: state.session, app: $('app-choice').value });
$('discover').onclick = () =>
  hostCommand('/jobs', { kind: 'discover', session: state.session, goal: $('goal').value });
$('takeover').onclick = () => command('/takeover');
$('resume').onclick = () => command('/resume');
$('stop').onclick = () => {
  hostCommand('/stop', {});
  command('/stop');
};
$('send').onclick = () => {
  const text = $('text').value;
  $('text').value = '';
  if (text) action({ type: 'type', text });
};
document
  .querySelectorAll('[data-key]')
  .forEach((b) => (b.onclick = () => action({ type: 'press', key: b.dataset.key })));
$('select').onclick = () => action({ type: 'hotkey', keys: ['ctrl', 'a'] });
$('scroll-up').onclick = () => action({ type: 'scroll', amount: 3 });
$('scroll-down').onclick = () => action({ type: 'scroll', amount: -3 });
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
refreshHost();
loadWorkflows();
