export function WorkspaceHeader() {
  return (
    <>
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
    </>
  );
}

export function WorkspaceFooter() {
  return (
    <footer>
      <span>
        <span className="footer-mark" aria-hidden="true">
          ✳
        </span>{" "}
        Northstar member services
      </span>
      <span>Demo workspace · Synthetic records only</span>
    </footer>
  );
}
