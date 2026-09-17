import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import { App } from "./App";
import { parseScenario } from "./scenario";
import "./styles.css";

const root = createRoot(document.getElementById("root")!);
try {
  const response = await fetch("/fixture-config.json", { cache: "no-store" });
  if (!response.ok) throw new Error("Configuration unavailable");
  const config: unknown = await response.json();
  const scenario = parseScenario(config);
  root.render(
    <StrictMode>
      <App scenario={scenario} />
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
