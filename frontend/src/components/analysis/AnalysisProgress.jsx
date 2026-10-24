import { CheckCircle2, Loader2, Shield } from 'lucide-react';
import Card from '../common/Card';
import Button from '../common/Button';
import { PIPELINE_STAGES } from '../../utils/constants';

const AnalysisProgress = ({
  currentStepIndex = 0,
  contractName = 'Contract.sol',
  progressPercent: explicitProgress,
  stageMessage = '',
  stageName = '',
  onCancel = null,
}) => {
  const progressPercent = typeof explicitProgress === 'number'
    ? explicitProgress
    : Math.min(100, Math.round(((currentStepIndex + 1) / PIPELINE_STAGES.length) * 100));

  return (
    <div className="max-w-[720px] mx-auto py-6">
      <Card className="p-6">
        {/* Header */}
        <div className="mb-6 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-[18px] font-semibold text-[var(--text-main)]">
              Analysis in progress
            </h2>
            <span className="text-[13px] font-mono font-semibold text-[var(--accent)] tnum">
              {progressPercent}%
            </span>
          </div>
          <p className="text-[13px] text-[var(--text-secondary)]">
            Analyzing <span className="font-mono text-[var(--text-main)] font-semibold">{contractName}</span> with Legal-BERT.
          </p>

          {stageMessage && (
            <div className="mt-2 flex items-center gap-2 p-2.5 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] text-[12px] font-mono text-[var(--text-secondary)]">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--accent)] shrink-0" />
              <span>{stageMessage}</span>
            </div>
          )}

          {/* Progress bar */}
          <div className="pt-2">
            <div className="h-1.5 w-full bg-[var(--surface-subtle)] rounded-[2px] overflow-hidden border border-[var(--border)]">
              <div
                className="h-full bg-[var(--accent)] rounded-[2px] transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* 8-Stage Tracker */}
        <div className="space-y-1 divide-y divide-[var(--border)]">
          {PIPELINE_STAGES.map((stage, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;

            return (
              <div
                key={stage.id}
                className={`flex items-start gap-3 py-2.5 px-2 transition-colors ${
                  isCurrent
                    ? 'bg-[var(--accent-tint)] rounded-[4px]'
                    : isCompleted
                    ? 'text-[var(--text-main)]'
                    : 'text-[var(--text-muted)]'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-[var(--low)]" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-[var(--border-strong)] flex items-center justify-center text-[10px] text-[var(--text-muted)] font-mono tnum">
                      {stage.id}
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[13px] ${
                        isCurrent
                          ? 'font-semibold text-[var(--text-main)]'
                          : isCompleted
                          ? 'font-medium text-[var(--text-main)]'
                          : 'text-[var(--text-muted)]'
                      }`}
                    >
                      {stage.name}
                    </span>
                    {isCurrent && (
                      <span className="text-[10px] font-mono text-[var(--accent)] uppercase font-semibold">
                        Processing
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
                    {stage.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Cancellation Option */}
        {onCancel && (
          <div className="mt-6 pt-4 border-t border-[var(--border)] flex items-center justify-between">
            <span className="text-[12px] text-[var(--text-muted)]">
              Job running asynchronously on local backend
            </span>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={onCancel}
            >
              Cancel analysis
            </Button>
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-[var(--text-secondary)] shrink-0" />
          <span>Operational decision support indicator. Absence of findings is not proof of safety.</span>
        </div>
      </Card>
    </div>
  );
};

export default AnalysisProgress;
