import { ChevronLeft, ChevronRight, MapPin, Lightbulb } from 'lucide-react';
import SeverityTag from '../common/SeverityTag';
import Button from '../common/Button';

const FindingDetailPanel = ({
  finding = null,
  totalFindings = 1,
  currentIndex = 0,
  onPrevious = () => {},
  onNext = () => {},
  onJumpToLines = () => {},
  titleRef = null,
}) => {
  if (!finding) {
    return (
      <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] p-6 text-center text-xs text-[var(--text-muted)]">
        No finding selected. Select a finding from the list or code viewer.
      </div>
    );
  }

  const lineNums = finding.lineNumbers || [];
  const locationText = lineNums.length > 0
    ? lineNums.length === 1
      ? `Line ${lineNums[0]}`
      : `Lines ${Math.min(...lineNums)} to ${Math.max(...lineNums)}`
    : 'Contract scope';

  const displayId = `F-0${currentIndex + 1}`;

  return (
    <aside
      className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] flex flex-col overflow-hidden text-[13px]"
      aria-label="Finding detail and evidence panel"
    >
      {/* Navigation Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--surface-subtle)] select-none">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[12px] font-bold text-[var(--text-main)]">
            {displayId}
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono tnum">
            ({currentIndex + 1} of {totalFindings})
          </span>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="secondary"
            size="sm"
            onClick={onPrevious}
            disabled={currentIndex <= 0}
            aria-label="Previous finding"
            className="h-[24px] px-2 text-xs"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={onNext}
            disabled={currentIndex >= totalFindings - 1}
            aria-label="Next finding"
            className="h-[24px] px-2 text-xs"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Detail Content (Scrollable) */}
      <div className="p-4 space-y-4 overflow-y-auto max-h-[620px]">
        {/* 1. Severity Tag + Category */}
        <div className="flex items-center justify-between gap-2">
          <SeverityTag severity={finding.severity} size="default" />
          <span className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
            {finding.category}
          </span>
        </div>

        {/* 2. Title */}
        <h3
          ref={titleRef}
          tabIndex={-1}
          className="text-[15px] font-semibold text-[var(--text-main)] leading-snug outline-none"
        >
          {finding.title || 'Operational Hazard Flag'}
        </h3>

        {/* 3. Location link */}
        <div className="flex items-center gap-2 text-[12px] font-mono text-[var(--text-secondary)]">
          <MapPin className="w-3.5 h-3.5 text-[var(--accent)] shrink-0" />
          <button
            type="button"
            onClick={() => onJumpToLines(lineNums)}
            className="text-[var(--accent)] hover:underline font-semibold focus-ring rounded-[2px] cursor-pointer"
            aria-label={`Scroll to ${locationText} in code viewer`}
          >
            {locationText}
          </button>
        </div>

        {/* 4. Evidence Code Snippet */}
        {finding.snippet && (
          <div className="space-y-1.5">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Flagged Code Evidence
            </div>
            <div className="rounded-[4px] border border-[var(--border)] bg-[var(--code-bg)] p-2.5 font-mono text-[12px] overflow-x-auto text-[var(--text-main)] leading-relaxed">
              <pre className="whitespace-pre">{finding.snippet}</pre>
            </div>
          </div>
        )}

        {/* 5. Explanation */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Risk Explanation
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
            {finding.description || finding.explanation || 'Operational hazard evaluated by Legal-BERT classification semantics.'}
          </p>
        </div>

        {/* 6. Model Explanation / Probability attribution */}
        {(finding.confidence || finding.probability || finding.evidenceDescription) && (
          <div className="p-3 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1.5 text-[12px]">
            <div className="font-semibold text-[var(--text-main)] text-[11px] uppercase tracking-wider">
              Legal-BERT Model Inference
            </div>
            {finding.confidence && (
              <div className="flex items-center justify-between text-[11px] text-[var(--text-secondary)] font-mono">
                <span>Model score:</span>
                <span className="font-semibold text-[var(--text-main)] tnum">{finding.confidence}</span>
              </div>
            )}
            {finding.threshold && (
              <div className="flex items-center justify-between text-[11px] text-[var(--text-secondary)] font-mono">
                <span>Threshold:</span>
                <span className="tnum">{finding.threshold} uncalibrated</span>
              </div>
            )}
            {finding.evidenceDescription && (
              <div className="text-[11px] text-[var(--text-muted)] pt-1 border-t border-[var(--border)]">
                {finding.evidenceDescription}
              </div>
            )}
          </div>
        )}

        {/* 7. Actionable Remediation Guidance */}
        {(finding.suggestion || finding.recommendation) && (
          <div className="space-y-1.5 pt-2 border-t border-[var(--border)]">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-main)]">
              <Lightbulb className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span>Remediation Guidance</span>
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed bg-[var(--surface-subtle)] p-3 rounded-[4px] border border-[var(--border)]">
              {typeof finding.suggestion === 'string'
                ? finding.suggestion
                : typeof finding.recommendation === 'string'
                ? finding.recommendation
                : finding.recommendation?.suggestion || 'Follow safe smart contract architectural patterns.'}
            </p>
          </div>
        )}

        {/* 8. Statutory Disclaimer Note */}
        <div className="pt-2 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] leading-relaxed">
          Explanations describe model behavior; they are not a verified vulnerability.
        </div>
      </div>
    </aside>
  );
};

export default FindingDetailPanel;
