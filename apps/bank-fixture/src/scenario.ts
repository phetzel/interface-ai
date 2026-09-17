// Launch-time rendering behavior only; never member data or expected results.
export type Scenario = {
  searchDelayMs: number;
  blockSearch: boolean;
  duplicateSavings: boolean;
  hideBalance: boolean;
  offsetPx: number;
  policyProbe: boolean;
  expireSession: boolean;
};

export function parseScenario(config: unknown): Scenario {
  if (!config || typeof config !== 'object') throw new Error('Invalid configuration');
  const value = config as Record<string, unknown>;
  if (
    typeof value.searchDelayMs !== 'number' ||
    ![250, 1800].includes(value.searchDelayMs) ||
    typeof value.offsetPx !== 'number' ||
    ![0, 40].includes(value.offsetPx) ||
    typeof value.blockSearch !== 'boolean' ||
    typeof value.duplicateSavings !== 'boolean' ||
    typeof value.hideBalance !== 'boolean' ||
    typeof value.policyProbe !== 'boolean' ||
    typeof value.expireSession !== 'boolean'
  ) {
    throw new Error('Invalid configuration');
  }
  return {
    searchDelayMs: value.searchDelayMs,
    blockSearch: value.blockSearch,
    duplicateSavings: value.duplicateSavings,
    hideBalance: value.hideBalance,
    offsetPx: value.offsetPx,
    policyProbe: value.policyProbe,
    expireSession: value.expireSession,
  };
}
