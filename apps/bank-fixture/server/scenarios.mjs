/** Harness-controlled launch configuration; no member data or expected results. */
export const scenarioNames = [
  "default",
  "delayed",
  "blocked",
  "duplicate",
  "unreadable",
  "translated",
];

export function scenarioConfig(name) {
  if (!scenarioNames.includes(name)) {
    throw new Error(
      `Unknown FIXTURE_SCENARIO: ${name}. Choose ${scenarioNames.join(", ")}.`,
    );
  }
  return {
    searchDelayMs: name === "delayed" ? 1800 : 250,
    blockSearch: name === "blocked",
    duplicateSavings: name === "duplicate",
    hideBalance: name === "unreadable",
    offsetPx: name === "translated" ? 40 : 0,
  };
}
