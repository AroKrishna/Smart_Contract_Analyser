import { useState } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';

const ShapChart = ({ explanations = [], onJumpToLine = null }) => {
  const [showTable, setShowTable] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Normalize data items
  const items = explanations.map((e) => {
    const rawVal = e.contribution ?? e.value ?? 0;
    const absVal = Math.abs(rawVal);
    const tokenName = e.token || e.feature || 'Token';
    const categoryName = e.category || 'General';
    const isRaisesRisk = e.impact ? e.impact === 'positive' : rawVal >= 0;
    const lineNum = e.line || (typeof e.token === 'string' && e.token.match(/line\s*(\d+)/i) ? parseInt(RegExp.$1, 10) : null);

    return {
      token: tokenName,
      category: categoryName,
      val: rawVal,
      absVal,
      isRaisesRisk,
      lineNum,
    };
  });

  // Sort by absolute contribution descending
  const sortedItems = [...items].sort((a, b) => b.absVal - a.absVal);
  const displayedItems = showAll ? sortedItems : sortedItems.slice(0, 6);

  const maxVal = Math.max(
    ...sortedItems.map((item) => item.absVal),
    0.01
  );

  return (
    <Card
      title="SHAP contributions"
      subtitle="How strongly each part of the code pushed the risk score up or down (Shapley values)"
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
                  <th className="p-2.5">Feature / Token</th>
                  <th className="p-2.5">Category</th>
                  <th className="p-2.5">Direction</th>
                  <th className="p-2.5 text-right">Shapley Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {sortedItems.map((item, idx) => (
                  <tr key={idx} className="hover:bg-[var(--surface-subtle)]">
                    <td className="p-2.5 font-medium text-[var(--text-main)]">
                      {item.token}
                    </td>
                    <td className="p-2.5 text-[var(--text-secondary)]">
                      {item.category}
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
                      {item.val >= 0 ? `+${item.val.toFixed(4)}` : item.val.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Horizontal Bars Around Center Axis */
          <div className="space-y-3">
            {/* Axis Labels */}
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
                No significant SHAP token attributions calculated.
              </div>
            ) : (
              displayedItems.map((item, idx) => {
                const widthPercent = Math.min(100, Math.round((item.absVal / maxVal) * 100));

                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between text-[12px]">
                      <div className="flex items-center gap-2 truncate">
                        <span className="font-mono font-medium text-[var(--text-main)] truncate">
                          {item.token}
                        </span>
                        <span className="text-[11px] text-[var(--text-muted)] hidden sm:inline">
                          [{item.category}]
                        </span>
                      </div>
                      <span
                        className="font-mono text-xs font-semibold tnum shrink-0 ml-2"
                        style={{
                          color: item.isRaisesRisk ? 'var(--chart-raises)' : 'var(--chart-lowers)',
                        }}
                      >
                        {item.val >= 0 ? `+${item.val.toFixed(4)}` : item.val.toFixed(4)}
                      </span>
                    </div>

                    {/* Dual-direction centered axis bar */}
                    <div className="relative h-2 w-full bg-[var(--surface-subtle)] rounded-[2px] overflow-hidden flex border border-[var(--border)]">
                      {/* Center guideline */}
                      <div className="absolute inset-y-0 left-1/2 w-px bg-[var(--border-strong)] z-10" />

                      {/* Left side (Lowers risk) */}
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

                      {/* Right side (Raises risk) */}
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

        {/* Advisory Caption */}
        <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--text-muted)] leading-relaxed">
          Explanations describe model behavior; they are not a verified vulnerability.
        </div>
      </div>
    </Card>
  );
};

export default ShapChart;
