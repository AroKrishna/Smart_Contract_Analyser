import Card from '../common/Card';
import { ShieldCheck, Loader2, AlertCircle } from 'lucide-react';

const RiskOverview = ({ distribution = [], loading = false, error = null }) => {
  const hasClauses = distribution && distribution.length > 0 && distribution.some((item) => (item.count || 0) > 0);

  return (
    <Card
      title="Risk Category Breakdown"
      subtitle="Pre-deployment legal risk clause distribution across audited contracts"
      className="border-slate-800/80 bg-slate-900/60"
    >
      {loading ? (
        <div className="py-8 flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
          <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
          <span>Loading category distribution...</span>
        </div>
      ) : error ? (
        <div className="py-6 px-4 rounded-lg bg-red-950/20 border border-red-900/40 text-center space-y-1">
          <AlertCircle className="w-5 h-5 text-red-400 mx-auto mb-1" />
          <p className="text-xs font-medium text-red-300">Unable to load category metrics</p>
          <p className="text-[11px] text-slate-400">{error}</p>
        </div>
      ) : !hasClauses ? (
        <div className="py-8 text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-slate-800/80 border border-slate-700/60 mx-auto flex items-center justify-center text-slate-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-200">No risk clauses recorded</p>
            <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
              Run an audit on a Solidity contract to view your category risk distribution.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {distribution.map((item) => (
            <div key={item.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-200">{item.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 font-mono">{item.count} clauses</span>
                  <span className="font-semibold text-slate-300 font-mono w-8 text-right">
                    {item.percentage}%
                  </span>
                </div>
              </div>

              {/* Custom Bar Indicator */}
              <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/60">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, Math.max(0, item.percentage))}%`,
                    backgroundColor: item.color || '#3b82f6',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
        <span>Model: Legal-BERT Classifier</span>
        <span className="font-mono">5 Primary Taxonomies</span>
      </div>
    </Card>
  );
};

export default RiskOverview;
