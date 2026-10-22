import { Lock, Ban, FileCheck2, Scale, CreditCard } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';

const CATEGORY_ICONS = {
  Privacy: Lock,
  Termination: Ban,
  'Legal Compliance': FileCheck2,
  Liability: Scale,
  'Payment / Financial': CreditCard,
};

const RiskCard = ({ categories = [] }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-100">
          5 Primary Legal Risk Categories
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          Taxonomy breakdown
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((cat) => {
          const Icon = CATEGORY_ICONS[cat.name] || FileCheck2;

          return (
            <Card
              key={cat.name}
              className="border-slate-800/80 bg-slate-900/60 p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-semibold text-slate-200">
                      {cat.name}
                    </span>
                  </div>
                  <Badge riskLevel={cat.riskLevel} size="sm" dot />
                </div>

                <p className="text-xs text-slate-400 leading-relaxed min-h-[3rem] mb-4">
                  {cat.summary}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 space-y-2">
                <div className="flex flex-col gap-1 text-xs font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Score: {cat.score}/100</span>
                    <span className="text-slate-300">
                      {cat.detectedClauses} {cat.detectedClauses === 1 ? 'clause' : 'clauses'} flagged
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-amber-400/80 font-mono">Uncalibrated Sigmoid</span>
                    {cat.supportStatus === 'inconclusive_zero_positive_support' ? (
                      <span className="text-slate-500 font-mono">Zero Test Positives</span>
                    ) : (
                      <span className="text-slate-400 font-mono">Threshold: 0.50</span>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      cat.score >= 75
                        ? 'bg-red-500'
                        : cat.score >= 50
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${cat.score}%` }}
                  />
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default RiskCard;
