import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './Button';

const ErrorState = ({
  title = 'Something went wrong',
  message = 'An unexpected error occurred while processing contract data.',
  onRetry,
  retryLabel = 'Try Again',
  className = '',
}) => {
  return (
    <div
      className={`p-8 text-center flex flex-col items-center justify-center space-y-3 rounded-[4px] border border-[var(--critical)] bg-[var(--critical-tint)] ${className}`}
    >
      <div className="w-10 h-10 rounded-[4px] bg-[var(--surface)] border border-[var(--critical)] flex items-center justify-center text-[var(--critical)] mb-1">
        <AlertTriangle className="w-5 h-5" />
      </div>

      <h4 className="text-[15px] font-semibold text-[var(--critical)]">{title}</h4>

      <p className="text-[13px] text-[var(--text-secondary)] max-w-sm leading-relaxed">
        {message}
      </p>

      {onRetry && (
        <div className="pt-2">
          <Button
            variant="destructive"
            size="sm"
            icon={RefreshCw}
            onClick={onRetry}
          >
            {retryLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

export default ErrorState;
