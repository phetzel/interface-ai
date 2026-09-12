import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { members, displayAmount, type Account, type Member } from "./data";

export type Scenario = {
  searchDelayMs: number;
  blockSearch: boolean;
  duplicateSavings: boolean;
  hideBalance: boolean;
  offsetPx: number;
};
type View =
  | {
      kind: "search";
      status: "idle" | "loading" | "invalid" | "not-found";
      query: string;
    }
  | { kind: "member"; member: Member }
  | { kind: "account"; member: Member; account: Account };
const initial: View = { kind: "search", status: "idle", query: "" };

function Arrow({ back = false }: { back?: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d={back ? "M19 12H5m6 6-6-6 6-6" : "M5 12h14m-6-6 6 6-6 6"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function App({ scenario }: { scenario: Scenario }) {
  const [view, setView] = useState<View>(initial);
  const [input, setInput] = useState("");
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

  useEffect(() => {
    if (
      view.kind !== "search" ||
      view.status !== "loading" ||
      scenario.blockSearch
    )
      return;
    const timer = setTimeout(() => {
      const member = members.find((member) => member.id === view.query);
      setView(
        member ? { kind: "member", member } : { ...view, status: "not-found" },
      );
    }, scenario.searchDelayMs);
    return () => clearTimeout(timer);
  }, [view, scenario]);

  function reset() {
    setInput("");
    setView(initial);
  }
  function search(event: FormEvent) {
    event.preventDefault();
    if (view.kind === "search" && view.status === "loading") return;
    // Do not coerce to a number or pad: the exact five-character identity matters.
    setView({
      kind: "search",
      query: input,
      status: /^\d{5}$/.test(input) ? "loading" : "invalid",
    });
  }

  const member = view.kind === "search" ? undefined : view.member;
  const account = view.kind === "account" ? view.account : undefined;
  const loading = view.kind === "search" && view.status === "loading";
  const shift = {
    "--content-offset": `${scenario.offsetPx}px`,
  } as CSSProperties;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            ✳
          </span>
          <span>
            NORTHSTAR<small>MEMBER SERVICES</small>
          </span>
        </div>
        <div className="operator">
          <span className="demo-badge">Synthetic data</span>
          <span className="avatar" aria-hidden="true">
            DO
          </span>
          <span>Demo operator</span>
        </div>
      </header>
      <div className="workspace-strip">
        <span>Member workspace</span>
        <span className="read-only">
          <span aria-hidden="true">●</span> Read-only access
        </span>
      </div>
      <main className="workspace" style={shift}>
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          {member ? (
            <button onClick={reset}>Member search</button>
          ) : (
            <span>Member search</span>
          )}
          {member && (
            <>
              <span aria-hidden="true">/</span>
              {account ? (
                <button onClick={() => setView({ kind: "member", member })}>
                  {member.name}
                </button>
              ) : (
                <span>{member.name}</span>
              )}
            </>
          )}
          {account && (
            <>
              <span aria-hidden="true">/</span>
              <span>{account.type}</span>
            </>
          )}
        </nav>

        <div className="page-heading">
          <div>
            <p className="eyebrow">MEMBER SERVICES</p>
            <h1 tabIndex={-1} ref={heading}>
              {account
                ? `${account.type} account`
                : member
                  ? "Member overview"
                  : "Find a member"}
            </h1>
            <p className="lede">
              {account
                ? "Account information and current balance."
                : member
                  ? "Confirm the member, then choose an account to view."
                  : "Search by member ID to view account information."}
            </p>
          </div>
          <span className="workspace-number" aria-hidden="true">
            {account ? "03" : member ? "02" : "01"}
          </span>
        </div>

        {view.kind === "search" ? (
          <div className="search-layout">
            <section
              className="panel search-panel"
              aria-labelledby="search-title"
            >
              <div className="panel-heading">
                <span className="small-icon" aria-hidden="true">
                  ⌕
                </span>
                <h2 id="search-title">Member lookup</h2>
              </div>
              <form onSubmit={search} noValidate aria-busy={loading}>
                <label htmlFor="member-id">Member ID</label>
                <p className="field-hint" id="member-hint">
                  Enter all five digits, including leading zeroes.
                </p>
                <div className="search-controls">
                  <input
                    id="member-id"
                    type="text"
                    inputMode="numeric"
                    autoComplete="off"
                    spellCheck={false}
                    value={input}
                    disabled={loading}
                    onChange={(event) => {
                      setInput(event.target.value);
                      if (view.status !== "idle") setView(initial);
                    }}
                    aria-describedby={`member-hint${view.status === "invalid" ? " input-error" : ""}`}
                    aria-invalid={view.status === "invalid"}
                    placeholder="Enter member ID"
                  />
                  <button className="primary" type="submit" disabled={loading}>
                    {loading ? "Searching…" : "Search"}
                    {!loading && <Arrow />}
                  </button>
                </div>
                {view.status === "invalid" && (
                  <p className="error" id="input-error" role="alert">
                    Enter a member ID with exactly five digits.
                  </p>
                )}
                {loading && (
                  <div className="search-feedback" role="status">
                    <span>Looking up member {view.query}…</span>
                    <button
                      className="text-button"
                      type="button"
                      onClick={reset}
                    >
                      Cancel search
                    </button>
                  </div>
                )}
                {view.status === "not-found" && (
                  <div className="notice" role="status">
                    <strong>Member not found</strong>
                    <p>
                      No member matches ID <b>{view.query}</b>. Check the ID and
                      search again.
                    </p>
                  </div>
                )}
              </form>
              <div className="panel-foot">
                Account information is available after a member is selected.
              </div>
            </section>
            <aside className="help-panel">
              <p className="eyebrow">BEFORE YOU SEARCH</p>
              <h2>
                A little detail.
                <br />
                The right member.
              </h2>
              <p>
                Use the member’s full ID to locate their record. You can then
                review their checking and savings accounts.
              </p>
              <div className="help-rule" />
              <span className="quiet-label">TRAINING ENVIRONMENT</span>
              <p className="small">
                All members and balances in this workspace are fictional.
              </p>
            </aside>
          </div>
        ) : (
          <>
            <section className="member-banner" aria-label="Member identity">
              <div className="member-avatar" aria-hidden="true">
                {member!.name.endsWith("A") ? "DA" : "DB"}
              </div>
              <div>
                <h2>{member!.name}</h2>
                <p>
                  Member ID <strong>{member!.id}</strong>
                </p>
              </div>
              <span className="active-badge">Active member</span>
            </section>
            {view.kind === "member" ? (
              <section
                className="panel accounts-panel"
                aria-labelledby="accounts-title"
              >
                <div className="section-heading">
                  <h2 id="accounts-title">Accounts</h2>
                  <span>USD accounts</span>
                </div>
                <div className="account-list">
                  {view.member.accounts
                    .flatMap((item) =>
                      scenario.duplicateSavings && item.type === "Savings"
                        ? [item, { ...item }]
                        : [item],
                    )
                    .map((item, index) => (
                      <div
                        className="account-row"
                        key={`${item.type}-${index}`}
                      >
                        <span
                          className={`account-icon ${item.type.toLowerCase()}`}
                          aria-hidden="true"
                        >
                          {item.type === "Savings" ? "↗" : "⇄"}
                        </span>
                        <div className="account-name">
                          <h3>{item.type}</h3>
                          <p>Account ending in {item.lastFour}</p>
                        </div>
                        <span className="account-status">Open</span>
                        <button
                          className="outline"
                          aria-label={`View ${item.type.toLowerCase()}`}
                          onClick={() =>
                            setView({
                              kind: "account",
                              member: view.member,
                              account: item,
                            })
                          }
                        >
                          View account <Arrow />
                        </button>
                      </div>
                    ))}
                </div>
                <div className="panel-foot">
                  Select an account to view its balance and details.
                </div>
              </section>
            ) : (
              <section
                className="panel balance-panel"
                aria-labelledby="balance-title"
              >
                <div className="balance-main">
                  <div className="section-heading">
                    <h2 id="balance-title">Current balance</h2>
                    <span className="currency">USD</span>
                  </div>
                  {scenario.hideBalance ? (
                    <>
                      <p
                        className="balance unavailable"
                        aria-label="Balance unavailable"
                      >
                        —
                      </p>
                      <p className="balance-caption" role="status">
                        Balance unavailable. Please try again later.
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="balance">
                        {displayAmount(view.account.amountMinor)}
                      </p>
                      <p className="balance-caption">
                        Current balance in US dollars
                      </p>
                    </>
                  )}
                </div>
                <dl className="account-facts">
                  <div>
                    <dt>Account type</dt>
                    <dd>{view.account.type}</dd>
                  </div>
                  <div>
                    <dt>Account number</dt>
                    <dd>•••• {view.account.lastFour}</dd>
                  </div>
                  <div>
                    <dt>Currency</dt>
                    <dd>USD</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>Open</dd>
                  </div>
                </dl>
              </section>
            )}
            <div className="bottom-actions">
              {view.kind === "account" && (
                <button
                  className="text-button"
                  onClick={() =>
                    setView({ kind: "member", member: view.member })
                  }
                >
                  <Arrow back /> Back to accounts
                </button>
              )}
              <button className="text-button" onClick={reset}>
                Search another member <Arrow />
              </button>
            </div>
          </>
        )}
        <footer>
          <span>
            <span className="footer-mark" aria-hidden="true">
              ✳
            </span>{" "}
            Northstar member services
          </span>
          <span>Demo workspace · Synthetic records only</span>
        </footer>
      </main>
    </div>
  );
}
