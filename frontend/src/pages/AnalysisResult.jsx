import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  Share2,
  FileCode,
  Layers,
  Lightbulb,
  Cpu,
  Copy,
  Check,
  Loader2,
  AlertCircle,
  PlusCircle,
  MessageSquare,
  FileText,
  Trash2,
  ShieldAlert,
} from 'lucide-react';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import RiskSummary from '../components/analysis/RiskSummary';
import RiskCard from '../components/analysis/RiskCard';
import CodeViewer from '../components/analysis/CodeViewer';
import ShapChart from '../components/analysis/ShapChart';
import LimeExplanation from '../components/analysis/LimeExplanation';
import RecommendationCard from '../components/analysis/RecommendationCard';
import ComplianceMatrix from '../components/analysis/ComplianceMatrix';
import LegalChatAssistant from '../components/analysis/LegalChatAssistant';
import { api } from '../services/api';

const AnalysisResult = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'code' | 'xai' | 'recommendations' | 'assistant'
  const [downloading, setDownloading] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [discarding, setDiscarding] = useState(false);

  // Analysis data state
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadAuditReport() {
      setLoading(true);
      setLoadError(null);

      // 1. Check if passed via React Router navigation state
      const stateResult = location.state?.analysisResult;
      if (stateResult && (stateResult.analysisId === id || stateResult.id === id)) {
        if (!isCancelled) {
          setContract(stateResult);
          setLoading(false);
        }
        return;
      }

      // 2. Check cached or live API service (from ephemeral in-memory store)
      try {
        const liveResult = await api.getAnalysis(id);
        if (liveResult && !isCancelled) {
          setContract(liveResult);
          setLoading(false);
          return;
        }
      } catch (err) {
        console.warn('API lookup by ID failed:', err);
      }

      // 3. In local no-login mode: Do NOT fall back to static mock data
      if (!isCancelled) {
        setLoadError(
          `Audit report '${id}' could not be located in local storage or active session cache.`
        );
        setLoading(false);
      }
    }

    loadAuditReport();

    return () => {
      isCancelled = true;
    };
  }, [id, location.state]);

  const handleDownloadReport = async (format = 'PDF') => {
    if (format === 'PDF') setDownloading(true);
    else setDownloadingDocx(true);

    const aId = contract?.analysisId || contract?.id || id;
    const cName = contract?.name || contract?.contractName || 'Contract';

    try {
      await api.downloadReport(aId, format, cName);
    } catch (err) {
      console.warn('Backend report download failed:', err);
      alert(`Structured Audit Report for "${cName}" export failed.`);
    } finally {
      if (format === 'PDF') setDownloading(false);
      else setDownloadingDocx(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const handleDiscardAndNew = async () => {
    if (!window.confirm('Discard current temporary analysis result and start a new audit?')) {
      return;
    }
    setDiscarding(true);
    const aId = contract?.analysisId || contract?.id || id;
    try {
      await api.discardAnalysis(aId);
    } catch (e) {
      console.warn('Discard failed:', e);
    }
    navigate('/analysis/new');
  };

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        <h3 className="text-base font-semibold text-slate-200">
          Loading Audit Report...
        </h3>
        <p className="text-xs text-slate-400 font-mono">
          Resolving temporary analysis ID: {id}
        </p>
      </div>
    );
  }

  if (loadError || !contract) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-5 text-center">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-100">Audit Not Found or Expired</h3>
        <p className="text-xs text-slate-400 leading-relaxed max-w-md mx-auto">
          {loadError || `Unable to load audit '${id}'.`}
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Link to="/analysis/new">
            <Button variant="primary" size="sm" icon={PlusCircle}>
              Start New Analysis
            </Button>
          </Link>
          <Link to="/">
            <Button variant="secondary" size="sm">
              Home
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const contractName = contract.name || contract.contractName || 'Contract.sol';
  const analysisId = contract.id || contract.analysisId || id;

  return (
    <div className="space-y-8">
      {/* ============================================================ */}
      {/* 1. TOP HEADER & ACTIONS                                      */}
      {/* ============================================================ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <Link to="/analysis/new">
            <Button variant="ghost" size="sm" icon={ArrowLeft}>
              New Audit
            </Button>
          </Link>
          <div className="h-4 w-px bg-slate-800" />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-slate-100">
                Audit Report: <span className="font-mono text-blue-400">{contractName}</span>
              </h2>

              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-semibold flex items-center gap-1.5 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Legal-BERT Neural Inference
              </span>
            </div>

            <p className="text-xs text-slate-400 mt-0.5">
              Audit ID: <span className="font-mono text-slate-300">{analysisId}</span> • Local Audit Workspace
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            icon={Download}
            isLoading={downloading}
            onClick={() => handleDownloadReport('PDF')}
          >
            Export PDF
          </Button>

          <Button
            variant="outline"
            size="sm"
            icon={FileText}
            isLoading={downloadingDocx}
            onClick={() => handleDownloadReport('DOCX')}
          >
            Export DOCX
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={Share2}
            onClick={() => setShareModalOpen(true)}
          >
            Share
          </Button>

          <Button
            variant="ghost"
            size="sm"
            icon={Trash2}
            isLoading={discarding}
            onClick={handleDiscardAndNew}
            className="text-red-400 hover:text-red-300 hover:bg-red-950/20 border border-red-900/40"
          >
            Discard & New
          </Button>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 2. RESEARCH PROTOTYPE & CRITICAL SAFETY WARNING BANNER       */}
      {/* ============================================================ */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-200 space-y-3">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1.5 w-full">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs sm:text-sm font-bold text-amber-100 flex items-center gap-2">
                CRITICAL NOTICE: Absence of Findings is NOT Proof of Contract Safety
              </h3>
              <span className="text-[11px] px-2 py-0.5 rounded bg-amber-950/60 border border-amber-700/50 text-amber-300 font-mono">
                Checkpoint: {contract.metadata?.checkpointName || contract.modelDisclosures?.checkpointName || 'legal_bert_v3.3.0'}
              </span>
            </div>
            <p className="text-xs text-amber-300/90 leading-relaxed">
              {contract.safetyWarning || (
                'Low predicted risk scores or the absence of detected findings do NOT constitute proof that a smart contract is safe, compliant, or free from operational legal hazards. This prototype Legal-BERT multi-label model was trained on a small dataset (N=44). In the held-out real-source test split (N=7), categories Privacy, Liability, and Payment / Financial had zero positive examples (inconclusive support), and the model missed all test positives for Termination and Legal Compliance at the default 0.50 uncalibrated threshold.'
              )}
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-amber-400/90 font-mono pt-1">
              <span>• Raw scores are uncalibrated sigmoid outputs, NOT true statistical probabilities.</span>
              <span>• Test Macro F1: 0.0000 | Specificity: 100.0% (28/28 negatives)</span>
            </div>
          </div>
        </div>

        {/* Experiment Report Test Benchmark Table */}
        {contract.testEvaluationReport && (
          <div className="mt-3 pt-3 border-t border-amber-500/20 text-xs text-slate-300 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-amber-200 text-xs">
                Held-Out Real-Source Test Split Benchmark (N=7 Contracts, 35 Decisions)
              </span>
              <span className="text-[10px] text-amber-400/70 font-mono">
                Baseline TF-IDF Macro F1: 0.1600 vs Legal-BERT: 0.0000
              </span>
            </div>
            <div className="overflow-x-auto rounded border border-amber-900/40 bg-slate-950/60">
              <table className="w-full text-left text-[11px] font-mono">
                <thead>
                  <tr className="border-b border-amber-900/40 bg-amber-950/30 text-amber-300">
                    <th className="p-2">Category</th>
                    <th className="p-2">Pos / Neg</th>
                    <th className="p-2">TP / FN / TN</th>
                    <th className="p-2">Precision</th>
                    <th className="p-2">Recall</th>
                    <th className="p-2">F1</th>
                    <th className="p-2">Support Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {contract.testEvaluationReport.categoryBreakdown?.map((cat, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="p-2 font-medium text-slate-200">{cat.category}</td>
                      <td className="p-2">{cat.testPositives} / {cat.testNegatives}</td>
                      <td className="p-2">{cat.truePositives} / {cat.falseNegatives} / {cat.trueNegatives}</td>
                      <td className="p-2">{cat.precision.toFixed(4)}</td>
                      <td className="p-2">{cat.recall.toFixed(4)}</td>
                      <td className="p-2">{cat.f1.toFixed(4)}</td>
                      <td className="p-2">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                          cat.supportStatus.includes('inconclusive')
                            ? 'bg-slate-800 text-slate-400'
                            : 'bg-red-950/50 text-red-300 border border-red-900/40'
                        }`}>
                          {cat.supportStatus}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ============================================================ */}
      {/* 3. OVERALL RISK SUMMARY COMPONENT                            */}
      {/* ============================================================ */}
      <RiskSummary contract={contract} />

      {/* ============================================================ */}
      {/* 4. 5 RISK CATEGORIES BREAKDOWN                               */}
      {/* ============================================================ */}
      <RiskCard categories={contract.categories || []} />

      {/* ============================================================ */}
      {/* 5. SECTION TABS                                              */}
      {/* ============================================================ */}
      <div className="border-b border-slate-800 flex items-center justify-between overflow-x-auto">
        <div className="flex gap-4 min-w-max">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'all'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-4 h-4" />
            Full Audit View
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('code')}
            className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'code'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="w-4 h-4" />
            Code & Risky Clauses
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('xai')}
            className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'xai'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" />
            XAI Explanations (SHAP & LIME)
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('recommendations')}
            className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'recommendations'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Lightbulb className="w-4 h-4" />
            Recommendations & Compliance
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('assistant')}
            className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'assistant'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            AI Legal Assistant
          </button>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 6. TABBED VIEWS                                              */}
      {/* ============================================================ */}
      {/* View 1: Code Viewer with Accurate Finding Line Numbers */}
      {(activeTab === 'all' || activeTab === 'code') && (
        <section className="space-y-4">
          <CodeViewer
            code={contract.solidityCode || ''}
            findings={contract.findings || []}
          />
        </section>
      )}

      {/* View 2: XAI Interpretability (Genuine Neural Gradient Saliency) */}
      {(activeTab === 'all' || activeTab === 'xai') && (
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ShapChart explanations={contract.shapValues || contract.xai?.tokenAttributions || []} />
          <LimeExplanation explanations={contract.limeExplanations || []} />
        </section>
      )}

      {/* View 3: Recommendations & Compliance Matrix */}
      {(activeTab === 'all' || activeTab === 'recommendations') && (
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RecommendationCard recommendations={contract.recommendations || []} />
          <ComplianceMatrix matrix={contract.complianceMatrix || []} />
        </section>
      )}

      {/* View 4: Context-Scoped AI Legal Assistant */}
      {(activeTab === 'all' || activeTab === 'assistant') && (
        <section className="space-y-4">
          <LegalChatAssistant contractId={analysisId} contractName={contractName} />
        </section>
      )}

      {/* Share Report Modal */}
      <Modal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        title="Share Structured Audit Report"
        subtitle={`Decision-support report for ${contractName}`}
        footer={
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShareModalOpen(false)}
          >
            Close
          </Button>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Direct Audit URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={window.location.href}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 px-3 py-2 select-all focus:outline-none"
              />
              <Button
                variant="primary"
                size="sm"
                icon={linkCopied ? Check : Copy}
                onClick={handleCopyLink}
              >
                {linkCopied ? 'Copied' : 'Copy'}
              </Button>
            </div>
          </div>

          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs text-slate-400 space-y-1">
            <span className="font-semibold text-slate-300">Auditor Note:</span>
            <p>
              Shared reports include full Legal-BERT category breakdown, word-embedding gradient saliency, and statutory compliance assessments.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AnalysisResult;
