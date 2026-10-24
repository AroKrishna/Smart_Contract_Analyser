import { useRef } from 'react';
import SeverityTag from '../common/SeverityTag';
import { RISK_CATEGORIES } from '../../utils/constants';

const FindingsOutline = ({
  findings = [],
  selectedFindingId = null,
  onSelectFinding = () => {},
  selectedCategory = 'All',
  onSelectCategory = () => {},
  onEnterPress = () => {},
}) => {
  const listRef = useRef(null);

  // Compute category counts
  const categoryCounts = { All: findings.length };
  RISK_CATEGORIES.forEach((cat) => {
    categoryCounts[cat] = findings.filter((f) => f.category === cat).length;
  });

  // Filtered findings
  const displayedFindings = selectedCategory === 'All'
    ? findings
    : findings.filter((f) => f.category === selectedCategory);

  // Keyboard navigation inside list
  const handleKeyDown = (e, index) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (index + 1) % displayedFindings.length;
      const nextId = displayedFindings[nextIndex].findingId || displayedFindings[nextIndex].id || `f-${nextIndex + 1}`;
      onSelectFinding(nextId);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = (index - 1 + displayedFindings.length) % displayedFindings.length;
      const prevId = displayedFindings[prevIndex].findingId || displayedFindings[prevIndex].id || `f-${prevIndex + 1}`;
      onSelectFinding(prevId);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      onEnterPress();
    }
  };

  return (
    <div
      className="w-full flex flex-col rounded-[4px] border border-[var(--border)] bg-[var(--surface)] divide-y divide-[var(--border)] overflow-hidden text-[13px]"
      aria-label="Findings Outline and Category Filters"
    >
      {/* Category Filter Pills / List */}
      <div className="p-3 bg-[var(--surface-subtle)] space-y-2">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Categories ({findings.length})
        </div>
        <div className="flex flex-wrap gap-1" role="radiogroup" aria-label="Filter by Category">
          <button
            type="button"
            role="radio"
            aria-checked={selectedCategory === 'All'}
            onClick={() => onSelectCategory('All')}
            className={`px-2 py-1 text-[11px] rounded-[3px] font-medium transition-colors focus-ring cursor-pointer ${
              selectedCategory === 'All'
                ? 'bg-[var(--surface)] text-[var(--text-main)] font-semibold border border-[var(--border-strong)]'
                : 'text-[var(--text-secondary)] hover:bg-[var(--surface)] border border-transparent'
            }`}
          >
            All ({categoryCounts.All || 0})
          </button>
          {RISK_CATEGORIES.map((cat) => {
            const count = categoryCounts[cat] || 0;
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => onSelectCategory(cat)}
                className={`px-2 py-1 text-[11px] rounded-[3px] font-medium transition-colors focus-ring cursor-pointer ${
                  isSelected
                    ? 'bg-[var(--surface)] text-[var(--text-main)] font-semibold border border-[var(--border-strong)]'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--surface)] border border-transparent'
                }`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Findings List (The Table of Contents for Review) */}
      <div
        ref={listRef}
        role="listbox"
        aria-label="Findings List"
        className="divide-y divide-[var(--border)] max-h-[580px] overflow-y-auto"
      >
        {displayedFindings.length === 0 ? (
          <div className="p-4 text-center text-xs text-[var(--text-muted)]">
            No findings flagged in {selectedCategory}.
          </div>
        ) : (
          displayedFindings.map((finding, idx) => {
            const fId = finding.findingId || finding.id || `f-${idx + 1}`;
            const isSelected = fId === selectedFindingId;
            const lineNums = finding.lineNumbers || [];
            const locationText = lineNums.length > 0
              ? lineNums.length === 1
                ? `Line ${lineNums[0]}`
                : `Lines ${Math.min(...lineNums)}–${Math.max(...lineNums)}`
              : 'Contract scope';

            return (
              <div
                key={fId}
                role="option"
                tabIndex={0}
                aria-selected={isSelected}
                onClick={() => onSelectFinding(fId)}
                onKeyDown={(e) => handleKeyDown(e, idx)}
                className={`p-3 cursor-pointer transition-colors focus-ring space-y-1.5 ${
                  isSelected
                    ? 'bg-[var(--accent-tint)] border-l-[3px] border-l-[var(--accent)] -ml-[1px]'
                    : 'hover:bg-[var(--surface-subtle)] border-l-[3px] border-l-transparent -ml-[1px]'
                }`}
              >
                {/* Row 1: Severity Tag + Category Text */}
                <div className="flex items-center justify-between gap-2">
                  <SeverityTag severity={finding.severity} size="sm" />
                  <span className="text-[11px] text-[var(--text-secondary)] font-medium truncate">
                    {finding.category}
                  </span>
                </div>

                {/* Row 2: Title */}
                <div className="text-[13px] font-semibold text-[var(--text-main)] leading-snug line-clamp-2">
                  {finding.title || 'Operational Hazard Flag'}
                </div>

                {/* Row 3: Location */}
                <div className="text-[11px] font-mono text-[var(--text-muted)] tnum flex items-center justify-between">
                  <span>{locationText}</span>
                  <span className="text-[10px] uppercase font-bold text-[var(--text-muted)]">
                    F-0{idx + 1}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer count indicator */}
      <div className="p-2.5 bg-[var(--surface-subtle)] text-[11px] text-[var(--text-muted)] font-mono tnum flex items-center justify-between">
        <span>Showing {displayedFindings.length} of {findings.length} findings</span>
        <span>Arrow keys to navigate</span>
      </div>
    </div>
  );
};

export default FindingsOutline;
