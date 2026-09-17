"""Trusted application startup checks. Business-task actions never use HTTP/DOM."""

import json
from pathlib import Path
import urllib.request

BANK_URL = 'http://fixture:4173/'


def chromium_command():
    return [
        'chromium',
        '--user-data-dir=/tmp/interface-ai/chromium-profile',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-background-networking',
        '--disable-extensions',
        '--disable-sync',
        '--disable-default-apps',
        '--password-store=basic',
        '--no-proxy-server',
        '--force-device-scale-factor=1',
        '--lang=en-US',
        '--kiosk',
        BANK_URL,
    ]


def fixture_ready():
    with urllib.request.urlopen(BANK_URL + 'healthz', timeout=2) as response:
        return response.status == 200 and json.load(response) == {'status': 'ready'}


def active_application(mode):
    from Xlib import Xatom
    from Xlib.display import Display

    display = Display()
    try:
        root = display.screen().root
        prop = root.get_full_property(display.intern_atom('_NET_ACTIVE_WINDOW'), Xatom.WINDOW)
        if prop is None or not len(prop.value) or not prop.value[0]:
            return None
        window = display.create_resource_object('window', int(prop.value[0]))
        name = window.get_full_property(
            display.intern_atom('_NET_WM_NAME'), display.intern_atom('UTF8_STRING')
        )
        value = name.value if name is not None else window.get_wm_name() or ''
        title = value if isinstance(value, str) else bytes(value).decode('utf-8', 'replace')
        expected = 'Northstar' if mode == 'bank' else 'interface-ai desktop calibration'
        if expected not in title:
            return None
        return {'windowId': window.id, 'windowClass': list(window.get_wm_class() or ())}
    finally:
        display.close()


def sandbox_status(browser_pid):
    """Check renderer namespaces and additional seccomp filters, not just flags."""
    processes = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            status = dict(
                line.split(':', 1)
                for line in (directory / 'status').read_text().splitlines()
                if ':' in line
            )
            # Chromium rewrites child argv as one space-separated process title.
            args = (directory / 'cmdline').read_bytes().replace(b'\0', b' ').split()
            processes[int(directory.name)] = (status, args)
        except (OSError, ValueError):
            continue
    if browser_pid not in processes:
        return None
    outer_filters = int(processes[browser_pid][0].get('Seccomp_filters', '0'))
    verified = []
    for pid, (status, args) in processes.items():
        if b'--type=renderer' not in args:
            continue
        ancestor = pid
        seen = set()
        while ancestor in processes and ancestor not in seen and ancestor != browser_pid:
            seen.add(ancestor)
            ancestor = int(processes[ancestor][0]['PPid'])
        if ancestor != browser_pid:
            continue
        item = {
            'pid': pid,
            'noNewPrivileges': status.get('NoNewPrivs', '').strip() == '1',
            'seccompMode': int(status.get('Seccomp', '0')),
            'filterCount': int(status.get('Seccomp_filters', '0')),
            'pidNamespaceDepth': len(status.get('NSpid', '').split()),
            'effectiveCapabilities': status.get('CapEff', '').strip(),
            'disableSandboxFlag': any(
                arg in args for arg in (b'--no-sandbox', b'--disable-seccomp-filter-sandbox')
            ),
        }
        if not (
            item['noNewPrivileges']
            and item['seccompMode'] == 2
            and item['filterCount'] > outer_filters
            and item['pidNamespaceDepth'] >= 2
            and int(item['effectiveCapabilities'], 16) == 0
            and not item['disableSandboxFlag']
        ):
            raise RuntimeError('Chromium renderer sandbox verification failed')
        verified.append(item)
    return {'browserFilterCount': outer_filters, 'renderers': verified} if verified else None


def assert_known_surface(image, mode):
    # Dedicated synthetic environment only; this is not general-purpose redaction.
    if image.size != (1280, 800):
        raise RuntimeError('Unexpected screenshot dimensions')
    samples = {
        'native': [
            ((10, 10), (15, 23, 42)),
            ((10, 110), (241, 245, 249)),
            ((1270, 790), (241, 245, 249)),
        ],
        'bank': [
            ((5, 20), (255, 255, 255)),
            ((5, 120), (24, 56, 61)),
            ((20, 300), (245, 246, 244)),
        ],
    }[mode]
    if any(image.getpixel(point)[:3] != color for point, color in samples):
        raise RuntimeError('Unknown surface; synthetic screenshot export suppressed')


def bank_painted():
    from interface_ai.desktop.backend import X11Backend

    backend = X11Backend()
    try:
        assert_known_surface(backend.screenshot(), 'bank')
        return True
    except RuntimeError:
        return False
    finally:
        backend.close()
