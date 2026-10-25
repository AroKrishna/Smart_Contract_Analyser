import { Link } from 'react-router-dom';
import { FileCode, ArrowUpRight, ShieldCheck } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';

const RecentAnalysis = ({ contracts = [] }) => {
  return (
    <Card
      title="Recent Contract Analyses"
      subtitle="Latest Solidity smart contracts evaluated by Legal-BERT with SHAP / LIME attribution"
      action={
        <Link
          to="/history"
          className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
        >
          View all audits <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      }
      className="border-slate-800/80 bg-slate-900/60"
      contentClassName="p-0 overflow-x-auto"
    >
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-slate-800/80 bg-slate-950/60 text-slate-400">
            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">
              Contract Name
            </th>
            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">
              Type
            </th>
            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">
              Audited At
            </th>
            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">
              Legal Risk
            </th>
            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px] text-right">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {contracts.length === 0 ? (
            <tr>
              <td colSpan="5" className="py-8 px-4 text-center text-slate-400">
                <FileCode className="w-6 h-6 mx-auto mb-2 text-slate-500 opacity-60" />
                <p className="font-medium text-slate-300">No contract analyses yet</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Submit a Solidity contract to generate Legal-BERT risk assessments.
                </p>
              </td>
            </tr>
          ) : (
            contracts.map((item) => (
            <tr
              key={item.id}
              className="hover:bg-slate-850/40 transition-colors group"
            >
              <td className="py-3.5 px-4 font-medium text-slate-200">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <FileCode className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                      {item.name}
                    </span>
                    <p className="text-[11px] text-slate-400 font-normal line-clamp-1">
                      {item.description}
                    </p>
                  </div>
                </div>
              </td>

              <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                {item.contractType}
              </td>

              <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap font-mono text-[11px]">
                {item.auditDate}
              </td>

              <td className="py-3.5 px-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <Badge riskLevel={item.overallRiskLevel} size="sm" dot />
                  <span className="font-mono text-slate-300 font-medium">
                    {item.overallRiskScore}/100
                  </span>
                </div>
              </td>

              <td className="py-3.5 px-4 text-right whitespace-nowrap">
                <Link
                  to={`/analysis/${item.id}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors text-xs font-medium border border-slate-700/80"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                  View Audit
                </Link>
              </td>
            </tr>
          )))}
        </tbody>
      </table>
    </Card>
  );
};

export default RecentAnalysis;
