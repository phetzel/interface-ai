import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { resolve, sep, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { scenarioConfig } from './scenarios.mjs';

const root = fileURLToPath(new URL('../dist/', import.meta.url));
const config = scenarioConfig(process.env.FIXTURE_SCENARIO ?? 'default');
const host = process.env.HOST ?? '127.0.0.1';
const port = Number(process.env.PORT ?? 4173);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid PORT');
await stat(resolve(root, 'index.html')); // Fail readiness if the app has not been built.
const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
};

const server = createServer(async (request, response) => {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
  );
  if (!['GET', 'HEAD'].includes(request.method)) {
    response.writeHead(405, { Allow: 'GET, HEAD' }).end();
    return;
  }
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://fixture').pathname);
    if (pathname === '/healthz' || pathname === '/fixture-config.json') {
      response.setHeader('Content-Type', 'application/json');
      response.end(
        request.method === 'HEAD'
          ? undefined
          : JSON.stringify(pathname === '/healthz' ? { status: 'ready' } : config),
      );
      return;
    }
    // Only the index and Vite's assets are served. No source/tests/oracle fallback.
    if (pathname !== '/' && pathname !== '/index.html' && !pathname.startsWith('/assets/')) {
      response.writeHead(404).end();
      return;
    }
    const target = resolve(root, pathname === '/' ? 'index.html' : '.' + pathname);
    if (!target.startsWith(root + (root.endsWith(sep) ? '' : sep))) {
      response.writeHead(404).end();
      return;
    }
    const bytes = await readFile(target);
    response.setHeader('Content-Type', mime[extname(target)] ?? 'application/octet-stream');
    response.end(request.method === 'HEAD' ? undefined : bytes);
  } catch {
    response.writeHead(404).end();
  }
});
server.listen(port, host, () =>
  console.log(
    `Bank fixture ready on http://${host}:${port}; scenario=${process.env.FIXTURE_SCENARIO ?? 'default'}`,
  ),
);
for (const signal of ['SIGINT', 'SIGTERM'])
  process.on(signal, () => {
    server.close(() => process.exit(0));
    server.closeAllConnections();
  });
