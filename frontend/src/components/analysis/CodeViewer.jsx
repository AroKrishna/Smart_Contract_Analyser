import { useState, useRef, useEffect } from 'react';
import { Copy, Check } from 'lucide-react';
import { getSeverityConfig, normalizeSeverity } from '../../utils/severity';

const CodeViewer = ({
  code = '',
  findings = [],
  selectedFindingId = null,
  onSelectFinding = () => {},
  filename = 'Contract.sol',
}) => {
  const [copied, setCopied] = useState(false);
  const codeContainerRef = useRef(null);
  const lineRefs = useRef(new Map());

  const lines = code ? code.split('\n') : [];
  const linesCount = lines.length;

  // Build a map of line number -> list of findings that touch this line
  const lineFindingsMap = new Map();
  findings.forEach((finding, fIdx) => {
    const fId = finding.findingId || finding.id || `f-${fIdx + 1}`;
    const nums = finding.lineNumbers || [];
    nums.forEach((lineNum) => {
      if (!lineFindingsMap.has(lineNum)) {
        lineFindingsMap.set(lineNum, []);
      }
      lineFindingsMap.get(lineNum).push({ ...finding, computedId: fId, index: fIdx + 1 });
    });
  });

  // Find the selected finding and its line numbers
  const selectedFinding = findings.find(
    (f, idx) => (f.findingId || f.id || `f-${idx + 1}`) === selectedFindingId
  ) || findings[0];

  const selectedLineNumbers = selectedFinding?.lineNumbers || [];

  // Scroll to selected finding's first line when selectedFindingId changes
  useEffect(() => {
    if (selectedFindingId && selectedLineNumbers.length > 0) {
      const firstLine = Math.min(...selectedLineNumbers);
      const el = lineRefs.current.get(firstLine);
      if (el && codeContainerRef.current) {
        // Smooth scroll within container
        const container = codeContainerRef.current;
        const topPos = el.offsetTop - container.offsetTop - 40;
        container.scrollTo({ top: Math.max(0, topPos), behavior: 'smooth' });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedFindingId]);

  const handleCopyCode = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Determine highest severity on a line for gutter marker
  const getLineGutterInfo = (lineNum) => {
    const lineFindings = lineFindingsMap.get(lineNum);
    if (!lineFindings || lineFindings.length === 0) return null;

    const severityPriority = { Critical: 4, High: 3, Medium: 2, Low: 1 };
    let highest = lineFindings[0];
    let maxPrio = severityPriority[normalizeSeverity(highest.severity)] || 1;

    for (let i = 1; i < lineFindings.length; i++) {
      const cur = lineFindings[i];
      const prio = severityPriority[normalizeSeverity(cur.severity)] || 1;
      if (prio > maxPrio) {
        highest = cur;
        maxPrio = prio;
      }
    }

    return {
      highestFinding: highest,
      count: lineFindings.length,
      config: getSeverityConfig(highest.severity),
      allFindings: lineFindings,
    };
  };

  return (
    <div
      className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] flex flex-col overflow-hidden text-[13px]"
      aria-label={`Solidity source: ${filename}`}
    >
      {/* Header Row: Filename, line count, copy button */}
      <div className="flex items-center justify-between px-3.5 py-2 border-b border-[var(--border)] bg-[var(--surface-subtle)] select-none">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[12px] font-semibold text-[var(--text-main)]">
            {filename}
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono tnum">
            {linesCount} {linesCount === 1 ? 'line' : 'lines'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyCode}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-[3px] border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] focus-ring transition-colors cursor-pointer"
            aria-label="Copy source code to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-[var(--low)]" />
                <span className="text-[var(--low)] font-medium">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Viewer Body */}
      <div
        ref={codeContainerRef}
        tabIndex={0}
        aria-label={`Code content for ${filename}. Use arrow keys to scroll.`}
        className="overflow-x-auto overflow-y-auto max-h-[620px] bg-[var(--code-bg)] font-mono text-[13px] leading-[20px] focus-ring"
      >
        <div className="min-w-fit w-full">
          {lines.map((lineContent, idx) => {
            const lineNum = idx + 1;
            const gutterInfo = getLineGutterInfo(lineNum);
            const isSelectedRange = selectedLineNumbers.includes(lineNum);
            const isFirstSelectedLine = selectedLineNumbers[0] === lineNum;
            const isLastSelectedLine = selectedLineNumbers[selectedLineNumbers.length - 1] === lineNum;

            // Highlight styling as specified in design guide section 2 and 6:
            // Full width severity tint, severity left edge (3px for Critical/High, 2px Medium, 1px Low),
            // and underline pattern (solid 2px for Critical, dashed for High, dotted for Medium).
            let rowStyle = {};
            let leftEdgeClass = 'border-l-[3px] border-transparent';
            let underlineClass = '';

            if (gutterInfo) {
              const cfg = gutterInfo.config;
              rowStyle.backgroundColor = cfg.tintVar;
              leftEdgeClass = cfg.edgeClass;
              rowStyle.borderLeftColor = cfg.cssVar;
              underlineClass = cfg.underlineClass;
            }

            // Outline for active selected finding
            const selectedOutlineClass = isSelectedRange
              ? `bg-[var(--accent-tint)]/40 ${isFirstSelectedLine ? 'border-t border-t-[var(--accent)]' : ''} ${isLastSelectedLine ? 'border-b border-b-[var(--accent)]' : ''}`
              : '';

            return (
              <div
                key={lineNum}
                ref={(el) => {
                  if (el) lineRefs.current.set(lineNum, el);
                  else lineRefs.current.delete(lineNum);
                }}
                className={`flex items-stretch hover:bg-[var(--surface-subtle)]/70 transition-colors ${leftEdgeClass} ${selectedOutlineClass}`}
                style={rowStyle}
              >
                {/* Gutter: 56px wide, surface subtle background, 1px right rule */}
                <div className="w-[56px] shrink-0 bg-[var(--code-gutter)] border-r border-[var(--border)] flex items-center justify-between px-2 select-none">
                  {/* Line Number: 12px mono, muted text, right-aligned, non-selectable */}
                  <span className="text-[12px] text-[var(--text-muted)] font-mono tnum text-right w-6">
                    {lineNum}
                  </span>

                  {/* Finding marker shape button in gutter */}
                  <div className="w-4 flex items-center justify-center">
                    {gutterInfo && (
                      <button
                        type="button"
                        onClick={() => {
                          const targetId = gutterInfo.highestFinding.computedId;
                          onSelectFinding(targetId);
                        }}
                        title={`Finding: ${gutterInfo.highestFinding.title} (${gutterInfo.highestFinding.severity})`}
                        aria-label={`Finding at line ${lineNum}: ${gutterInfo.highestFinding.severity} severity, activate to select finding`}
                        className="p-0.5 text-[11px] leading-none focus-ring rounded-[2px] cursor-pointer hover:scale-125 transition-transform"
                        style={{ color: gutterInfo.config.cssVar }}
                      >
                        {gutterInfo.config.shape}
                        {gutterInfo.count > 1 && (
                          <span className="text-[9px] font-bold ml-0.5 font-mono">
                            {gutterInfo.count}
                          </span>
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Code line content: non-wrapping whitespace-pre */}
                <div
                  onClick={() => {
                    if (gutterInfo) {
                      onSelectFinding(gutterInfo.highestFinding.computedId);
                    }
                  }}
                  className={`px-3 py-[2px] whitespace-pre text-[var(--text-main)] font-mono flex-1 select-text ${
                    gutterInfo ? 'cursor-pointer' : ''
                  } ${underlineClass}`}
                  style={
                    gutterInfo
                      ? {
                          textDecorationColor: gutterInfo.config.cssVar,
                        }
                      : undefined
                  }
                >
                  {lineContent || ' '}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer bar with finding jump shortcut notice */}
      <div className="px-3.5 py-1.5 border-t border-[var(--border)] bg-[var(--surface-subtle)] flex items-center justify-between text-[11px] text-[var(--text-muted)] select-none">
        <span>Click flagged gutter markers or highlighted lines to inspect details</span>
        <span className="font-mono hidden sm:inline">IBM Plex Mono</span>
      </div>
    </div>
  );
};

export default CodeViewer;
