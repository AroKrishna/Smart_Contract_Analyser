import { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import {
  AlertCircle,
  PlusCircle,
  Copy,
  Check,
  Shield,
  Layers,
  Lightbulb,
  MessageSquare,
  ListFilter,
  X,
} from 'lucide-react';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import AnalysisSummaryStrip from '../components/analysis/AnalysisSummaryStrip';
import FindingsOutline from '../components/analysis/FindingsOutline';
import CodeViewer from '../components/analysis/CodeViewer';
import FindingDetailPanel from '../components/analysis/FindingDetailPanel';
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

  // Data state
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // Active finding selection
  const [selectedFindingId, setSelectedFindingId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [mobileActiveZone, setMobileActiveZone] = useState('source'); // 'findings' | 'source' | 'details'
  const [tabletDrawerOpen, setTabletDrawerOpen] = useState(false);
  const [activeSecondaryTab, setActiveSecondaryTab] = useState('xai'); // 'xai' | 'recommendations' | 'assistant'

  // Action states
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);
  const [discarding, setDiscarding] = useState(false);

  const detailTitleRef = useRef(null);

  // Load audit report
  useEffect(() => {
    let isCancelled = false;

    async function loadAuditReport() {
      setLoading(true);
      setLoadError(null);

      // 1. Check router state
      const stateResult = location.state?.analysisResult;
      if (stateResult && (stateResult.analysisId === id || stateResult.id === id)) {
        if (!isCancelled) {
          setContract(stateResult);
          initSelection(stateResult);
          setLoading(false);
        }
        return;
      }

      // 2. Fetch from API or cache
      try {
        const liveResult = await api.getAnalysis(id);
        if (liveResult && !isCancelled) {
          setContract(liveResult);
          initSelection(liveResult);
          setLoading(false);
          return;
        }
      } catch (err) {
        console.warn('API lookup by ID failed:', err);
      }

      if (!isCancelled) {
        setLoadError(
          `Audit report '${id}' could not be located. In-memory temporary sessions expire after 30 minutes.`
        );
        setLoading(false);
      }
    }

    function initSelection(data) {
      const fList = data.findings || [];
      if (fList.length > 0) {
        const first = fList[0];
        setSelectedFindingId(first.findingId || first.id || 'f-1');
      }
    }

    loadAuditReport();

    return () => {
      isCancelled = true;
    };
  }, [id, location.state]);

  const handleDownloadReport = async (format = 'PDF') => {
    if (format === 'PDF') setDownloadingPdf(true);
    else setDownloadingDocx(true);

    const aId = contract?.analysisId || contract?.id || id;
    const cName = contract?.name || contract?.contractName || 'Contract';

    try {
      await api.downloadReport(aId, format, cName);
    } catch (err) {
      console.warn('Report download failed:', err);
      alert(`Report export for "${cName}" failed.`);
    } finally {
      if (format === 'PDF') setDownloadingPdf(false);
      else setDownloadingDocx(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  const handleDiscardAndNew = async () => {
    if (!window.confirm('Discard current analysis result and start a new audit?')) {
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

  // Findings list and navigation
  const findings = contract?.findings || [];
  const selectedIndex = findings.findIndex(
    (f, idx) => (f.findingId || f.id || `f-${idx + 1}`) === selectedFindingId
  );
  const currentFinding = selectedIndex >= 0 ? findings[selectedIndex] : findings[0] || null;

  const handleSelectFinding = (findingId) => {
    setSelectedFindingId(findingId);
    setTabletDrawerOpen(false);
    // On mobile, keep on source or switch to source
    if (window.innerWidth < 768 && mobileActiveZone === 'findings') {
      setMobileActiveZone('source');
    }
  };

  const handlePreviousFinding = () => {
    if (selectedIndex > 0) {
      const prev = findings[selectedIndex - 1];
      setSelectedFindingId(prev.findingId || prev.id || `f-${selectedIndex}`);
    }
  };

  const handleNextFinding = () => {
    if (selectedIndex < findings.length - 1) {
      const next = findings[selectedIndex + 1];
      setSelectedFindingId(next.findingId || next.id || `f-${selectedIndex + 2}`);
    }
  };

  const handleEnterOnFinding = () => {
    detailTitleRef.current?.focus();
  };

  if (loading) {
    return (
      <div className="py-24 max-w-[720px] mx-auto text-center space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin mx-auto" />
        <h2 className="text-[16px] font-semibold text-[var(--text-main)]">
          Loading audit report
        </h2>
        <p className="text-[12px] font-mono text-[var(--text-muted)]">
          Resolving temporary analysis ID: {id}
        </p>
      </div>
    );
  }

  if (loadError || !contract) {
    return (
      <div className="max-w-[720px] mx-auto py-16 text-center space-y-4">
        <div className="w-10 h-10 rounded-[4px] bg-[var(--high-tint)] border border-[var(--high)] text-[var(--high)] flex items-center justify-center mx-auto">
          <AlertCircle className="w-5 h-5" />
        </div>
        <h2 className="text-[18px] font-semibold text-[var(--text-main)]">
          Audit report not found or expired
        </h2>
        <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed max-w-md mx-auto">
          {loadError || `Unable to load audit report '${id}'.`}
        </p>
        <div className="pt-2 flex items-center justify-center gap-3">
          <Link to="/analysis/new">
            <Button variant="primary" size="sm" icon={PlusCircle}>
              Start new analysis
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="secondary" size="sm">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const contractName = contract.name || contract.contractName || 'Contract.sol';
  const analysisId = contract.id || contract.analysisId || id;
  const overallRiskScore = contract.overallRiskScore ?? contract.riskScore ?? 0;
  const overallRiskLevel = contract.overallRiskLevel || contract.riskLevel || 'Low';

  return (
    <div className="space-y-6">
      {/* 1. TOP SUMMARY STRIP */}
      <AnalysisSummaryStrip
        contractName={contractName}
        analysisId={analysisId}
        overallRiskScore={overallRiskScore}
        overallRiskLevel={overallRiskLevel}
        summary={contract.summary}
        categories={contract.categories || []}
        findings={findings}
        onExport={handleDownloadReport}
        onShare={() => setShareModalOpen(true)}
        onDiscard={handleDiscardAndNew}
        exportingPdf={downloadingPdf}
        exportingDocx={downloadingDocx}
        discarding={discarding}
      />

      {/* 2. STATUTORY SAFETY NOTICE & HELD-OUT TEST BENCHMARK */}
      <div className="rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] p-4 text-[12px] text-[var(--text-secondary)] space-y-3">
        <div className="flex items-start gap-2.5">
          <Shield className="w-4 h-4 text-[var(--text-muted)] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold text-[var(--text-main)]">
                CRITICAL NOTICE: Absence of Findings is NOT Proof of Contract Safety
              </span>
              <span className="text-[11px] font-mono text-[var(--text-muted)]">
                Checkpoint: {contract.metadata?.checkpointName || contract.modelDisclosures?.checkpointName || 'legal_bert_v3.3.0'}
              </span>
            </div>
            <p className="leading-relaxed text-[var(--text-secondary)]">
              {contract.safetyWarning || (
                'Low predicted risk scores or the absence of detected findings do NOT constitute proof that a smart contract is safe, compliant, or free from operational legal hazards. This prototype Legal-BERT multi-label model was trained on a small dataset (N=44). In the held-out real-source test split (N=7), categories Privacy, Liability, and Payment / Financial had zero positive examples (inconclusive support).'
              )}
            </p>
          </div>
        </div>

        {/* Experiment Test Benchmark Table */}
        {contract.testEvaluationReport && (
          <div className="pt-2 border-t border-[var(--border)] space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-semibold text-[var(--text-main)]">
                Held-Out Real-Source Test Split Benchmark (N=7 Contracts, 35 Decisions)
              </span>
              <span className="font-mono text-[var(--text-muted)]">
                Baseline TF-IDF Macro F1: 0.1600 vs Legal-BERT: 0.0000
              </span>
            </div>
            <div className="overflow-x-auto border border-[var(--border)] rounded-[3px] bg-[var(--surface)]">
              <table className="w-full text-left text-[11px] font-mono tnum">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--surface-subtle)] text-[var(--text-muted)]">
                    <th className="p-2">Category</th>
                    <th className="p-2">Pos / Neg</th>
                    <th className="p-2">TP / FN / TN</th>
                    <th className="p-2">Precision</th>
                    <th className="p-2">Recall</th>
                    <th className="p-2">F1</th>
                    <th className="p-2">Support Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)] text-[var(--text-secondary)]">
                  {contract.testEvaluationReport.categoryBreakdown?.map((cat, idx) => (
                    <tr key={idx} className="hover:bg-[var(--surface-subtle)]">
                      <td className="p-2 font-medium text-[var(--text-main)]">{cat.category}</td>
                      <td className="p-2">{cat.testPositives} / {cat.testNegatives}</td>
                      <td className="p-2">{cat.truePositives} / {cat.falseNegatives} / {cat.trueNegatives}</td>
                      <td className="p-2">{cat.precision.toFixed(4)}</td>
                      <td className="p-2">{cat.recall.toFixed(4)}</td>
                      <td className="p-2">{cat.f1.toFixed(4)}</td>
                      <td className="p-2">
                        <span className={`px-1.5 py-0.5 rounded-[2px] text-[10px] border ${
                          cat.supportStatus.includes('inconclusive')
                            ? 'bg-[var(--surface-subtle)] text-[var(--text-muted)] border-[var(--border)]'
                            : 'bg-[var(--critical-tint)] text-[var(--critical)] border-[var(--critical)]'
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

      {/* 3. MOBILE SEGMENTED CONTROL (< 768px) */}
      <div className="md:hidden flex border-b border-[var(--border)] mb-2" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={mobileActiveZone === 'findings'}
          onClick={() => setMobileActiveZone('findings')}
          className={`flex-1 py-2 text-center text-xs font-medium border-b-2 transition-colors ${
            mobileActiveZone === 'findings'
              ? 'border-[var(--accent)] text-[var(--text-main)] font-semibold'
              : 'border-transparent text-[var(--text-secondary)]'
          }`}
        >
          Findings ({findings.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mobileActiveZone === 'source'}
          onClick={() => setMobileActiveZone('source')}
          className={`flex-1 py-2 text-center text-xs font-medium border-b-2 transition-colors ${
            mobileActiveZone === 'source'
              ? 'border-[var(--accent)] text-[var(--text-main)] font-semibold'
              : 'border-transparent text-[var(--text-secondary)]'
          }`}
        >
          Source
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mobileActiveZone === 'details'}
          onClick={() => setMobileActiveZone('details')}
          className={`flex-1 py-2 text-center text-xs font-medium border-b-2 transition-colors ${
            mobileActiveZone === 'details'
              ? 'border-[var(--accent)] text-[var(--text-main)] font-semibold'
              : 'border-transparent text-[var(--text-secondary)]'
          }`}
        >
          Details
        </button>
      </div>

      {/* TABLET OUTLINE TOGGLE (768px - 1199px) */}
      <div className="hidden md:flex xl:hidden items-center justify-between py-1">
        <Button
          variant="secondary"
          size="sm"
          icon={ListFilter}
          onClick={() => setTabletDrawerOpen((prev) => !prev)}
        >
          {tabletDrawerOpen ? 'Hide outline' : `Show findings outline (${findings.length})`}
        </Button>
        <span className="text-[12px] text-[var(--text-muted)] font-mono">
          Selected: {currentFinding?.title || 'None'}
        </span>
      </div>

      {/* TABLET DRAWER (when open on 768-1199px) */}
      {tabletDrawerOpen && (
        <div className="hidden md:block xl:hidden p-3 border border-[var(--border)] rounded-[4px] bg-[var(--surface)] shadow-md mb-4">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--border)]">
            <span className="font-semibold text-xs text-[var(--text-main)]">Review Outline</span>
            <button
              type="button"
              onClick={() => setTabletDrawerOpen(false)}
              className="p-1 rounded-[3px] text-[var(--text-muted)] hover:text-[var(--text-main)]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <FindingsOutline
            findings={findings}
            selectedFindingId={selectedFindingId}
            onSelectFinding={handleSelectFinding}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            onEnterPress={handleEnterOnFinding}
          />
        </div>
      )}

      {/* ============================================================ */}
      {/* 4. THE THREE-ZONE REVIEW WORKSPACE                           */}
      {/* ============================================================ */}
      <section
        className="w-full grid grid-cols-1 md:grid-cols-12 gap-4 items-start"
        aria-label="Contract review workspace"
      >
        {/* ZONE 1: Left Outline & Findings List (Desktop >= 1200px) */}
        <div className="hidden xl:block xl:col-span-3">
          <FindingsOutline
            findings={findings}
            selectedFindingId={selectedFindingId}
            onSelectFinding={handleSelectFinding}
            selectedCategory={selectedCategory}
            onSelectCategory={setSelectedCategory}
            onEnterPress={handleEnterOnFinding}
          />
        </div>

        {/* MOBILE ZONE 1: Shown only when mobile tab is 'findings' */}
        {mobileActiveZone === 'findings' && (
          <div className="md:hidden col-span-1">
            <FindingsOutline
              findings={findings}
              selectedFindingId={selectedFindingId}
              onSelectFinding={handleSelectFinding}
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
              onEnterPress={handleEnterOnFinding}
            />
          </div>
        )}

        {/* ZONE 2: Center Solidity Source Viewer */}
        <div
          className={`col-span-1 ${
            mobileActiveZone !== 'source' ? 'hidden md:block' : ''
          } md:col-span-7 xl:col-span-6`}
        >
          <CodeViewer
            code={contract.solidityCode || ''}
            findings={findings}
            selectedFindingId={selectedFindingId}
            onSelectFinding={handleSelectFinding}
            filename={contractName}
          />
        </div>

        {/* ZONE 3: Right Annotation / Detail Panel */}
        <div
          className={`col-span-1 ${
            mobileActiveZone !== 'details' ? 'hidden md:block' : ''
          } md:col-span-5 xl:col-span-3`}
        >
          <FindingDetailPanel
            finding={currentFinding}
            totalFindings={findings.length}
            currentIndex={selectedIndex >= 0 ? selectedIndex : 0}
            onPrevious={handlePreviousFinding}
            onNext={handleNextFinding}
            onJumpToLines={() => {
              if (window.innerWidth < 768) {
                setMobileActiveZone('source');
              }
            }}
            titleRef={detailTitleRef}
          />
        </div>
      </section>

      {/* MOBILE STICKY BOTTOM BAR (< 768px) */}
      <div className="md:hidden sticky bottom-0 z-30 p-2.5 bg-[var(--surface-raised)] border-t border-[var(--border)] shadow-lg flex items-center justify-between text-xs font-mono">
        <span className="text-[var(--text-secondary)] truncate mr-2">
          Finding {selectedIndex + 1} of {findings.length}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={handlePreviousFinding}
            disabled={selectedIndex <= 0}
            className="h-[28px] px-2 text-xs"
          >
            Prev
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleNextFinding}
            disabled={selectedIndex >= findings.length - 1}
            className="h-[28px] px-2 text-xs"
          >
            Next
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setMobileActiveZone('details')}
            className="h-[28px] px-2 text-xs"
          >
            Details
          </Button>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 5. SECONDARY ANALYSIS SECTIONS (XAI, MATRIX, ASSISTANT)     */}
      {/* ============================================================ */}
      <div className="pt-6 border-t border-[var(--border)] space-y-4">
        {/* Underlined Section Tabs */}
        <div className="border-b border-[var(--border)] flex items-center gap-6 overflow-x-auto" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeSecondaryTab === 'xai'}
            onClick={() => setActiveSecondaryTab('xai')}
            className={`nav-tab-underlined flex items-center gap-2 cursor-pointer pb-2.5 text-[14px] ${
              activeSecondaryTab === 'xai'
                ? 'text-[var(--text-main)] font-semibold border-b-2 border-[var(--accent)]'
                : 'text-[var(--text-secondary)]'
            }`}
          >
            <Layers className="w-4 h-4" />
            XAI Explanations (SHAP & LIME)
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeSecondaryTab === 'recommendations'}
            onClick={() => setActiveSecondaryTab('recommendations')}
            className={`nav-tab-underlined flex items-center gap-2 cursor-pointer pb-2.5 text-[14px] ${
              activeSecondaryTab === 'recommendations'
                ? 'text-[var(--text-main)] font-semibold border-b-2 border-[var(--accent)]'
                : 'text-[var(--text-secondary)]'
            }`}
          >
            <Lightbulb className="w-4 h-4" />
            Remediation & Compliance
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeSecondaryTab === 'assistant'}
            onClick={() => setActiveSecondaryTab('assistant')}
            className={`nav-tab-underlined flex items-center gap-2 cursor-pointer pb-2.5 text-[14px] ${
              activeSecondaryTab === 'assistant'
                ? 'text-[var(--text-main)] font-semibold border-b-2 border-[var(--accent)]'
                : 'text-[var(--text-secondary)]'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            AI Legal Assistant
          </button>
        </div>

        {/* Tab 1: XAI Deep-Dive */}
        {activeSecondaryTab === 'xai' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ShapChart explanations={contract.shapValues || contract.shapExplanations || contract.xai?.tokenAttributions || []} />
            <LimeExplanation explanations={contract.limeExplanations || []} />
          </div>
        )}

        {/* Tab 2: Recommendations & Statutory Compliance Matrix */}
        {activeSecondaryTab === 'recommendations' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RecommendationCard recommendations={contract.recommendations || []} />
            <ComplianceMatrix matrix={contract.complianceMatrix || []} />
          </div>
        )}

        {/* Tab 3: AI Legal Assistant */}
        {activeSecondaryTab === 'assistant' && (
          <div className="max-w-[720px]">
            <LegalChatAssistant contractId={analysisId} contractName={contractName} />
          </div>
        )}
      </div>

      {/* Share Modal */}
      <Modal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        title="Share Audit Report"
        subtitle={`Audit results for ${contractName}`}
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
        <div className="space-y-4 text-[13px]">
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Direct Audit URL
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={window.location.href}
                className="w-full bg-[var(--surface-subtle)] border border-[var(--border-strong)] rounded-[4px] text-xs font-mono text-[var(--text-main)] px-3 py-2 select-all focus-ring"
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
          <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
            Shared URL points to this local session. Full reports can also be exported as PDF or Word DOCX.
          </p>
        </div>
      </Modal>
    </div>
  );
};

export default AnalysisResult;
