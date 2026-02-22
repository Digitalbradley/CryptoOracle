import { useAuth } from '../auth/AuthContext';

interface NavItem {
  id: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dash', label: 'DASH', icon: '⬡' },
  { id: 'sign', label: 'SIGN', icon: '◈' },
  { id: 'cycl', label: 'CYCL', icon: '↻' },
  { id: 'cale', label: 'CALE', icon: '▦' },
  { id: 'gema', label: 'GEMA', icon: 'ℵ' },
];

export default function BottomNav({ className = '' }: { className?: string }) {
  const { logout } = useAuth();
  const active = 'dash';

  return (
    <nav
      className={`fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around h-14 ${className}`}
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
        paddingBottom: 'env(safe-area-inset-bottom, 0px)',
      }}
    >
      {NAV_ITEMS.map((item) => {
        const isActive = item.id === active;
        return (
          <button
            key={item.id}
            className="flex flex-col items-center justify-center h-11 min-w-11 px-1"
            style={{
              color: isActive ? 'var(--accent-gold)' : 'var(--text-muted)',
              border: 'none',
              cursor: item.id === 'dash' ? 'default' : 'not-allowed',
              opacity: isActive ? 1 : 0.5,
              backgroundColor: 'transparent',
            }}
          >
            <span className="text-base">{item.icon}</span>
            <span className="font-mono text-[9px] leading-none mt-0.5">{item.label}</span>
          </button>
        );
      })}
      <button
        onClick={logout}
        className="flex flex-col items-center justify-center h-11 min-w-11 px-1"
        style={{
          color: 'var(--text-muted)',
          border: 'none',
          cursor: 'pointer',
          backgroundColor: 'transparent',
        }}
      >
        <span className="text-base">⏻</span>
        <span className="font-mono text-[9px] leading-none mt-0.5">OUT</span>
      </button>
    </nav>
  );
}
