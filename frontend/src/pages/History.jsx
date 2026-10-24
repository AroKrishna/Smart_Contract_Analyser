import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileCode,
  Search,
  Filter,
  ArrowUpRight,
  ShieldCheck,
  Calendar,
  Database,
  Trash2,
} from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import { mockContracts } from '../data/mockData';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

const History = () => {
  const { user, isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState('All');
  const [liveAudits, setLiveAudits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const riskLevels = ['All', 'Low', 'Medium', 'High', 'Critical'];

  useEffect(() => {
    let isCancelled = false;

    async function loadHistory() {
      setLoading(true);
      try {
        const data = await api.listHistory(searchQuery, selectedRiskLevel);
        if (!isCancelled && data?.analyses) {
          setLiveAudits(data.analyses);
        } else if (!isCancelled) {
          setLiveAudits([]);
        }
      } catch (e) {
        console.warn('Live history fetch failed:', e);
      } finally {
        if (!isCancelled) setLoading(false);
      }
    }

    loadHistory();

    return () => {
      isCancelled = true;
    };
  }, [searchQuery, selectedRiskLevel]);

  const handleDelete = async (auditId, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to permanently delete audit '${auditId}'?`)) {
      return;
    }
    setDeletingId(auditId);
    try {
      await api.deleteAnalysis(auditId);
      setLiveAudits((prev) => prev.filter((a) => (a.id || a.analysisId) !== auditId));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  // For authenticated users, display strictly their persistent audits from the backend
  const displayContracts = isAuthenticated
    ? liveAudits
    : mockContracts.filter((contract) => {
        const matchesSearch =
          contract.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          contract.contractType.toLowerCase().includes(searchQuery.toLowerCase()) ||
          contract.description.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesRisk =
          selectedRiskLevel === 'All' || contract.overallRiskLevel === selectedRiskLevel;

        return matchesSearch && matchesRisk;
      });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100">
              Audit History & Archive
            </h2>
            {liveAudits.length > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[11px] font-mono">
                <Database className="w-3 h-3" /> SQLite Storage Connected
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Historical archive of all Solidity contracts assessed by Legal-BERT and XAI interpretability
          </p>
        </div>

        <Link to="/analysis/new">
          <Button variant="primary" size="sm">
            + New Contract Audit
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center gap-4">
        <div className="flex-1 w-full">
          <Input
            placeholder="Search contracts by name, type, or keyword..."
            icon={Search}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Risk Level Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0 mr-1" />
          {riskLevels.map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setSelectedRiskLevel(level)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors border ${
                selectedRiskLevel === level
                  ? 'bg-blue-600 text-white border-blue-500 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Table */}
      <Card
        className="border-slate-800 bg-slate-900/60"
        contentClassName="p-0 overflow-x-auto"
      >
        {displayContracts.length === 0 ? (
          <EmptyState
            title="No Audits Found"
            description="No smart contracts match your search term or risk category filter."
            actionLabel="Reset Search & Filters"
            onAction={() => {
              setSearchQuery('');
              setSelectedRiskLevel('All');
            }}
          />
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Contract / Protocol</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Composite Score</th>
                <th className="py-3 px-4">Evaluation Summary</th>
                <th className="py-3 px-4">Audited Date</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {displayContracts.map((contract) => {
                const auditId = contract.id || contract.analysisId;
                const contractName = contract.name || contract.contractName || 'Contract.sol';
                const riskLevel = contract.overallRiskLevel || contract.riskLevel || 'Low';
                const riskScore = contract.overallRiskScore ?? contract.riskScore ?? 0;
                const auditDate = contract.auditDate || contract.created_at || 'Recent';

                return (
                  <tr
                    key={auditId}
                    className="hover:bg-slate-900/40 transition-colors group"
                  >
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
                          <FileCode className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-100 group-hover:text-blue-400 transition-colors">
                            {contractName}
                          </div>
                          <div className="text-[10px] text-slate-500 font-mono">
                            {auditId}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <Badge riskLevel={riskLevel} size="sm" dot />
                    </td>

                    <td className="py-3.5 px-4 font-mono font-medium">
                      <span className="text-slate-200">{riskScore}</span>
                      <span className="text-slate-500 text-[10px]">/100</span>
                    </td>

                    <td className="py-3.5 px-4 max-w-xs truncate text-slate-400 text-[11px]">
                      {contract.summary || 'Operational legal risk triage evaluated.'}
                    </td>

                    <td className="py-3.5 px-4 text-slate-400 text-[11px] font-mono">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3 text-slate-500" />
                        {auditDate}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="inline-flex items-center gap-3">
                        <Link
                          to={`/analysis/${auditId}`}
                          className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 font-semibold group-hover:translate-x-0.5 transition-transform"
                        >
                          <span>View</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </Link>
                        {isAuthenticated && (
                          <button
                            type="button"
                            onClick={(e) => handleDelete(auditId, e)}
                            disabled={deletingId === auditId}
                            title="Delete audit"
                            className="text-slate-500 hover:text-red-400 p-1 rounded hover:bg-slate-800 transition-colors disabled:opacity-50"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
};

export default History;
