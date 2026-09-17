import { useEffect, useRef, type CSSProperties } from 'react';
import { AccountDetails } from './components/AccountDetails';
import { AccountList } from './components/AccountList';
import { Arrow } from './components/Arrow';
import { MemberIdentity } from './components/MemberIdentity';
import { MemberSearch } from './components/MemberSearch';
import { PolicyProbe } from './components/PolicyProbe';
import { SessionExpiredDialog } from './components/SessionExpiredDialog';
import { WorkspaceHeading } from './components/WorkspaceHeading';
import { WorkspaceFooter, WorkspaceHeader } from './components/WorkspaceLayout';
import type { Scenario } from './scenario';
import { useMemberWorkspace } from './useMemberWorkspace';

export function App({ scenario }: { scenario: Scenario }) {
  const workspace = useMemberWorkspace(scenario);
  const { view } = workspace;
  const heading = useRef<HTMLHeadingElement>(null);
  const firstRender = useRef(true);

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    window.scrollTo(0, 0);
    heading.current?.focus({ preventScroll: true });
  }, [view.kind]);

  const shift = {
    '--content-offset': `${scenario.offsetPx}px`,
  } as CSSProperties;

  return (
    <div className="app-shell">
      <WorkspaceHeader />
      <main className="workspace" style={shift} inert={workspace.expired}>
        <WorkspaceHeading
          view={view}
          headingRef={heading}
          onSearch={workspace.reset}
          onAccounts={workspace.showAccounts}
        />
        {view.kind === 'search' ? (
          <MemberSearch
            state={view}
            input={workspace.input}
            onInputChange={workspace.changeInput}
            onSearch={workspace.search}
            onReset={workspace.reset}
          />
        ) : (
          <>
            <MemberIdentity member={view.member} />
            {view.kind === 'member' ? (
              <AccountList
                accounts={view.member.accounts}
                duplicateSavings={scenario.duplicateSavings}
                onSelect={workspace.openAccount}
              />
            ) : (
              <AccountDetails account={view.account} hideBalance={scenario.hideBalance} />
            )}
            <div className="bottom-actions">
              {view.kind === 'account' && (
                <button className="text-button" onClick={workspace.showAccounts}>
                  <Arrow back /> Back to accounts
                </button>
              )}
              <button className="text-button" onClick={workspace.reset}>
                Search another member <Arrow />
              </button>
            </div>
          </>
        )}
        <WorkspaceFooter />
      </main>
      {workspace.expired && <SessionExpiredDialog onRestore={workspace.restoreSession} />}
      {scenario.policyProbe && <PolicyProbe />}
    </div>
  );
}
