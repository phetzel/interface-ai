# Chromium sandbox profile

`chromium-seccomp.json` is based on Microsoft's [Playwright v1.63.0 profile](https://github.com/microsoft/playwright/blob/v1.63.0/utils/docker/seccomp_profile.json), retrieved 2026-09-12. The original file SHA-256 is `cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849`. Its Apache license is included as `chromium-seccomp.LICENSE`.

The upstream profile uses a default-deny syscall policy and permits `clone`, `setns`, and `unshare` for browser user namespaces. See [Playwright's Docker guidance](https://playwright.dev/docs/docker). Only the desktop service uses this profile; fixture and viewer retain their existing settings.

One local rule allows `chroot`. Without it, the tested Chromium build entered its user namespace but failed its private `chroot` operation. The kernel still checks the caller's namespace capabilities: no outer-container capability was added. The desktop remains non-root with `cap_drop: ALL` and `no-new-privileges:true`; it uses neither privileged mode nor host IPC/networking.

Chromium launches with its sandbox enabled and no remote-debugging interface. Startup checks renderer processes for extra seccomp filters beyond the container filter, nested PID namespaces, no effective capabilities, and no-new-privileges. A failed check aborts startup rather than adding `--no-sandbox`. These checks establish the selected launch configuration, not general hostile-code containment or application/action policy.
