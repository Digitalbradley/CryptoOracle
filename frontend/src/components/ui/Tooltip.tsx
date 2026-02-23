import { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  text: string;
  children: React.ReactNode;
}

export default function Tooltip({ text, children }: TooltipProps) {
  const [show, setShow] = useState(false);
  const [above, setAbove] = useState(true);
  const tipRef = useRef<HTMLDivElement>(null);
  const wrapRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (show && tipRef.current && wrapRef.current) {
      const rect = wrapRef.current.getBoundingClientRect();
      setAbove(rect.top > 60);
    }
  }, [show]);

  return (
    <span
      ref={wrapRef}
      className="relative inline-flex items-center gap-0.5 cursor-help"
      style={{ borderBottom: '1px dotted var(--text-muted)' }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          ref={tipRef}
          className="absolute z-50 px-2.5 py-1.5 rounded text-[10px] leading-snug font-normal whitespace-normal pointer-events-none"
          style={{
            backgroundColor: 'var(--bg-void)',
            color: 'var(--text-secondary)',
            border: '1px solid var(--border-subtle)',
            width: 'max-content',
            maxWidth: '220px',
            left: '50%',
            transform: 'translateX(-50%)',
            ...(above
              ? { bottom: 'calc(100% + 6px)' }
              : { top: 'calc(100% + 6px)' }),
          }}
        >
          {text}
        </div>
      )}
    </span>
  );
}
