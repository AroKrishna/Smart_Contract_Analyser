import Card from '../common/Card';
import SeverityTag from '../common/SeverityTag';

const RiskCard = ({ categories = [] }) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[16px] font-semibold text-[var(--text-main)]">
          5 Primary Legal Risk Categories
        </h3>
        <span className="text-[11px] text-[var(--text-muted)] font-mono">
          Taxonomy breakdown
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {categories.map((cat) => (
          <Card
            key={cat.name}
            className="p-4 flex flex-col justify-between space-y-3"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="text-[14px] font-semibold text-[var(--text-main)]">
                  {cat.name}
                </span>
                <SeverityTag severity={cat.riskLevel || cat.severity} size="sm" />
              </div>

              <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed">
                {cat.summary}
              </p>
            </div>

            <div className="pt-2.5 border-t border-[var(--border)] space-y-1.5 text-[11px] font-mono tnum">
              <div className="flex items-center justify-between text-[var(--text-muted)]">
                <span>Score: {cat.score}/100</span>
                <span>
                  {cat.detectedClauses} {cat.detectedClauses === 1 ? 'clause' : 'clauses'} flagged
                </span>
              </div>

              <div className="h-1.5 w-full bg-[var(--surface-subtle)] rounded-[2px] overflow-hidden border border-[var(--border)]">
                <div
                  className="h-full rounded-[2px] transition-all duration-300"
                  style={{
                    width: `${cat.score}%`,
                    backgroundColor: cat.score >= 75 ? 'var(--critical)' : cat.score >= 50 ? 'var(--high)' : 'var(--low)',
                  }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default RiskCard;
