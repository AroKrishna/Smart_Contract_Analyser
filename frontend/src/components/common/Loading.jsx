import { Loader2 } from 'lucide-react';

const Loading = ({
  text = 'Loading...',
  size = 'md',
  fullPage = false,
  className = '',
}) => {
  const spinnerSizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const content = (
    <div
      className={`flex flex-col items-center justify-center space-y-2.5 text-[13px] ${className}`}
    >
      <Loader2
        className={`${spinnerSizes[size] || spinnerSizes.md} animate-spin text-[var(--accent)]`}
      />
      {text && (
        <span className="text-[12px] text-[var(--text-muted)] font-mono">
          {text}
        </span>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center w-full">
        {content}
      </div>
    );
  }

  return content;
};

export default Loading;
