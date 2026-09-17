// Fictional display data. The acceptance oracle is authored separately in tests/.
export type Account = {
  type: 'Checking' | 'Savings';
  lastFour: string;
  amountMinor: number;
};
export type Member = { id: string; name: string; accounts: Account[] };
export const members: readonly Member[] = [
  {
    id: '00123',
    name: 'Demo Member A',
    accounts: [
      { type: 'Checking', lastFour: '3108', amountMinor: 842019 },
      { type: 'Savings', lastFour: '7421', amountMinor: 123456 },
    ],
  },
  {
    id: '00456',
    name: 'Demo Member B',
    accounts: [
      { type: 'Checking', lastFour: '8820', amountMinor: 231640 },
      { type: 'Savings', lastFour: '1956', amountMinor: 9807 },
    ],
  },
];

// Integer cents remain authoritative; no parsing or floating-point arithmetic.
export function displayAmount(amountMinor: number): string {
  return `$${Math.floor(amountMinor / 100).toLocaleString('en-US')}.${String(amountMinor % 100).padStart(2, '0')}`;
}
