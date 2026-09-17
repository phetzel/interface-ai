import type { SearchState } from "../useMemberWorkspace";
import { Arrow } from "./Arrow";

export function MemberSearch({
  state,
  input,
  onInputChange,
  onSearch,
  onReset,
}: {
  state: SearchState;
  input: string;
  onInputChange: (value: string) => void;
  onSearch: () => void;
  onReset: () => void;
}) {
  const loading = state.status === "loading";
  return (
    <div className="search-layout">
      <section className="panel search-panel" aria-labelledby="search-title">
        <div className="panel-heading">
          <span className="small-icon" aria-hidden="true">
            ⌕
          </span>
          <h2 id="search-title">Member lookup</h2>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSearch();
          }}
          noValidate
          aria-busy={loading}
        >
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
              onChange={(event) => onInputChange(event.target.value)}
              aria-describedby={`member-hint${state.status === "invalid" ? " input-error" : ""}`}
              aria-invalid={state.status === "invalid"}
              placeholder="Enter member ID"
            />
            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Searching…" : "Search"}
              {!loading && <Arrow />}
            </button>
          </div>
          {state.status === "invalid" && (
            <p className="error" id="input-error" role="alert">
              Enter a member ID with exactly five digits.
            </p>
          )}
          {loading && (
            <div className="search-feedback" role="status">
              <span>Looking up member {state.query}…</span>
              <button className="text-button" type="button" onClick={onReset}>
                Cancel search
              </button>
            </div>
          )}
          {state.status === "not-found" && (
            <div className="notice" role="status">
              <strong>Member not found</strong>
              <p>
                No member matches ID <b>{state.query}</b>. Check the ID and
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
          Use the member’s full ID to locate their record. You can then review
          their checking and savings accounts.
        </p>
        <div className="help-rule" />
        <span className="quiet-label">TRAINING ENVIRONMENT</span>
        <p className="small">
          All members and balances in this workspace are fictional.
        </p>
      </aside>
    </div>
  );
}
