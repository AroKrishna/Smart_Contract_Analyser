import { useState } from 'react';
import { AlertTriangle, Check, Copy, Info } from 'lucide-react';
import Card from '../common/Card';

const CodeViewer = ({
  code = '',
  highlightedLines: propHighlightedLines,
  findings = [],
}) => {
  const lines = code ? code.split('\n') : [];

  const hasDynamicFindings = Array.isArray(findings) && findings.length > 0;
  const activeHighlightedLines = hasDynamicFindings
    ? findings.flatMap((f) => f.lineNumbers || [])
    : (propHighlightedLines || []);

  const [copied, setCopied] = useState(false);
  const [selectedLine, setSelectedLine] = useState(
    activeHighlightedLines.length > 0 ? activeHighlightedLines[0] : (lines.length > 0 ? 1 : 0)
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLineRisk = (lineNum) => {
    if (hasDynamicFindings) {
      const match = findings.find((f) => (f.lineNumbers || []).includes(lineNum));
      if (!match) return null;

      const badgeClasses = {
        Critical: 'bg-red-500/20 text-red-300 border-red-500/30',
        High: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
        Medium: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        Low: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      };

      return {
        level: match.severity || 'Medium',
        category: match.category,
        clause: match.snippet ? match.snippet.split('\n')[0] : match.title,
        explanation: match.description,
        regulatoryCitation: match.regulatoryCitation,
        badgeClass: badgeClasses[match.severity] || badgeClasses.Medium,
      };
    }

    return null;
  };

  const currentRisk = getLineRisk(selectedLine);

  return (
    <Card
      title="Solidity Source Code & Clause Highlighting"
      subtitle="Interactive code viewer highlighting sections classified by Legal-BERT with severe risk signals"
      action={
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors text-xs font-medium border border-slate-700"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? 'Copied' : 'Copy Source'}
        </button>
      }
      className="border-slate-800 bg-slate-900/60"
      contentClassName="p-0"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
        {/* Code Lines Viewer */}
        <div className="lg:col-span-8 bg-slate-950/80 font-mono text-xs overflow-x-auto max-h-[500px] overflow-y-auto">
          <div className="min-w-[500px]">
            {lines.map((lineText, idx) => {
              const lineNum = idx + 1;
              const isHighlighted = activeHighlightedLines.includes(lineNum);
              const isSelected = selectedLine === lineNum;
              const riskInfo = getLineRisk(lineNum);

              return (
                <div
                  key={lineNum}
                  onClick={() => riskInfo && setSelectedLine(lineNum)}
                  className={`flex items-center group transition-colors ${
                    isSelected
                      ? 'bg-blue-600/15 border-l-2 border-blue-500'
                      : isHighlighted
                      ? 'bg-red-500/10 hover:bg-red-500/15 border-l-2 border-red-500/80 cursor-pointer'
                      : 'hover:bg-slate-900/60 border-l-2 border-transparent'
                  }`}
                >
                  {/* Line Number */}
                  <span className="w-12 py-1 px-3 select-none text-right text-slate-400 shrink-0 text-[11px]">
                    {lineNum}
                  </span>

                  {/* Flag indicator if risk detected */}
                  <span className="w-5 text-center shrink-0">
                    {riskInfo && (
                      <AlertTriangle
                        className={`w-3.5 h-3.5 inline ${
                          riskInfo.level === 'Critical'
                            ? 'text-red-400'
                            : 'text-amber-400'
                        }`}
                      />
                    )}
                  </span>

                  {/* Code Line Content */}
                  <span
                    className={`py-1 pr-4 whitespace-pre flex-1 ${
                      isHighlighted
                        ? 'text-red-200 font-medium'
                        : 'text-slate-300'
                    }`}
                  >
                    {lineText || ' '}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Clause Risk Inspector */}
        <div className="lg:col-span-4 p-5 bg-slate-900/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Clause Inspector
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Line {selectedLine}
              </span>
            </div>

            {currentRisk ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">
                    {currentRisk.category}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${currentRisk.badgeClass}`}
                  >
                    {currentRisk.level} Risk
                  </span>
                </div>

                <div className="p-2.5 rounded bg-slate-950 font-mono text-xs text-red-300 border border-slate-800">
                  {currentRisk.clause}
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                  {currentRisk.explanation}
                </p>

                {currentRisk.regulatoryCitation && (
                  <div className="text-[10px] text-slate-400 font-mono bg-slate-950/40 p-2 rounded border border-slate-800/80">
                    <span className="text-slate-500 uppercase tracking-wider text-[9px] block mb-0.5">Citation Benchmark:</span>
                    {currentRisk.regulatoryCitation}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 text-center text-xs text-slate-500">
                <Info className="w-4 h-4 mx-auto mb-1.5 text-slate-400" />
                Select any highlighted line to inspect detected legal risks.
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
            Click on flagged lines in the code viewer to isolate SHAP token influences.
          </div>
        </div>
      </div>
    </Card>
  );
};

export default CodeViewer;
