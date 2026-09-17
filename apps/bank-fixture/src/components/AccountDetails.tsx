import { displayAmount, type Account } from "../data";

export function AccountDetails({
  account,
  hideBalance,
}: {
  account: Account;
  hideBalance: boolean;
}) {
  return (
    <section className="panel balance-panel" aria-labelledby="balance-title">
      <div className="balance-main">
        <div className="section-heading">
          <h2 id="balance-title">Current balance</h2>
          <span className="currency">USD</span>
        </div>
        {hideBalance ? (
          <>
            <p className="balance unavailable" aria-label="Balance unavailable">
              —
            </p>
            <p className="balance-caption" role="status">
              Balance unavailable. Please try again later.
            </p>
          </>
        ) : (
          <>
            <p className="balance">{displayAmount(account.amountMinor)}</p>
            <p className="balance-caption">Current balance in US dollars</p>
          </>
        )}
      </div>
      <dl className="account-facts">
        <div>
          <dt>Account type</dt>
          <dd>{account.type}</dd>
        </div>
        <div>
          <dt>Account number</dt>
          <dd>•••• {account.lastFour}</dd>
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
  );
}
