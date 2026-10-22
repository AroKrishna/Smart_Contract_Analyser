import Card from '../common/Card';
import { ArrowUpRight, ArrowDownRight, Layers } from 'lucide-react';

const ShapChart = ({ explanations = [] }) => {
  const maxVal = Math.max(
    ...explanations.map((e) => Math.abs(e.contribution ?? e.value ?? 0.001)),
    0.01
  );

  return (
    <Card
      title="SHAP Feature Attribution (Shapley Values)"
      subtitle="Game-theoretic Shapley Additive exPlanations (shap.Explainer) measuring token marginal risk contributions"
      className="border-slate-800 bg-slate-900/60"
    >
      <div className="space-y-4">
        <p className="text-xs text-slate-400 leading-relaxed">
          Tokens with <span className="text-orange-400 font-semibold">positive Shapley value (+)</span> pushed Legal-BERT toward a higher predicted hazard in the primary category. Tokens with <span className="text-emerald-400 font-semibold">negative Shapley value (-)</span> reduced the predicted hazard.
        </p>

        <div className="space-y-3 pt-2">
          {explanations.length === 0 ? (
            <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-500">
              No significant SHAP token attributions computed for this contract scope.
            </div>
          ) : (
            explanations.map((item, idx) => {
              const tokenName = item.token || item.feature || 'Token';
              const categoryName = item.category || 'Primary Category';
              const rawVal = item.contribution ?? item.value ?? 0;
              const absVal = Math.abs(rawVal);
              const isPositive = item.impact ? item.impact === 'positive' : rawVal >= 0;
              const barWidthPercent = Math.min(100, Math.max(12, Math.round((absVal / maxVal) * 100)));

              return (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-200">
                        {tokenName}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        [{categoryName}]
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 font-mono text-xs">
                      {isPositive ? (
                        <span className="flex items-center gap-1 text-orange-400 font-semibold">
                          <ArrowUpRight className="w-3.5 h-3.5" />
                          +{absVal.toFixed(4)} (Hazard Driver)
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                          <ArrowDownRight className="w-3.5 h-3.5" />
                          -{absVal.toFixed(4)} (Mitigating)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Contribution Bar */}
                  <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden flex">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isPositive ? 'bg-orange-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${barWidthPercent}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 font-mono">
            <Layers className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            Method: Genuine SHAP (shap.Explainer Partition/Permutation)
          </span>
          <span className="text-slate-500 text-[10px]">
            Target: Top Predicted Risk Head
          </span>
        </div>
      </div>
    </Card>
  );
};

export default ShapChart;
