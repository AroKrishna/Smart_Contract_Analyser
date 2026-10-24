import { getSeverityConfig } from '../../utils/severity';

const SeverityTag = ({ severity = 'Low', size = 'default', showWord = true, className = '' }) => {
  const config = getSeverityConfig(severity);

  // Styling adheres to design guide section 2 and 6:
  // Chip has 1px border in severity color, severity tint background, severity text color.
  const sizeClasses = size === 'sm'
    ? 'text-[11px] px-1.5 py-0.5 gap-1 font-semibold'
    : size === 'lg'
    ? 'text-sm px-2.5 py-1 gap-1.5 font-semibold'
    : 'text-xs px-2 py-0.5 gap-1.5 font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-[3px] border font-mono tracking-wider ${sizeClasses} ${className}`}
      style={{
        backgroundColor: config.tintVar,
        borderColor: config.cssVar,
        color: config.cssVar,
      }}
      aria-label={`${config.level} severity`}
    >
      <span className="text-[12px] leading-none select-none" aria-hidden="true">
        {config.shape}
      </span>
      {showWord && <span className="uppercase text-[11px] font-bold">{config.word}</span>}
    </span>
  );
};

export default SeverityTag;
