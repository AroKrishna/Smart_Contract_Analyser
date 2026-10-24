import SeverityTag from './SeverityTag';

const Badge = ({
  children,
  variant = 'default',
  riskLevel,
  size = 'md',
  dot = false,
  className = '',
}) => {
  if (riskLevel) {
    return (
      <SeverityTag
        severity={riskLevel}
        size={size === 'lg' ? 'lg' : size === 'sm' ? 'sm' : 'default'}
        className={className}
      />
    );
  }

  const sizes = {
    sm: 'text-[11px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2 py-0.5 gap-1.5',
    lg: 'text-xs px-2.5 py-1 gap-2',
  };

  const variants = {
    default: 'bg-[var(--surface-subtle)] text-[var(--text-secondary)] border-[var(--border)]',
    info: 'bg-[var(--accent-tint)] text-[var(--accent)] border-[var(--accent)]/30',
    success: 'bg-[var(--low-tint)] text-[var(--low)] border-[var(--low)]/40',
    warning: 'bg-[var(--high-tint)] text-[var(--high)] border-[var(--high)]/40',
    danger: 'bg-[var(--critical-tint)] text-[var(--critical)] border-[var(--critical)]/40',
  };

  const currentVariant = variants[variant] || variants.default;

  return (
    <span
      className={`inline-flex items-center font-medium rounded-[3px] border ${currentVariant} ${sizes[size] || sizes.md} ${className}`}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
};

export default Badge;
