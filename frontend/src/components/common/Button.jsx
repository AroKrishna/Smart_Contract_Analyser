import { Loader2 } from 'lucide-react';

const Button = ({
  children,
  variant = 'primary', // 'primary' | 'secondary' | 'tertiary' | 'destructive' | 'destructive-confirmed' | 'outline' | 'ghost'
  size = 'md', // 'sm' (28px) | 'md' (36px) | 'lg' (44px)
  isLoading = false,
  disabled = false,
  disabledReason = '',
  icon: Icon,
  iconPosition = 'left',
  className = '',
  type = 'button',
  onClick,
  ...props
}) => {
  // Heights and paddings as specified in Section 4 of Design Guide:
  // sm: 28px height, 12px horizontal padding
  // md: 36px height, 16px horizontal padding
  // lg: 44px height, 20px horizontal padding
  const sizeStyles = {
    sm: 'h-[28px] px-3 text-xs gap-2',
    md: 'h-[36px] px-4 text-[14px] gap-2',
    lg: 'h-[44px] px-5 text-[15px] gap-2.5',
  };

  // Button styles strictly mapped to Design Guide tokens:
  const variantStyles = {
    primary:
      'bg-[var(--accent-fill)] text-white hover:bg-[var(--accent-hover)] active:brightness-95 border-0 shadow-xs disabled:bg-[var(--surface-subtle)] disabled:text-[var(--text-muted)] disabled:border disabled:border-[var(--border)]',
    secondary:
      'bg-[var(--surface)] text-[var(--text-main)] border border-[var(--border-strong)] hover:bg-[var(--surface-subtle)] active:bg-[var(--surface-subtle)] disabled:text-[var(--text-muted)] disabled:border-[var(--border)]',
    tertiary:
      'bg-transparent text-[var(--accent)] hover:bg-[var(--accent-tint)] hover:underline border-0 disabled:text-[var(--text-muted)] disabled:no-underline',
    outline:
      'bg-[var(--surface)] text-[var(--text-main)] border border-[var(--border)] hover:bg-[var(--surface-subtle)] active:bg-[var(--surface-subtle)] disabled:text-[var(--text-muted)]',
    ghost:
      'bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] border-0 disabled:text-[var(--text-muted)]',
    destructive:
      'bg-[var(--surface)] text-[var(--critical)] border border-[var(--critical)] hover:bg-[var(--critical-tint)] active:brightness-95 disabled:text-[var(--text-muted)] disabled:border-[var(--border)]',
    'destructive-confirmed':
      'bg-[var(--critical)] text-white hover:brightness-90 active:brightness-75 border-0 disabled:opacity-50',
  };

  const currentSize = sizeStyles[size] || sizeStyles.md;
  const currentVariant = variantStyles[variant] || variantStyles.primary;

  const buttonElement = (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      aria-disabled={disabled || isLoading}
      title={disabled && disabledReason ? disabledReason : undefined}
      className={`inline-flex items-center justify-center font-medium rounded-[4px] cursor-pointer transition-colors focus-ring select-none disabled:cursor-not-allowed ${currentSize} ${currentVariant} ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current shrink-0" aria-hidden="true" />
      ) : (
        Icon && iconPosition === 'left' && <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      )}
      <span>{children}</span>
      {!isLoading && Icon && iconPosition === 'right' && (
        <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      )}
    </button>
  );

  return buttonElement;
};

export default Button;
