import type { Account } from "../data";
import { Arrow } from "./Arrow";

export function AccountList({
  accounts,
  duplicateSavings,
  onSelect,
}: {
  accounts: Account[];
  duplicateSavings: boolean;
  onSelect: (account: Account) => void;
}) {
  return (
    <section className="panel accounts-panel" aria-labelledby="accounts-title">
      <div className="section-heading">
        <h2 id="accounts-title">Accounts</h2>
        <span>USD accounts</span>
      </div>
      <div className="account-list">
        {accounts
          .flatMap((item) =>
            duplicateSavings && item.type === "Savings"
              ? [item, { ...item }]
              : [item],
          )
          .map((item, index) => (
            <div className="account-row" key={`${item.type}-${index}`}>
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
                onClick={() => onSelect(item)}
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
  );
}
