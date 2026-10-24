import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowRight,
  Calendar,
  Trash2,
  Plus,
} from 'lucide-react';
import Card from '../components/common/Card';
import SeverityTag from '../components/common/SeverityTag';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import { mockContracts } from '../data/mockData';
import { api } from '../services/api';

const History = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState('All');
  const [liveAudits, setLiveAudits] = useState([]);
  const [deletingId, setDeletingId] = useState(null);

  const riskLevels = ['All', 'Low', 'Medium', 'High', 'Critical'];

  useEffect(() => {
    let isCancelled = false;

    async function loadHistory() {
      try {
        const data = await api.listHistory(searchQuery, selectedRiskLevel);
        if (!isCancelled && data?.analyses && data.analyses.length > 0) {
          setLiveAudits(data.analyses);
        } else if (!isCancelled) {
          setLiveAudits([]);
        }
      } catch (e) {
        console.warn('Live history fetch failed:', e);
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

  const sourceData = liveAudits.length > 0 ? liveAudits : mockContracts;
  const filteredContracts = sourceData.filter((contract) => {
    const nameStr = (contract.name || contract.contractName || '').toLowerCase();
    const typeStr = (contract.contractType || '').toLowerCase();
    const descStr = (contract.description || '').toLowerCase();
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || nameStr.includes(q) || typeStr.includes(q) || descStr.includes(q);

    const rLevel = contract.overallRiskLevel || contract.riskLevel || 'Low';
    const matchesRisk = selectedRiskLevel === 'All' || rLevel.toLowerCase() === selectedRiskLevel.toLowerCase();

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold text-[var(--text-main)] leading-tight">
            Audit history
          </h1>
          <p className="text-[14px] text-[var(--text-secondary)]">
            Archive of Solidity contracts analyzed on this machine.
          </p>
        </div>

        <Link to="/analysis/new">
          <Button variant="primary" size="md" icon={Plus}>
            New analysis
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="flex-1 w-full">
          <Input
            placeholder="Search contracts by name, type, or keyword..."
            icon={Search}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Risk Level Filter Chips */}
        <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0" role="radiogroup" aria-label="Filter by Risk Level">
          <Filter className="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0 mr-1" />
          {riskLevels.map((level) => (
            <button
              key={level}
              type="button"
              role="radio"
              aria-checked={selectedRiskLevel === level}
              onClick={() => setSelectedRiskLevel(level)}
              className={`px-2.5 py-1 rounded-[3px] text-xs font-medium whitespace-nowrap transition-colors focus-ring cursor-pointer border ${
                selectedRiskLevel === level
                  ? 'bg-[var(--surface)] text-[var(--text-main)] border-[var(--border-strong)] font-semibold shadow-xs'
                  : 'bg-[var(--surface-subtle)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--surface)] hover:text-[var(--text-main)]'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Table */}
      <Card contentClassName="p-0 overflow-x-auto">
        {filteredContracts.length === 0 ? (
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
          <table className="w-full text-left text-[13px] border-collapse">
            <thead>
              <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-muted)] font-mono text-[11px] uppercase tracking-wider">
                <th className="py-2.5 px-4">Contract</th>
                <th className="py-2.5 px-4">Risk Level</th>
                <th className="py-2.5 px-4">Score</th>
                <th className="py-2.5 px-4">Summary</th>
                <th className="py-2.5 px-4">Audited Date</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)] text-[var(--text-secondary)]">
              {filteredContracts.map((contract, idx) => {
                const auditId = contract.id || contract.analysisId || `audit-${idx + 1}`;
                const contractName = contract.name || contract.contractName || 'Contract.sol';
                const riskLevel = contract.overallRiskLevel || contract.riskLevel || 'Low';
                const riskScore = contract.overallRiskScore ?? contract.riskScore ?? 0;
                const auditDate = contract.auditDate || contract.created_at || 'Recent';

                return (
                  <tr
                    key={auditId}
                    className="hover:bg-[var(--surface-subtle)] transition-colors group"
                  >
                    <td className="py-3 px-4 font-medium text-[var(--text-main)]">
                      <div>
                        <div className="font-semibold font-mono text-[13px] group-hover:text-[var(--accent)] transition-colors">
                          {contractName}
                        </div>
                        <div className="text-[11px] text-[var(--text-muted)] font-mono">
                          {auditId}
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <SeverityTag severity={riskLevel} size="sm" />
                    </td>

                    <td className="py-3 px-4 font-mono font-medium whitespace-nowrap tnum">
                      <span className="text-[var(--text-main)]">{riskScore}</span>
                      <span className="text-[var(--text-muted)] text-[11px]">/100</span>
                    </td>

                    <td className="py-3 px-4 max-w-xs truncate text-[var(--text-secondary)] text-[12px]">
                      {contract.summary || 'Operational legal risk triage evaluated.'}
                    </td>

                    <td className="py-3 px-4 text-[var(--text-muted)] text-[11px] font-mono whitespace-nowrap tnum">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3 text-[var(--text-muted)]" />
                        {auditDate}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-2">
                        <Link
                          to={`/analysis/${auditId}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-[3px] border border-[var(--border-strong)] bg-[var(--surface)] hover:bg-[var(--surface-subtle)] text-[var(--text-main)] text-xs font-medium focus-ring"
                        >
                          <span>Review</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                        {liveAudits.length > 0 && (
                          <button
                            type="button"
                            onClick={(e) => handleDelete(auditId, e)}
                            disabled={deletingId === auditId}
                            title="Delete audit"
                            aria-label={`Delete audit ${auditId}`}
                            className="text-[var(--text-muted)] hover:text-[var(--critical)] p-1 rounded-[3px] focus-ring transition-colors disabled:opacity-50 cursor-pointer"
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
