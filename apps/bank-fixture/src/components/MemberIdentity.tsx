import type { Member } from '../data';

export function MemberIdentity({ member }: { member: Member }) {
  return (
    <section className="member-banner" aria-label="Member identity">
      <div className="member-avatar" aria-hidden="true">
        {member.name.endsWith('A') ? 'DA' : 'DB'}
      </div>
      <div>
        <h2>{member.name}</h2>
        <p>
          Member ID <strong>{member.id}</strong>
        </p>
      </div>
      <span className="active-badge">Active member</span>
    </section>
  );
}
