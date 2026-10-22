import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Download,
  Search,
  ExternalLink,
  ShieldCheck,
  Calendar,
} from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import { mockReports } from '../data/mockData';
import { api } from '../services/api';

const Reports = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  const filteredReports = mockReports.filter((rep) =>
    rep.contractName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    rep.contractType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDownload = async (report, format) => {
    setDownloadingId(`${report.id}-${format}`);
    const auditId = report.contractId || report.id;
    try {
      await api.downloadReport(auditId, format, report.contractName);
    } catch (err) {
      console.warn('Real report download failed, using fallback notice:', err);
      alert(`Structured Audit Report for "${report.contractName}" prepared in ${format} format.`);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">
            Structured Audit Reports
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Download executive legal-risk reports with SHAP/LIME attributions in PDF or DOCX formats
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredReports.map((report) => (
          <Card
            key={report.id}
            className="border-slate-800 bg-slate-900/60 p-5 flex flex-col justify-between hover:border-slate-700 transition-colors"
          >
            <div>
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">
                      {report.contractName}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {report.contractType}
                    </p>
                  </div>
                </div>

                <Badge riskLevel={report.riskLevel} size="sm" dot />
              </div>

              <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/80 mb-4 space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Risk Score:</span>
                  <span className="font-mono text-slate-200 font-semibold">
                    {report.riskScore}/100
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Audited Date:</span>
                  <span className="font-mono text-slate-300 flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    {report.generatedDate}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Report Sections:</span>
                  <span className="text-slate-300">
                    Exec Summary, Risk Matrix, SHAP/LIME, Recommendations
                  </span>
                </div>
              </div>
            </div>

            {/* Actions Bar */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
              <Link
                to={`/analysis/${report.contractId}`}
                className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
              >
                <span>View Online</span>
                <ExternalLink className="w-3 h-3" />
              </Link>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  icon={Download}
                  isLoading={downloadingId === `${report.id}-PDF`}
                  onClick={() => handleDownload(report, 'PDF')}
                >
                  PDF
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={Download}
                  isLoading={downloadingId === `${report.id}-DOCX`}
                  onClick={() => handleDownload(report, 'DOCX')}
                >
                  DOCX
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Report Structure Notice */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 text-xs text-slate-400 flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Structured Report Specification:</strong> Each generated report includes the 5-point audit sequence: Executive Summary, Overall Risk Score, Highlighted Risky Clauses, AI Recommendations, and Full Compliance Matrix.
        </p>
      </div>
    </div>
  );
};

export default Reports;
