import { useAuth } from '../auth/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ backgroundColor: 'var(--bg-void)' }}
    >
      <div className="starfield" />

      <div
        className="relative z-10 w-full max-w-sm rounded-xl p-8 text-center"
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Oracle symbol */}
        <div className="flex justify-center mb-4">
          <div
            className="gold-pulse w-16 h-16 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '2px solid var(--accent-gold)',
            }}
          >
            <span className="text-2xl">☽</span>
          </div>
        </div>

        <h1
          className="text-xl font-bold mb-2"
          style={{ color: 'var(--accent-gold)' }}
        >
          CryptoOracle
        </h1>

        <p className="text-sm mb-1" style={{ color: 'var(--text-primary)' }}>
          Welcome, <span className="font-mono font-semibold">{user}</span>
        </p>

        <p className="text-xs mb-6" style={{ color: 'var(--text-muted)' }}>
          Dashboard coming soon — Phase 5b
        </p>

        <div
          className="rounded-lg p-4 mb-6 text-left text-xs font-mono space-y-1"
          style={{
            backgroundColor: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
          }}
        >
          <p>System Status: <span style={{ color: 'var(--signal-bullish)' }}>Online</span></p>
          <p>Auth: <span style={{ color: 'var(--signal-bullish)' }}>Authenticated</span></p>
          <p>Layers: <span style={{ color: 'var(--text-primary)' }}>6/6 active</span></p>
          <p>Scheduler: <span style={{ color: 'var(--signal-bullish)' }}>Running</span></p>
        </div>

        <button
          onClick={logout}
          className="w-full rounded-lg text-sm font-medium transition-all"
          style={{
            backgroundColor: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            height: '40px',
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => (e.target as HTMLElement).style.borderColor = 'var(--accent-gold)'}
          onMouseLeave={(e) => (e.target as HTMLElement).style.borderColor = 'var(--border-subtle)'}
        >
          Logout
        </button>
      </div>
    </div>
  );
}
