import Card from '../common/Card';
import SeverityTag from '../common/SeverityTag';
import { Lightbulb, Shield } from 'lucide-react';

const RecommendationCard = ({ recommendations = [] }) => {
  return (
    <Card
      title="Actionable remediation guidance"
      subtitle="Suggested code refactorings and safer alternatives to resolve identified legal risks"
    >
      <div className="space-y-3 text-[13px]">
        {recommendations.length === 0 ? (
          <div className="p-4 text-center text-xs text-[var(--text-muted)] border border-[var(--border)] rounded-[4px]">
            No specific code refactorings flagged for this contract.
          </div>
        ) : (
          recommendations.map((rec, idx) => {
            const recKey = rec.id || rec.findingId || `rec-${idx}`;
            const recTitle = rec.title || 'Recommended Operational Adjustment';
            const recCat = rec.category || 'General';
            const recRisk = rec.riskLevel || rec.severity || 'Medium';
            const recClause = rec.clause || (rec.beforeCode ? rec.beforeCode.split('\n')[0] : recTitle);
            const recSuggestion = rec.suggestion || rec.rationale || rec.afterCode || 'Follow safe smart contract architectural patterns.';

            return (
              <div
                key={recKey}
                className="p-3.5 rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-2.5"
              >
                {/* Header info */}
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-[var(--accent)] shrink-0" />
                    <h4 className="text-[14px] font-semibold text-[var(--text-main)]">
                      {recTitle}
                    </h4>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-[var(--text-muted)] uppercase">
                      {recCat}
                    </span>
                    <SeverityTag severity={recRisk} size="sm" />
                  </div>
                </div>

                {/* Flagged Clause */}
                {recClause && (
                  <div className="p-2 rounded-[3px] bg-[var(--code-bg)] border border-[var(--border)] font-mono text-[12px] text-[var(--text-secondary)]">
                    <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block mb-0.5">
                      Flagged Pattern:
                    </span>
                    <code>{recClause}</code>
                  </div>
                )}

                {/* Safer Alternative */}
                <div className="space-y-1 text-[13px] text-[var(--text-secondary)] leading-relaxed">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-[var(--low)]" />
                    Recommended Implementation:
                  </span>
                  <p className="pl-5 text-[var(--text-secondary)]">
                    {recSuggestion}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
};

export default RecommendationCard;
