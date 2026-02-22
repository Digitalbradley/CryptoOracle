import { useState, type FormEvent } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [shaking, setShaking] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ backgroundColor: 'var(--bg-void)' }}>
        <div className="gold-pulse w-12 h-12 rounded-full" style={{ backgroundColor: 'var(--bg-surface)', border: '2px solid var(--accent-gold)' }} />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      await login(username, password);
    } catch {
      setError('Invalid credentials');
      setShaking(true);
      setTimeout(() => setShaking(false), 500);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ backgroundColor: 'var(--bg-void)' }}>
      {/* Starfield background */}
      <div className="starfield" />

      {/* Login card */}
      <div
        className={`relative z-10 w-full max-w-sm rounded-xl p-8 ${shaking ? 'shake' : ''}`}
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Oracle symbol */}
        <div className="flex justify-center mb-6">
          <div
            className="gold-pulse w-20 h-20 rounded-full flex items-center justify-center"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '2px solid var(--accent-gold)',
            }}
          >
            <svg
              width="40"
              height="40"
              viewBox="0 0 40 40"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Crescent moon */}
              <path
                d="M28 20c0 6.627-5.373 12-12 12-1.19 0-2.34-.173-3.427-.496A12 12 0 0020 8a12 12 0 008 12z"
                fill="var(--accent-gold)"
                opacity="0.9"
              />
              {/* Star */}
              <path
                d="M30 10l1.176 2.382 2.632.383-1.904 1.855.45 2.62L30 16.12l-2.354 1.12.45-2.62-1.904-1.855 2.632-.383z"
                fill="var(--accent-gold)"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h1
          className="text-2xl font-bold text-center mb-1"
          style={{ color: 'var(--accent-gold)', fontFamily: '"Inter", sans-serif' }}
        >
          CryptoOracle
        </h1>
        <p
          className="text-sm text-center mb-8 tracking-widest uppercase"
          style={{ color: 'var(--text-muted)', fontSize: '11px', letterSpacing: '0.2em' }}
        >
          Celestial Terminal
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label
              htmlFor="username"
              className="block text-xs font-medium mb-1.5"
              style={{ color: 'var(--text-secondary)' }}
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              autoFocus
              className="w-full rounded-lg px-3.5 text-sm outline-none transition-all"
              style={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                height: '44px',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--accent-gold)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--border-subtle)')}
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-xs font-medium mb-1.5"
              style={{ color: 'var(--text-secondary)' }}
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full rounded-lg px-3.5 pr-12 text-sm outline-none transition-all"
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  height: '44px',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'var(--accent-gold)')}
                onBlur={(e) => (e.target.style.borderColor = 'var(--border-subtle)')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs"
                style={{ color: 'var(--text-muted)' }}
                tabIndex={-1}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <p className="text-sm text-center" style={{ color: 'var(--severity-critical)' }}>
              {error}
            </p>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg font-semibold text-sm transition-all flex items-center justify-center gap-2"
            style={{
              backgroundColor: submitting ? 'var(--accent-gold-hover)' : 'var(--accent-gold)',
              color: 'var(--bg-void)',
              height: '44px',
              cursor: submitting ? 'wait' : 'pointer',
            }}
            onMouseEnter={(e) => {
              if (!submitting) (e.target as HTMLElement).style.backgroundColor = 'var(--accent-gold-hover)';
            }}
            onMouseLeave={(e) => {
              if (!submitting) (e.target as HTMLElement).style.backgroundColor = 'var(--accent-gold)';
            }}
          >
            {submitting && <span className="spinner" />}
            {submitting ? 'Authenticating...' : 'Enter the Oracle'}
          </button>
        </form>

        {/* Footer */}
        <p
          className="text-center mt-8"
          style={{ color: 'var(--text-muted)', fontSize: '10px', letterSpacing: '0.15em' }}
        >
          ESOTERIC TRADING INTELLIGENCE
        </p>
      </div>
    </div>
  );
}
