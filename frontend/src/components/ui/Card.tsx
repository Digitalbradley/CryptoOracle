import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  layerColor?: string;
}

export default function Card({ children, className = '', title, layerColor }: CardProps) {
  return (
    <div
      className={`rounded-xl p-4 ${className}`}
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderLeft: layerColor ? `3px solid ${layerColor}` : undefined,
      }}
    >
      {title && (
        <h3
          className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: 'var(--text-secondary)' }}
        >
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
