const Input = ({
  label,
  id,
  type = 'text',
  placeholder = '',
  value,
  onChange,
  error = '',
  hint = '',
  required = false,
  disabled = false,
  className = '',
  icon: Icon,
  ...props
}) => {
  return (
    <div className="w-full space-y-1">
      {label && (
        <label
          htmlFor={id}
          className="block text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wider"
        >
          {label} {required && <span className="text-[var(--critical)]">*</span>}
        </label>
      )}

      <div className="relative rounded-[4px]">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[var(--text-muted)]">
            <Icon className="w-4 h-4" />
          </div>
        )}

        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`w-full h-[36px] text-[14px] bg-[var(--surface)] text-[var(--text-main)] placeholder-[var(--text-muted)] rounded-[4px] border border-[var(--border-strong)] focus-ring transition-colors ${
            Icon ? 'pl-9 pr-3' : 'px-3'
          } ${
            error
              ? 'border-[var(--critical)] focus:border-[var(--critical)]'
              : 'hover:border-[var(--text-secondary)] focus:border-[var(--accent)]'
          } disabled:bg-[var(--surface-subtle)] disabled:text-[var(--text-muted)] disabled:cursor-not-allowed ${className}`}
          {...props}
        />
      </div>

      {hint && !error && (
        <p className="text-[12px] text-[var(--text-muted)] mt-1">{hint}</p>
      )}

      {error && (
        <p className="text-[12px] text-[var(--critical)] mt-1 font-medium">{error}</p>
      )}
    </div>
  );
};

export default Input;
