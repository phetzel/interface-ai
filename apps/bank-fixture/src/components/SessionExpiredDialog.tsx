import { useState, type FormEvent } from 'react';

export function SessionExpiredDialog({ onRestore }: { onRestore: () => void }) {
  const [recovery, setRecovery] = useState('');
  const [recoveryError, setRecoveryError] = useState(false);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (recovery !== 'demo') {
      setRecoveryError(true);
      return;
    }
    onRestore();
  }

  return (
    <div className="expiry-screen">
      <section
        className="expiry-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="expiry-title"
      >
        <h2 id="expiry-title">Session expired</h2>
        <p>Restore this synthetic workspace to continue.</p>
        <form onSubmit={submit}>
          <label htmlFor="recovery">Training code (type demo)</label>
          <input
            id="recovery"
            type="password"
            autoComplete="off"
            value={recovery}
            onChange={(event) => {
              setRecovery(event.target.value);
              setRecoveryError(false);
            }}
          />
          <button className="primary" type="submit">
            Restore workspace
          </button>
          {recoveryError && <p role="alert">Use the synthetic training code.</p>}
        </form>
        <p className="small">Training only. Do not enter a real password.</p>
      </section>
    </div>
  );
}
