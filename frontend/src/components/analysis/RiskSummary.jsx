import Card from '../common/Card';
import SeverityTag from '../common/SeverityTag';
import { getSeverityConfig } from '../../utils/severity';

const RiskSummary = ({ contract }) => {
  if (!contract) return null;

  const {
    name,
    contractType,
    auditDate,
    overallRiskScore,
    overallRiskLevel,
    confidence,
    summary,
  } = contract;

  const sevConfig = getSeverityConfig(overallRiskLevel);

  return (
    <Card className="p-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left: Score Numeral */}
        <div className="lg:col-span-4 flex flex-col items-center justify-center p-6 bg-[var(--surface-subtle)] rounded-[4px] border border-[var(--border)] text-center">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
            Overall Legal-Risk Score
          </span>

          <div className="text-[40px] leading-[44px] font-bold text-[var(--text-main)] font-mono tnum my-2">
            {overallRiskScore}
            <span className="text-[14px] text-[var(--text-muted)] font-normal ml-1">/100</span>
          </div>

          <div className="mt-2 flex flex-col items-center gap-1">
            <SeverityTag severity={overallRiskLevel} size="default" />
            {confidence && (
              <span className="text-[11px] text-[var(--text-muted)] font-mono text-center mt-1">
                Score Activation: <span className="text-[var(--text-main)] font-semibold">{confidence}</span>
              </span>
            )}
          </div>
        </div>

        {/* Right: Contract Context & Executive Summary */}
        <div className="lg:col-span-8 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
            <div>
              <h3 className="text-[16px] font-bold text-[var(--text-main)] font-mono">{name}</h3>
              <p className="text-[12px] text-[var(--text-muted)]">
                {contractType} • Audited on <span className="font-mono text-[var(--text-secondary)]">{auditDate}</span>
              </p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded-[3px] bg-[var(--surface-subtle)] border border-[var(--border)] text-[var(--text-muted)] font-mono">
              Legal-BERT v3.3.0
            </span>
          </div>

          <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed bg-[var(--surface-subtle)] p-3 rounded-[4px] border border-[var(--border)]">
            {summary}
          </p>

          <div className="text-[11px] text-[var(--text-muted)] leading-relaxed pt-1">
            Pre-deployment decision-support triage. Absence of findings is not proof of contract safety.
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RiskSummary;
