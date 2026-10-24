import { useState } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';

const LimeExplanation = ({ explanations = [] }) => {
  const [showTable, setShowTable] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Normalize LIME items
  const items = explanations.map((item) => {
    const rawWeight = item.weight ?? item.score ?? 0;
    const absWeight = Math.abs(rawWeight);
    const tokenOrCode = item.token ? `token: "${item.token}"` : (item.code || item.snippet || item.clause || 'Construct');
    const isRaisesRisk = item.type === 'risk' || rawWeight >= 0;
    const explanationText = item.explanation || item.description || 'Local linear surrogate regression weight.';

    return {
      label: tokenOrCode,
      weight: rawWeight,
      absWeight,
      isRaisesRisk,
      explanation: explanationText,
    };
  });

  const sortedItems = [...items].sort((a, b) => b.absWeight - a.absWeight);
  const displayedItems = showAll ? sortedItems : sortedItems.slice(0, 6);

  const maxWeight = Math.max(
    ...sortedItems.map((item) => item.absWeight),
    0.01
  );

  return (
    <Card
      title="LIME contributions"
      subtitle="How strongly local token perturbations pushed the risk score up or down (linear surrogate)"
      action={
        <Button
          variant="tertiary"
          size="sm"
          onClick={() => setShowTable((prev) => !prev)}
        >
          {showTable ? 'View as chart' : 'View as table'}
        </Button>
      }
    >
      <div className="space-y-4 text-[13px]">
        {/* Table View Alternative */}
        {showTable ? (
          <div className="overflow-x-auto border border-[var(--border)] rounded-[4px]">
            <table className="w-full text-left text-[12px] font-mono tnum">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-muted)]">
                  <th className="p-2.5">Perturbed Token / Clause</th>
                  <th className="p-2.5">Direction</th>
                  <th className="p-2.5 text-right">LIME Weight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {sortedItems.map((item, idx) => (
                  <tr key={idx} className="hover:bg-[var(--surface-subtle)]">
                    <td className="p-2.5 font-medium text-[var(--text-main)]">
                      {item.label}
                    </td>
                    <td className="p-2.5">
                      <span
                        className="font-semibold text-[11px]"
                        style={{
                          color: item.isRaisesRisk ? 'var(--chart-raises)' : 'var(--chart-lowers)',
                        }}
                      >
                        {item.isRaisesRisk ? 'Raises risk' : 'Lowers risk'}
                      </span>
                    </td>
                    <td className="p-2.5 text-right font-mono font-semibold text-[var(--text-main)]">
                      {item.weight >= 0 ? `+${item.weight.toFixed(4)}` : item.weight.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Dual-direction horizontal bars */
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border)] pb-2 select-none">
              <span className="flex items-center gap-1.5" style={{ color: 'var(--chart-lowers)' }}>
                ← Lowers risk
              </span>
              <span className="flex items-center gap-1.5" style={{ color: 'var(--chart-raises)' }}>
                Raises risk →
              </span>
            </div>

            {displayedItems.length === 0 ? (
              <div className="p-4 text-center text-xs text-[var(--text-muted)]">
                No LIME surrogate weights calculated for this scope.
              </div>
            ) : (
              displayedItems.map((item, idx) => {
                const widthPercent = Math.min(100, Math.round((item.absWeight / maxWeight) * 100));

                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-[12px]">
                      <span className="font-mono font-medium text-[var(--text-main)] truncate max-w-[280px]">
                        {item.label}
                      </span>
                      <span
                        className="font-mono text-xs font-semibold tnum shrink-0 ml-2"
                        style={{
                          color: item.isRaisesRisk ? 'var(--chart-raises)' : 'var(--chart-lowers)',
                        }}
                      >
                        {item.weight >= 0 ? `+${item.weight.toFixed(4)}` : item.weight.toFixed(4)}
                      </span>
                    </div>

                    <div className="relative h-2 w-full bg-[var(--surface-subtle)] rounded-[2px] overflow-hidden flex border border-[var(--border)]">
                      <div className="absolute inset-y-0 left-1/2 w-px bg-[var(--border-strong)] z-10" />

                      {/* Lowers risk */}
                      <div className="w-1/2 flex justify-end">
                        {!item.isRaisesRisk && (
                          <div
                            className="h-full rounded-l-[2px]"
                            style={{
                              width: `${widthPercent}%`,
                              backgroundColor: 'var(--chart-lowers)',
                            }}
                          />
                        )}
                      </div>

                      {/* Raises risk */}
                      <div className="w-1/2 flex justify-start">
                        {item.isRaisesRisk && (
                          <div
                            className="h-full rounded-r-[2px]"
                            style={{
                              width: `${widthPercent}%`,
                              backgroundColor: 'var(--chart-raises)',
                            }}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}

            {sortedItems.length > 6 && (
              <div className="pt-2">
                <Button
                  variant="tertiary"
                  size="sm"
                  onClick={() => setShowAll((prev) => !prev)}
                >
                  {showAll ? 'Show top 6 only' : `Show all ${sortedItems.length} tokens`}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Caption */}
        <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] leading-relaxed">
          Explanations describe model behavior; they are not a verified vulnerability.
        </div>
      </div>
    </Card>
  );
};

export default LimeExplanation;
