import Card from '../common/Card';
import { Sparkles, Code2 } from 'lucide-react';

const LimeExplanation = ({ explanations = [] }) => {
  return (
    <Card
      title="LIME Local Interpretability (Linear Surrogate)"
      subtitle="Local Interpretable Model-agnostic Explanations (LimeTextExplainer) via token perturbation regression"
      className="border-slate-800 bg-slate-900/60"
    >
      <div className="space-y-4">
        <p className="text-xs text-slate-400 leading-relaxed">
          LIME generates local perturbations around the submitted contract representation to fit an interpretable sparse linear surrogate model, isolating individual token weights.
        </p>

        <div className="space-y-4 pt-1">
          {explanations.length === 0 ? (
            <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-500">
              No LIME surrogate weights computed for this contract scope.
            </div>
          ) : (
            explanations.map((item, idx) => {
              const codeSnippet = item.token ? `token: "${item.token}"` : (item.code || item.snippet || item.clause || 'Clause construct');
              const surrogateText = item.explanation || item.description || 'LIME local surrogate linear weight identifying marginal model activation.';
              const rawWeight = item.weight ?? item.score ?? 0;
              const weightVal = typeof rawWeight === 'number' ? rawWeight.toFixed(4) : String(rawWeight);
              const isRisk = item.type === 'risk' || rawWeight > 0;

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`p-1 rounded border ${isRisk ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
                        <Code2 className="w-3.5 h-3.5" />
                      </span>
                      <span className="text-xs font-mono font-semibold text-slate-300">
                        {isRisk ? 'Hazard Weight (+)' : 'Mitigating Weight (-)'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs font-mono">
                      <span className="text-slate-400">LIME Surrogate Weight:</span>
                      <span className={`font-semibold ${isRisk ? 'text-orange-400' : 'text-emerald-400'}`}>
                        {rawWeight > 0 ? `+${weightVal}` : weightVal}
                      </span>
                    </div>
                  </div>

                  {/* Monospace Code Preview */}
                  <div className="p-2.5 rounded-lg bg-slate-900 font-mono text-xs text-purple-300 border border-purple-900/40">
                    {codeSnippet}
                  </div>

                  {/* Interpretation */}
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/30 p-2.5 rounded border border-slate-800/60">
                    {surrogateText}
                  </p>
                </div>
              );
            })
          )}
        </div>

        <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 font-mono">
            <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            Method: Genuine LIME (LimeTextExplainer Local Linear Surrogate)
          </span>
          <span className="text-slate-500 text-[10px]">
            Sampling: Local Text Perturbations
          </span>
        </div>
      </div>
    </Card>
  );
};

export default LimeExplanation;
