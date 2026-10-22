import { ShieldAlert, Activity, FileCode } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';

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

  return (
    <Card className="border-slate-800 bg-slate-900/80 p-6 shadow-xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left: Overall Score Dial */}
        <div className="lg:col-span-4 flex flex-col items-center justify-center p-6 bg-slate-950/60 rounded-xl border border-slate-800/80 text-center">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Overall Legal-Risk Score
          </span>

          <div className="relative flex items-center justify-center my-3">
            <div className="w-32 h-32 rounded-full border-4 border-slate-800 flex flex-col items-center justify-center bg-slate-900/60 shadow-inner">
              <span className="text-4xl font-extrabold text-slate-100 font-mono tracking-tight">
                {overallRiskScore}
              </span>
              <span className="text-[11px] text-slate-500 font-mono">/ 100</span>
            </div>
          </div>

          <div className="mt-2 flex flex-col items-center gap-1">
            <Badge riskLevel={overallRiskLevel} size="lg" dot />
            <span className="text-[11px] text-slate-400 font-mono text-center">
              Score Activation: <span className="text-slate-200 font-semibold">{confidence}</span>
            </span>
            <span className="text-[10px] text-amber-400/80 font-mono">
              (Uncalibrated Sigmoid — Not Probability)
            </span>
          </div>
        </div>

        {/* Right: Contract Context & Executive Summary */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
                <FileCode className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100">{name}</h3>
                <p className="text-xs text-slate-400">
                  {contractType} • Audited on <span className="font-mono text-slate-300">{auditDate}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                Legal-BERT v1.2
              </span>
            </div>
          </div>

          {/* Executive Summary */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              Executive Audit Summary
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-lg border border-slate-800/60">
              {summary}
            </p>
          </div>

          {/* Advisory Notice */}
          <div className="flex items-start gap-2.5 text-xs text-slate-400 bg-blue-950/20 border border-blue-900/40 p-3 rounded-lg">
            <ShieldAlert className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <strong className="text-slate-300">Decision-Support Scope:</strong> This automated audit identifies risk correlations based on trained legal semantics and token contributions. It is intended to assist pre-deployment review, not certify absolute compliance.
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default RiskSummary;
