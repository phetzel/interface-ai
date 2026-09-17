import type { Ref } from "react";
import type { WorkspaceView } from "../useMemberWorkspace";

export function WorkspaceHeading({
  view,
  headingRef,
  onSearch,
  onAccounts,
}: {
  view: WorkspaceView;
  headingRef: Ref<HTMLHeadingElement>;
  onSearch: () => void;
  onAccounts: () => void;
}) {
  const member = view.kind === "search" ? undefined : view.member;
  const account = view.kind === "account" ? view.account : undefined;
  return (
    <>
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        {member ? (
          <button onClick={onSearch}>Member search</button>
        ) : (
          <span>Member search</span>
        )}
        {member && (
          <>
            <span aria-hidden="true">/</span>
            {account ? (
              <button onClick={onAccounts}>{member.name}</button>
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
          <h1 tabIndex={-1} ref={headingRef}>
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
    </>
  );
}
