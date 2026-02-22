import { useEffect, useState } from 'react';
import { useAuth } from '../auth/AuthContext';

export default function StatusBar({ className = '' }: { className?: string }) {
  const { user } = useAuth();
  const [lastUpdate, setLastUpdate] = useState('');

  useEffect(() => {
    const tick = () => {
      setLastUpdate(new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'UTC',
      }));
    };
    tick();
    const id = setInterval(tick, 10_000);
    return () => clearInterval(id);
  }, []);

  return (
    <footer
      className={`h-7 flex items-center justify-between px-4 font-mono text-[10px] ${className}`}
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
        color: 'var(--text-muted)',
      }}
    >
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: 'var(--signal-bullish)' }}
          />
          CONNECTED
        </span>
        <span>|</span>
        <span>Last update: {lastUpdate}</span>
      </div>
      <span>User: {user}</span>
    </footer>
  );
}
