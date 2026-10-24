import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Download,
  Search,
  ExternalLink,
  Calendar,
} from 'lucide-react';
import Card from '../components/common/Card';
import SeverityTag from '../components/common/SeverityTag';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import EmptyState from '../components/common/EmptyState';
import { mockReports } from '../data/mockData';
import { api } from '../services/api';

const Reports = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);
  const [liveReports, setLiveReports] = useState([]);

  useEffect(() => {
    let isCancelled = false;
    async function loadReports() {
      try {
        const data = await api.listHistory();
        if (!isCancelled && data?.analyses && data.analyses.length > 0) {
          const mapped = data.analyses.map((a) => ({
            id: a.id || a.analysisId,
            contractId: a.id || a.analysisId,
            contractName: a.contractName || a.name || 'Contract.sol',
            contractType: a.contractType || 'Solidity Smart Contract',
            riskScore: a.overallRiskScore ?? a.riskScore ?? 0,
            riskLevel: a.overallRiskLevel || a.riskLevel || 'Low',
            generatedDate: a.auditDate || a.created_at || 'Recent',
          }));
          setLiveReports(mapped);
        }
      } catch (err) {
        console.warn('Failed to load local reports:', err);
      }
    }

    loadReports();
    return () => {
      isCancelled = true;
    };
  }, []);

  const sourceReports = liveReports.length > 0 ? liveReports : mockReports;
  const filteredReports = sourceReports.filter((rep) =>
    rep.contractName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (rep.contractType || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDownload = async (report, format) => {
    setDownloadingId(`${report.id}-${format}`);
    const auditId = report.contractId || report.id;
    try {
      await api.downloadReport(auditId, format, report.contractName);
    } catch (err) {
      console.warn('Report download error:', err);
      alert(`Report download failed: ${err.message}`);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="space-y-1">
          <h1 className="text-[24px] font-semibold text-[var(--text-main)] leading-tight">
            Audit reports
          </h1>
          <p className="text-[14px] text-[var(--text-secondary)]">
            Download structured audit reports with XAI attributions in PDF or Word DOCX formats.
          </p>
        </div>

        <div className="w-full sm:w-72">
          <Input
            placeholder="Search reports..."
            icon={Search}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Reports Grid */}
      {filteredReports.length === 0 ? (
        <Card className="p-8">
          <EmptyState
            title="No Reports Available"
            description="No smart contracts match your search criteria. Run an analysis to generate downloadable reports."
            actionLabel="Start New Analysis"
            actionLink="/analysis/new"
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredReports.map((report) => (
            <Card
              key={report.id}
              className="p-4 flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="text-[15px] font-semibold font-mono text-[var(--text-main)]">
                      {report.contractName}
                    </h3>
                    <p className="text-[12px] text-[var(--text-muted)]">
                      {report.contractType || 'Solidity Smart Contract'}
                    </p>
                  </div>
                  <SeverityTag severity={report.riskLevel} size="sm" />
                </div>

                <div className="flex items-center gap-4 text-[12px] text-[var(--text-secondary)] font-mono tnum pt-1">
                  <span>Score: <strong className="text-[var(--text-main)]">{report.riskScore}/100</strong></span>
                  <span className="flex items-center gap-1 text-[var(--text-muted)]">
                    <Calendar className="w-3.5 h-3.5" />
                    {report.generatedDate}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between gap-2">
                <Link
                  to={`/analysis/${report.contractId || report.id}`}
                  className="text-xs text-[var(--accent)] hover:underline font-medium inline-flex items-center gap-1 focus-ring rounded-[2px]"
                >
                  <span>Open review</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>

                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={Download}
                    isLoading={downloadingId === `${report.id}-PDF`}
                    onClick={() => handleDownload(report, 'PDF')}
                    className="text-xs"
                  >
                    PDF
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={Download}
                    isLoading={downloadingId === `${report.id}-DOCX`}
                    onClick={() => handleDownload(report, 'DOCX')}
                    className="text-xs"
                  >
                    DOCX
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Reports;
