import { useEffect, useState } from 'react';
import { members, type Account, type Member } from './data';
import type { Scenario } from './scenario';

export type SearchState = {
  kind: 'search';
  status: 'idle' | 'loading' | 'invalid' | 'not-found';
  query: string;
};
export type WorkspaceView =
  | SearchState
  | { kind: 'member'; member: Member }
  | { kind: 'account'; member: Member; account: Account };

const initial: SearchState = { kind: 'search', status: 'idle', query: '' };

// Owns navigation and the simulated lookup. Inputs stay exact strings, and
// leaving a loading view cancels its timer so an old lookup cannot navigate.
export function useMemberWorkspace(scenario: Scenario) {
  const [view, setView] = useState<WorkspaceView>(initial);
  const [input, setInput] = useState('');
  const [expired, setExpired] = useState(false);
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    if (view.kind !== 'search' || view.status !== 'loading' || scenario.blockSearch) return;
    const timer = setTimeout(() => {
      const member = members.find((member) => member.id === view.query);
      if (member && scenario.expireSession && !restored) setExpired(true);
      setView(member ? { kind: 'member', member } : { ...view, status: 'not-found' });
    }, scenario.searchDelayMs);
    return () => clearTimeout(timer);
  }, [view, scenario, restored]);

  function reset() {
    setInput('');
    setView(initial);
  }

  function changeInput(value: string) {
    setInput(value);
    if (view.kind === 'search' && view.status !== 'idle') setView(initial);
  }

  function search() {
    if (view.kind === 'search' && view.status === 'loading') return;
    // Do not coerce to a number or pad: the exact five-character identity matters.
    setView({
      kind: 'search',
      query: input,
      status: /^\d{5}$/.test(input) ? 'loading' : 'invalid',
    });
  }

  function openAccount(account: Account) {
    if (view.kind !== 'search') setView({ kind: 'account', member: view.member, account });
  }

  function showAccounts() {
    if (view.kind !== 'search') setView({ kind: 'member', member: view.member });
  }

  function restoreSession() {
    // Restoration lasts until page reload, including subsequent member searches.
    setRestored(true);
    setExpired(false);
  }

  return {
    view,
    input,
    expired,
    changeInput,
    search,
    reset,
    openAccount,
    showAccounts,
    restoreSession,
  };
}
