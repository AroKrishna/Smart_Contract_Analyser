import Card from '../common/Card';
import { mockRiskCategoryDistribution } from '../../data/mockData';

const RiskOverview = () => {
  return (
    <Card
      title="Risk category distribution"
      subtitle="Relative distribution of detected clauses across standard categories"
    >
      <div className="space-y-3.5 text-[13px]">
        {mockRiskCategoryDistribution.map((item) => (
          <div key={item.name} className="space-y-1">
            <div className="flex items-center justify-between text-[12px]">
              <span className="font-medium text-[var(--text-main)]">{item.name}</span>
              <div className="flex items-center gap-2 font-mono tnum text-[11px]">
                <span className="text-[var(--text-muted)]">{item.count} clauses</span>
                <span className="font-semibold text-[var(--text-secondary)] w-8 text-right">
                  {item.percentage}%
                </span>
              </div>
            </div>

            <div className="h-1.5 w-full bg-[var(--surface-subtle)] rounded-[2px] overflow-hidden border border-[var(--border)]">
              <div
                className="h-full rounded-[2px] transition-all duration-300"
                style={{
                  width: `${item.percentage}%`,
                  backgroundColor: 'var(--accent)',
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--text-muted)]">
        <span>Engine: Legal-BERT v3.3.0</span>
        <span className="font-mono">5 Categories</span>
      </div>
    </Card>
  );
};

export default RiskOverview;
