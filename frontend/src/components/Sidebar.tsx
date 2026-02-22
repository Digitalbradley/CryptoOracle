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
  { id: 'back', label: 'BACK', icon: '◧' },
];

export default function Sidebar({ className = '' }: { className?: string }) {
  const { logout } = useAuth();
  const active = 'dash';

  return (
    <aside
      className={`fixed top-0 left-0 bottom-0 w-14 flex-col items-center py-3 z-40 ${className}`}
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
      }}
    >
      {/* Logo */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center mb-4 gold-pulse"
        style={{
          backgroundColor: 'var(--bg-elevated)',
          border: '1.5px solid var(--accent-gold)',
        }}
      >
        <span className="text-sm">☽</span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 flex flex-col items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.id === active;
          return (
            <button
              key={item.id}
              className="w-10 h-10 flex flex-col items-center justify-center rounded-lg text-[10px] transition-colors relative"
              style={{
                color: isActive ? 'var(--accent-gold)' : 'var(--text-muted)',
                backgroundColor: isActive ? 'var(--accent-gold-dim)' : 'transparent',
                border: 'none',
                cursor: item.id === 'dash' ? 'default' : 'not-allowed',
                opacity: isActive ? 1 : 0.5,
              }}
              title={item.label}
            >
              <span className="text-sm">{item.icon}</span>
              <span className="font-mono leading-none mt-0.5">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Logout at bottom */}
      <button
        onClick={logout}
        className="w-10 h-10 flex items-center justify-center rounded-lg text-sm"
        style={{
          color: 'var(--text-muted)',
          border: 'none',
          cursor: 'pointer',
          backgroundColor: 'transparent',
        }}
        title="Logout"
      >
        ⏻
      </button>
    </aside>
  );
}
