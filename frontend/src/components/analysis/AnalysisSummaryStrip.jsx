import { Download, FileText, Share2, Trash2 } from 'lucide-react';
import SeverityTag from '../common/SeverityTag';
import Button from '../common/Button';
import { RISK_CATEGORIES } from '../../utils/constants';

const AnalysisSummaryStrip = ({
  contractName = 'Contract.sol',
  analysisId = '',
  overallRiskScore = 0,
  overallRiskLevel = 'Low',
  summary = '',
  findings = [],
  onExport = () => {},
  onShare = () => {},
  onDiscard = () => {},
  exportingPdf = false,
  exportingDocx = false,
  discarding = false,
}) => {

  // Compute findings count per category
  const categoryCounts = {};
  RISK_CATEGORIES.forEach((cat) => {
    categoryCounts[cat] = findings.filter((f) => f.category === cat).length;
  });

  return (
    <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface)] text-[var(--text-main)] overflow-hidden">
      {/* Top Header Row with File Name & Utility Actions */}
      <div className="px-4 py-3 border-b border-[var(--border)] bg-[var(--surface-subtle)] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[14px] font-semibold text-[var(--text-main)]">
            {contractName}
          </span>
          <span className="text-[11px] font-mono text-[var(--text-muted)] hidden sm:inline">
            ID: {analysisId}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={Download}
            isLoading={exportingPdf}
            onClick={() => onExport('PDF')}
          >
            Export PDF
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={FileText}
            isLoading={exportingDocx}
            onClick={() => onExport('DOCX')}
          >
            Export DOCX
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={Share2}
            onClick={onShare}
          >
            Share
          </Button>

          <Button
            variant="destructive"
            size="sm"
            icon={Trash2}
            isLoading={discarding}
            onClick={onDiscard}
          >
            Discard
          </Button>
        </div>
      </div>

      {/* Main Strip Body: Score Numeral + Level + Summary + Counts Table */}
      <div className="p-4 sm:p-5 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Score Numeral & Risk Level */}
        <div className="lg:col-span-3 flex items-center gap-4 border-b lg:border-b-0 lg:border-r border-[var(--border)] pb-4 lg:pb-0 lg:pr-6">
          <div className="text-[40px] leading-[44px] font-bold font-mono tracking-tight tnum text-[var(--text-main)]">
            {overallRiskScore}
            <span className="text-[14px] text-[var(--text-muted)] font-normal ml-1">/100</span>
          </div>

          <div className="space-y-1">
            <SeverityTag severity={overallRiskLevel} size="lg" />
            <div className="text-[11px] text-[var(--text-muted)] font-mono">
              Overall risk score
            </div>
          </div>
        </div>

        {/* One-Sentence Summary */}
        <div className="lg:col-span-5 space-y-1 border-b lg:border-b-0 lg:border-r border-[var(--border)] pb-4 lg:pb-0 lg:pr-6">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Operational Risk Assessment
          </div>
          <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
            {summary || 'Legal-BERT multi-label operational hazard classification evaluating contractual and architectural risks.'}
          </p>
        </div>

        {/* Category Count Table */}
        <div className="lg:col-span-4 space-y-1">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Category Breakdown
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1 text-[12px] font-mono tnum">
            {RISK_CATEGORIES.map((cat) => {
              const count = categoryCounts[cat] || 0;
              return (
                <div key={cat} className="flex items-center justify-between py-0.5">
                  <span className="text-[var(--text-muted)] truncate mr-2" title={cat}>
                    {cat}:
                  </span>
                  <span className={`font-semibold ${count > 0 ? 'text-[var(--text-main)]' : 'text-[var(--text-muted)]'}`}>
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisSummaryStrip;
