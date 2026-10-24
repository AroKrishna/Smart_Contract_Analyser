import Card from '../common/Card';

const StatCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeVariant = 'default',
}) => {
  return (
    <Card className="p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <Icon className="w-4 h-4 text-[var(--text-muted)]" />
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="text-[28px] font-bold text-[var(--text-main)] font-mono tracking-tight tnum">
          {value}
        </div>
        {badgeText && (
          <span
            className={`text-[11px] px-2 py-0.5 rounded-[3px] font-medium border ${
              badgeVariant === 'warning'
                ? 'bg-[var(--high-tint)] text-[var(--high)] border-[var(--high)]'
                : badgeVariant === 'danger'
                ? 'bg-[var(--critical-tint)] text-[var(--critical)] border-[var(--critical)]'
                : badgeVariant === 'success'
                ? 'bg-[var(--low-tint)] text-[var(--low)] border-[var(--low)]'
                : 'bg-[var(--surface-subtle)] text-[var(--text-secondary)] border-[var(--border)]'
            }`}
          >
            {badgeText}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-[12px] text-[var(--text-muted)] truncate">
          {subtitle}
        </p>
      )}
    </Card>
  );
};

export default StatCard;
