const Card = ({
  children,
  title,
  subtitle,
  action,
  className = '',
  contentClassName = '',
  headerClassName = '',
  ...props
}) => {
  return (
    <div
      className={`rounded-[4px] border border-[var(--border)] bg-[var(--surface)] text-[var(--text-main)] ${className}`}
      {...props}
    >
      {(title || subtitle || action) && (
        <div
          className={`px-4 py-3 border-b border-[var(--border)] flex flex-wrap items-center justify-between gap-3 ${headerClassName}`}
        >
          <div>
            {title && (
              <h3 className="text-[15px] font-semibold text-[var(--text-main)] leading-snug">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[12px] text-[var(--text-muted)] mt-0.5 leading-normal">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-4 ${contentClassName}`}>{children}</div>
    </div>
  );
};

export default Card;
