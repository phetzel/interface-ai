import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { scenarioConfig } from './server/scenarios.mjs';

// Dev and production use the same launch-time scenario. No query-string controls.
const scenario = scenarioConfig(process.env.FIXTURE_SCENARIO ?? 'default');
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'fixture-launch-config',
      configureServer(server) {
        server.middlewares.use('/fixture-config.json', (_req, res) => {
          res.setHeader('Content-Type', 'application/json');
          res.setHeader('Cache-Control', 'no-store');
          res.end(JSON.stringify(scenario));
        });
      },
    },
  ],
  build: { sourcemap: false },
});
