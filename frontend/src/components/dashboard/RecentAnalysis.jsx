import { Link } from 'react-router-dom';
import Card from '../common/Card';
import SeverityTag from '../common/SeverityTag';
import { ArrowRight } from 'lucide-react';

const RecentAnalysis = ({ contracts = [] }) => {
  return (
    <Card
      title="Recent contract analyses"
      subtitle="Latest Solidity smart contracts evaluated on this workspace"
      action={
        <Link
          to="/history"
          className="text-[12px] text-[var(--accent)] hover:underline font-medium flex items-center gap-1 focus-ring rounded-[2px]"
        >
          View all audits <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
      contentClassName="p-0 overflow-x-auto"
    >
      <table className="w-full text-left border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-muted)] font-mono">
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Contract Name
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Type
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Audited At
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px]">
              Legal Risk
            </th>
            <th className="py-2.5 px-4 font-semibold uppercase tracking-wider text-[11px] text-right">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border)]">
          {contracts.length === 0 ? (
            <tr>
              <td colSpan={5} className="py-6 px-4 text-center text-xs text-[var(--text-muted)]">
                No contract analyses recorded yet. Run your first analysis to see results here.
              </td>
            </tr>
          ) : (
            contracts.map((item) => (
              <tr
                key={item.id}
                className="hover:bg-[var(--surface-subtle)] transition-colors group"
              >
                <td className="py-3 px-4 font-medium text-[var(--text-main)]">
                  <div>
                    <span className="font-semibold font-mono text-[13px] group-hover:text-[var(--accent)] transition-colors">
                      {item.name}
                    </span>
                    {item.description && (
                      <p className="text-[11px] text-[var(--text-muted)] font-normal line-clamp-1">
                        {item.description}
                      </p>
                    )}
                  </div>
                </td>

                <td className="py-3 px-4 text-[var(--text-secondary)] whitespace-nowrap text-[12px]">
                  {item.contractType || 'Solidity Contract'}
                </td>

                <td className="py-3 px-4 text-[var(--text-muted)] whitespace-nowrap font-mono text-[11px] tnum">
                  {item.auditDate || 'Recent'}
                </td>

                <td className="py-3 px-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <SeverityTag severity={item.overallRiskLevel} size="sm" />
                    <span className="font-mono text-[var(--text-secondary)] font-medium tnum text-xs">
                      {item.overallRiskScore}/100
                    </span>
                  </div>
                </td>

                <td className="py-3 px-4 text-right whitespace-nowrap">
                  <Link
                    to={`/analysis/${item.id}`}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-[3px] border border-[var(--border-strong)] bg-[var(--surface)] hover:bg-[var(--surface-subtle)] text-[var(--text-main)] transition-colors text-xs font-medium focus-ring"
                  >
                    Open review
                  </Link>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </Card>
  );
};

export default RecentAnalysis;
