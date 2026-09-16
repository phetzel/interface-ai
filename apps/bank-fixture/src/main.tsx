import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import { App, type Scenario } from "./App";
import "./styles.css";

const root = createRoot(document.getElementById("root")!);
try {
  const response = await fetch("/fixture-config.json", { cache: "no-store" });
  if (!response.ok) throw new Error("Configuration unavailable");
  const config: unknown = await response.json();
  if (!config || typeof config !== "object")
    throw new Error("Invalid configuration");
  const value = config as Record<string, unknown>;
  if (
    typeof value.searchDelayMs !== "number" ||
    ![250, 1800].includes(value.searchDelayMs) ||
    typeof value.offsetPx !== "number" ||
    ![0, 40].includes(value.offsetPx) ||
    ["blockSearch", "duplicateSavings", "hideBalance", "policyProbe"].some(
      (key) => typeof value[key] !== "boolean",
    )
  ) {
    throw new Error("Invalid configuration");
  }
  root.render(
    <StrictMode>
      <App scenario={config as Scenario} />
    </StrictMode>,
  );
} catch {
  root.render(
    <main className="startup-error">
      <h1>Workspace unavailable</h1>
      <p>Reload the page to try again.</p>
    </main>,
  );
}
