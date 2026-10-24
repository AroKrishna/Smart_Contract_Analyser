import Card from '../common/Card';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

const ComplianceMatrix = ({ matrix = [] }) => {
  return (
    <Card
      title="Compliance considerations matrix"
      subtitle="Potential compliance assessment mapping based on statutory consumer and privacy standards"
      contentClassName="p-0 overflow-x-auto"
    >
      <table className="w-full text-left border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-muted)] font-mono">
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Regulatory Domain
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Assessment
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Audit Notes & Observations
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border)]">
          {matrix.map((row, idx) => {
            const isWarning = row.status === 'Warning';
            const isPass = row.status === 'Pass';

            return (
              <tr key={idx} className="hover:bg-[var(--surface-subtle)] transition-colors">
                <td className="py-3 px-4 font-medium text-[var(--text-main)] whitespace-nowrap">
                  {row.area}
                </td>

                <td className="py-3 px-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[3px] text-[11px] font-semibold border ${
                      isWarning
                        ? 'bg-[var(--high-tint)] text-[var(--high)] border-[var(--high)]'
                        : isPass
                        ? 'bg-[var(--low-tint)] text-[var(--low)] border-[var(--low)]'
                        : 'bg-[var(--surface-subtle)] text-[var(--text-secondary)] border-[var(--border)]'
                    }`}
                  >
                    {isWarning ? (
                      <AlertTriangle className="w-3 h-3 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-3 h-3 shrink-0" />
                    )}
                    {row.assessment}
                  </span>
                </td>

                <td className="py-3 px-4 text-[var(--text-secondary)] leading-relaxed max-w-md">
                  {row.note}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Mandatory Non-Guarantee Disclaimer */}
      <div className="p-3 bg-[var(--surface-subtle)] border-t border-[var(--border)] flex items-start gap-2.5 text-[11px] text-[var(--text-muted)]">
        <AlertCircle className="w-4 h-4 text-[var(--text-secondary)] shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          Statutory Notice: This assessment evaluates potential compliance risks based on automated heuristics and Legal-BERT clause classification. It does not provide legal opinions, guarantee regulatory compliance under any jurisdiction, or replace official legal certification.
        </p>
      </div>
    </Card>
  );
};

export default ComplianceMatrix;
