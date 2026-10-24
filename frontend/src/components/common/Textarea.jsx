const Textarea = ({
  label,
  id,
  rows = 14,
  placeholder = '',
  value,
  onChange,
  error = '',
  hint = '',
  required = false,
  disabled = false,
  className = '',
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

      <textarea
        id={id}
        rows={rows}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        className={`w-full text-[13px] bg-[var(--surface)] text-[var(--text-main)] placeholder-[var(--text-muted)] rounded-[4px] border border-[var(--border-strong)] p-3 focus-ring transition-colors font-mono leading-relaxed ${
          error
            ? 'border-[var(--critical)] focus:border-[var(--critical)]'
            : 'hover:border-[var(--text-secondary)] focus:border-[var(--accent)]'
        } disabled:bg-[var(--surface-subtle)] disabled:text-[var(--text-muted)] disabled:cursor-not-allowed ${className}`}
        {...props}
      />

      {hint && !error && (
        <p className="text-[12px] text-[var(--text-muted)] mt-1">{hint}</p>
      )}

      {error && (
        <p className="text-[12px] text-[var(--critical)] mt-1 font-medium">{error}</p>
      )}
    </div>
  );
};

export default Textarea;
