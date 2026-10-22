import { CheckCircle2, Loader2, Cpu, ShieldCheck } from 'lucide-react';
import Card from '../common/Card';
import { PIPELINE_STAGES } from '../../utils/constants';

const AnalysisProgress = ({
  currentStepIndex = 0,
  contractName = 'Contract.sol',
  progressPercent: explicitProgress,
  stageMessage = '',
  stageName = '',
}) => {
  const progressPercent = typeof explicitProgress === 'number'
    ? explicitProgress
    : Math.min(100, Math.round(((currentStepIndex + 1) / PIPELINE_STAGES.length) * 100));

  return (
    <div className="max-w-2xl mx-auto py-8">
      <Card className="border-slate-800 bg-slate-900/90 shadow-2xl p-6 sm:p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/30 text-blue-400 mb-3 animate-pulse">
            <Cpu className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-100">
            Running Legal-BERT & XAI Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Analyzing <span className="font-mono text-slate-300 font-semibold">{contractName}</span> for potential pre-deployment legal risks
          </p>

          {/* Real Backend Status Banner */}
          {stageMessage && (
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-950/60 border border-blue-500/30 text-blue-300 text-xs font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 shrink-0" />
              <span>{stageMessage}</span>
            </div>
          )}

          {/* Progress Bar */}
          <div className="mt-5 space-y-1.5">
            <div className="flex justify-between text-xs text-slate-400">
              <span>{stageName || `Pipeline Stage ${currentStepIndex + 1} of ${PIPELINE_STAGES.length}`}</span>
              <span className="font-mono text-blue-400 font-semibold">{progressPercent}%</span>
            </div>
            <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* 8-Stage Tracker */}
        <div className="space-y-3">
          {PIPELINE_STAGES.map((stage, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;

            return (
              <div
                key={stage.id}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                  isCurrent
                    ? 'bg-blue-600/10 border-blue-500/40 text-slate-100'
                    : isCompleted
                    ? 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                    : 'bg-slate-950/30 border-transparent text-slate-500'
                }`}
              >

                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500 font-mono">
                      {stage.id}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-xs font-medium ${
                        isCurrent
                          ? 'text-blue-300 font-semibold'
                          : isCompleted
                          ? 'text-slate-200'
                          : 'text-slate-500'
                      }`}
                    >
                      {stage.name}
                    </span>
                    {isCurrent && (
                      <span className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">
                        Processing...
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-[11px] mt-0.5 ${
                      isCurrent || isCompleted ? 'text-slate-400' : 'text-slate-600'
                    }`}
                  >
                    {stage.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Prototype Disclaimer */}
        <div className="mt-6 pt-4 border-t border-slate-800 text-center">
          <p className="text-[11px] text-slate-500 flex items-center justify-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
            Decision-support preview: UI representation of the planned AI analysis stages.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default AnalysisProgress;
