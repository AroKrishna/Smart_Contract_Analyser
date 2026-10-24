import { FolderSearch } from 'lucide-react';
import Button from './Button';

const EmptyState = ({
  icon: Icon = FolderSearch,
  title = 'No items found',
  description = 'There are no records matching your current criteria.',
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`p-10 text-center flex flex-col items-center justify-center space-y-2.5 text-[13px] ${className}`}
    >
      <div className="w-10 h-10 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] flex items-center justify-center text-[var(--text-muted)] mb-1">
        <Icon className="w-5 h-5" />
      </div>

      <h4 className="text-[15px] font-semibold text-[var(--text-main)]">{title}</h4>

      <p className="text-[12px] text-[var(--text-muted)] max-w-sm leading-relaxed">
        {description}
      </p>

      {actionLabel && onAction && (
        <div className="pt-2">
          <Button variant="secondary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export default EmptyState;
