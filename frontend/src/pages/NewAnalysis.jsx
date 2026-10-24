import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileCode,
  Upload,
  Code2,
  AlertCircle,
  X,
} from 'lucide-react';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Card from '../components/common/Card';
import Textarea from '../components/common/Textarea';
import AnalysisProgress from '../components/analysis/AnalysisProgress';
import { api } from '../services/api';

const SAMPLE_SOL_CODE = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EscrowSettlement
 * @notice Two-party commercial settlement with owner emergency kill switch
 */
contract EscrowSettlement {
    address payable public owner;
    address public buyer;
    address payable public seller;
    uint256 public feeRate = 200; // 2%
    bool public locked = false;

    event PaymentReleased(address indexed to, uint256 amount);

    constructor(address _buyer, address payable _seller) payable {
        owner = payable(msg.sender);
        buyer = _buyer;
        seller = _seller;
    }

    // High Risk: Unilateral Emergency Termination
    function emergencyKill() external {
        require(msg.sender == owner, "Only owner");
        selfdestruct(owner);
    }

    // Medium Risk: Arbitrary Fee Adjustment
    function setFeeRate(uint256 newRate) external {
        require(msg.sender == owner, "Only owner");
        feeRate = newRate;
    }

    function release() external {
        require(msg.sender == buyer || msg.sender == owner, "Unauthorized");
        uint256 fee = (address(this).balance * feeRate) / 10000;
        owner.transfer(fee);
        seller.transfer(address(this).balance);
    }
}`;

const SAMPLE_TOKEN_VAULT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TokenLendingPool
 * @notice Collateralized token deposit and lending vault
 */
contract TokenLendingPool {
    address public admin;
    mapping(address => uint256) public deposits;
    uint256 public penaltyRate = 500; // 5%

    // Privacy Concern: Personal identifier stored in plaintext
    string public adminContactEmail;

    constructor(string memory _email) {
        admin = msg.sender;
        adminContactEmail = _email;
    }

    function deposit() external payable {
        require(msg.value > 0, "Zero deposit");
        deposits[msg.sender] += msg.value;
    }

    function setPenaltyRate(uint256 _newPenalty) external {
        require(msg.sender == admin, "Only admin");
        penaltyRate = _newPenalty;
    }
}`;

const NewAnalysis = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [contractName, setContractName] = useState('EscrowSettlement.sol');
  const [description, setDescription] = useState('Two-party commercial settlement with emergency recovery');
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'paste'
  const [solidityCode, setSolidityCode] = useState(SAMPLE_SOL_CODE);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'online' | 'offline' | 'model_unavailable'

  // Asynchronous progress tracking
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeJobId, setActiveJobId] = useState(null);
  const pollTimeoutRef = useRef(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [realProgress, setRealProgress] = useState(15);
  const [realStageMessage, setRealStageMessage] = useState('Initializing pipeline...');
  const [realStageName, setRealStageName] = useState('Validating');
  const [isDragging, setIsDragging] = useState(false);

  // Evaluate backend status on mount
  useEffect(() => {
    let isMounted = true;
    async function evaluateServiceStatus() {
      try {
        const healthRes = await api.checkHealth();
        if (!isMounted) return;

        if (healthRes.status === 'healthy') {
          const readyRes = await api.checkReadiness();
          if (!isMounted) return;
          if (readyRes.status === 'ready') {
            setBackendStatus('online');
          } else {
            setBackendStatus('model_unavailable');
          }
        } else if (healthRes.status === 'degraded') {
          setBackendStatus('model_unavailable');
        } else {
          setBackendStatus('offline');
        }
      } catch {
        if (isMounted) setBackendStatus('offline');
      }
    }

    evaluateServiceStatus();

    return () => {
      isMounted = false;
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  const handleLoadSample = (sampleKey = 'escrow') => {
    setErrorMessage('');
    if (sampleKey === 'escrow') {
      setContractName('EscrowSettlement.sol');
      setDescription('Two-party commercial settlement with emergency recovery');
      setSolidityCode(SAMPLE_SOL_CODE);
      setUploadedFile(null);
      setUploadedFileName('');
    } else {
      setContractName('TokenLendingPool.sol');
      setDescription('Collateralized token deposit and lending vault');
      setSolidityCode(SAMPLE_TOKEN_VAULT);
      setUploadedFile(null);
      setUploadedFileName('');
    }
  };

  const handleClearCode = () => {
    setSolidityCode('');
    setUploadedFile(null);
    setUploadedFileName('');
    setContractName('');
    setDescription('');
    setErrorMessage('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const processFile = (file) => {
    if (!file) return;

    if (!file.name.endsWith('.sol')) {
      setErrorMessage('Invalid file type: Please select a valid Solidity smart contract file ending in .sol');
      return;
    }

    if (file.size > 1024 * 1024) {
      setErrorMessage('Selected file exceeds the 1MB size limit.');
      return;
    }

    setErrorMessage('');
    setUploadedFile(file);
    setUploadedFileName(file.name);
    setContractName(file.name);

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result;
      if (typeof content === 'string') {
        setSolidityCode(content);
      }
    };
    reader.readAsText(file);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    processFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    processFile(file);
  };

  const handleStartAnalysis = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!contractName.trim()) {
      setErrorMessage('Contract name is required.');
      return;
    }

    if (!solidityCode.trim()) {
      setErrorMessage('Please add Solidity source code by uploading a .sol file or pasting code.');
      return;
    }

    if (solidityCode.length > 1024 * 1024) {
      setErrorMessage('Source code exceeds the maximum permitted payload size of 1MB.');
      return;
    }

    if (backendStatus === 'offline') {
      const activeUrl = api.getBaseUrl();
      const targetLabel = activeUrl ? `at ${activeUrl}` : 'on port 8000';
      setErrorMessage(
        `Cannot initiate analysis: Backend service is currently unreachable ${targetLabel}. ` +
        `Please ensure the local FastAPI backend is running (e.g. 'uvicorn backend.main:app --host 127.0.0.1 --port 8000').`
      );
      return;
    }

    if (backendStatus === 'model_unavailable') {
      setErrorMessage(
        'Cannot initiate analysis: Legal-BERT model checkpoint (legal_bert_v3.3.0) is not loaded on the backend. ' +
        'Please ensure weights are in analysis/models/legal_bert_v3.3.0/.'
      );
      return;
    }

    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
    }

    setIsAnalyzing(true);
    setErrorMessage('');
    setCurrentStepIndex(0);
    setRealProgress(15);
    setRealStageName('Syntax Validation');
    setRealStageMessage('Validating Solidity syntax and initializing job...');

    try {
      const idempotencyKey = `idem-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      let job;

      if (activeTab === 'upload' && uploadedFile) {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('contract_name', contractName || uploadedFile.name);
        formData.append('description', description || '');
        formData.append('idempotency_key', idempotencyKey);
        job = await api.createAnalysisJob(formData);
      } else {
        const jobPayload = {
          sourceCode: solidityCode,
          contractName: contractName || 'Contract.sol',
          description: description || '',
          idempotencyKey,
        };
        job = await api.createAnalysisJob(jobPayload);
      }

      const jobId = job.jobId;
      setActiveJobId(jobId);

      const pollInterval = 1200;
      const maxAttempts = 150;
      let attempts = 0;

      const stageMap = {
        validating: { name: 'Syntax Validation', step: 0 },
        parsing: { name: 'AST & Clause Extraction', step: 1 },
        inferring: { name: 'Neural Legal-BERT Inference', step: 3 },
        attributing: { name: 'XAI Token Attribution (SHAP/LIME)', step: 5 },
        explaining: { name: 'XAI Token Attribution (SHAP/LIME)', step: 5 },
        saving: { name: 'Synthesizing Compliance & Persistence', step: 6 },
        completed: { name: 'Audit Finalized', step: 7 },
      };

      const poll = async () => {
        try {
          const statusRes = await api.getJobStatus(jobId);
          if (typeof statusRes.progress === 'number') {
            setRealProgress(statusRes.progress);
          }
          if (statusRes.stageMessage) {
            setRealStageMessage(statusRes.stageMessage);
          }
          if (statusRes.stage && stageMap[statusRes.stage]) {
            setRealStageName(stageMap[statusRes.stage].name);
            setCurrentStepIndex(stageMap[statusRes.stage].step);
          }

          if (statusRes.status === 'completed') {
            setIsAnalyzing(false);
            const finalResult = statusRes.result || (await api.getJobResult(jobId));
            navigate(`/analysis/${finalResult.analysisId}`, {
              state: { analysisResult: finalResult },
            });
            return;
          }

          if (statusRes.status === 'cancelled') {
            setIsAnalyzing(false);
            setErrorMessage('Analysis job was cancelled.');
            return;
          }

          if (statusRes.status === 'failed') {
            setIsAnalyzing(false);
            const errDetail = statusRes.error?.message || statusRes.stageMessage || 'Analysis job failed.';
            setErrorMessage(`Analysis failed: ${errDetail}. Please verify contract syntax and retry.`);
            return;
          }

          attempts++;
          if (attempts < maxAttempts) {
            pollTimeoutRef.current = setTimeout(poll, pollInterval);
          } else {
            setIsAnalyzing(false);
            setErrorMessage('Analysis job timed out. You can retrieve completed results from Audit History.');
          }
        } catch (pollErr) {
          setIsAnalyzing(false);
          setErrorMessage(`Error checking job status: ${pollErr.message}`);
        }
      };

      pollTimeoutRef.current = setTimeout(poll, pollInterval);
    } catch (err) {
      setIsAnalyzing(false);
      setErrorMessage(err.message || 'Analysis execution failed on the backend.');
    }
  };

  const handleCancelAnalysis = async () => {
    if (activeJobId) {
      try {
        setRealStageMessage('Cancelling analysis job...');
        await api.cancelJob(activeJobId);
      } catch (err) {
        console.warn('Failed to cancel job:', err);
      }
    }
  };

  if (isAnalyzing) {
    return (
      <AnalysisProgress
        currentStepIndex={currentStepIndex}
        contractName={contractName}
        progressPercent={realProgress}
        stageMessage={realStageMessage}
        stageName={realStageName}
        onCancel={handleCancelAnalysis}
      />
    );
  }

  const linesCount = solidityCode ? solidityCode.split('\n').length : 0;
  const byteSize = solidityCode ? new Blob([solidityCode]).size : 0;
  const sizeKb = Math.round((byteSize / 1024) * 10) / 10;
  const hasContent = Boolean(solidityCode && solidityCode.trim());

  return (
    <div className="max-w-[720px] mx-auto py-2 space-y-6">
      {/* Title & Concise Subtitle */}
      <div className="space-y-1">
        <h1 className="text-[24px] font-semibold text-[var(--text-main)] leading-tight">
          New analysis
        </h1>
        <p className="text-[14px] text-[var(--text-secondary)]">
          Analyze a Solidity contract on this machine.
        </p>
      </div>

      {/* Backend Status or Missing Weights Warning */}
      {backendStatus === 'model_unavailable' && (
        <div className="p-3 rounded-[4px] bg-[var(--high-tint)] border border-[var(--high)] text-[13px] text-[var(--high)] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Model weights missing: </span>
            Legal-BERT checkpoint (legal_bert_v3.3.0) is not loaded on the backend service.
          </div>
        </div>
      )}

      {backendStatus === 'offline' && !errorMessage && (
        <div className="p-3 rounded-[4px] bg-[var(--high-tint)] border border-[var(--high)] text-[13px] text-[var(--high)] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Backend offline: </span>
            Start the local FastAPI service (<code className="font-mono text-xs">uvicorn backend.main:app --port 8000</code>).
          </div>
        </div>
      )}

      {/* Error message */}
      {errorMessage && (
        <div className="p-3.5 rounded-[4px] bg-[var(--critical-tint)] border border-[var(--critical)] text-[13px] text-[var(--critical)] space-y-1">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="font-medium leading-relaxed">{errorMessage}</div>
          </div>
        </div>
      )}

      {/* Main Form */}
      <form onSubmit={handleStartAnalysis} className="space-y-6">
        <Card className="space-y-5">
          {/* Metadata Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contract Name"
              id="contractName"
              placeholder="e.g. EscrowSettlement.sol"
              value={contractName}
              onChange={(e) => setContractName(e.target.value)}
              required
            />
            <Input
              label="Description (Optional)"
              id="description"
              placeholder="e.g. Two-party settlement escrow"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {/* Underlined Tabs: Upload file vs Paste source */}
          <div>
            <div className="flex items-center justify-between border-b border-[var(--border)] mb-4" role="tablist">
              <div className="flex gap-6">
                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === 'upload'}
                  onClick={() => setActiveTab('upload')}
                  className={`nav-tab-underlined flex items-center gap-2 cursor-pointer pb-2.5 text-[14px] ${
                    activeTab === 'upload' ? 'text-[var(--text-main)] font-semibold border-b-2 border-[var(--accent)]' : 'text-[var(--text-secondary)]'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  Upload file
                </button>

                <button
                  type="button"
                  role="tab"
                  aria-selected={activeTab === 'paste'}
                  onClick={() => setActiveTab('paste')}
                  className={`nav-tab-underlined flex items-center gap-2 cursor-pointer pb-2.5 text-[14px] ${
                    activeTab === 'paste' ? 'text-[var(--text-main)] font-semibold border-b-2 border-[var(--accent)]' : 'text-[var(--text-secondary)]'
                  }`}
                >
                  <Code2 className="w-4 h-4" />
                  Paste source
                </button>
              </div>

              {/* Quick Sample Selector */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[var(--text-muted)] text-[12px] hidden sm:inline">Load sample:</span>
                <button
                  type="button"
                  onClick={() => handleLoadSample('escrow')}
                  className="text-xs text-[var(--accent)] hover:underline cursor-pointer focus-ring px-1.5 py-0.5 rounded-[2px]"
                >
                  Escrow
                </button>
                <span className="text-[var(--border)]">|</span>
                <button
                  type="button"
                  onClick={() => handleLoadSample('vault')}
                  className="text-xs text-[var(--accent)] hover:underline cursor-pointer focus-ring px-1.5 py-0.5 rounded-[2px]"
                >
                  Lending vault
                </button>
              </div>
            </div>

            {/* TAB 1: Upload File Area */}
            {activeTab === 'upload' && (
              <div className="space-y-4">
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`min-h-[160px] rounded-[4px] border border-dashed p-6 flex flex-col items-center justify-center text-center transition-colors ${
                    isDragging
                      ? 'border-[var(--accent)] bg-[var(--accent-tint)]'
                      : 'border-[var(--border-strong)] bg-[var(--surface-subtle)] hover:border-[var(--accent)]'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".sol"
                    className="sr-only"
                    id="contract-file-upload"
                    onChange={handleFileUpload}
                  />

                  <FileCode className="w-8 h-8 text-[var(--text-secondary)] mb-2" aria-hidden="true" />

                  {uploadedFileName ? (
                    <div className="space-y-2">
                      <div className="text-[14px] font-semibold text-[var(--text-main)] font-mono">
                        {uploadedFileName}
                      </div>
                      <div className="text-[12px] text-[var(--text-muted)] font-mono tnum">
                        {sizeKb} KB • {linesCount} lines
                      </div>
                      <div className="pt-1 flex items-center justify-center gap-2">
                        <label
                          htmlFor="contract-file-upload"
                          className="inline-flex items-center justify-center h-[28px] px-3 text-xs font-medium rounded-[4px] border border-[var(--border-strong)] bg-[var(--surface)] text-[var(--text-main)] hover:bg-[var(--surface-subtle)] cursor-pointer focus-ring"
                        >
                          Change file
                        </label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          icon={X}
                          onClick={handleClearCode}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-[14px] text-[var(--text-main)] font-medium">
                        Drag and drop a Solidity contract (.sol) here
                      </div>
                      <div className="text-[12px] text-[var(--text-muted)]">
                        Up to 1MB. UTF-8 encoded Solidity source.
                      </div>
                      <div className="pt-2">
                        <label
                          htmlFor="contract-file-upload"
                          className="inline-flex items-center justify-center h-[36px] px-4 text-[14px] font-medium rounded-[4px] border border-[var(--border-strong)] bg-[var(--surface)] text-[var(--text-main)] hover:bg-[var(--surface-subtle)] cursor-pointer focus-ring"
                        >
                          Choose file
                        </label>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: Paste Code */}
            {activeTab === 'paste' && (
              <div className="space-y-2">
                <Textarea
                  id="soliditySource"
                  rows={14}
                  placeholder="// Paste Solidity contract source code here..."
                  value={solidityCode}
                  onChange={(e) => setSolidityCode(e.target.value)}
                  required
                />
              </div>
            )}

            {/* Small Read-Only Summary Once Content Exists */}
            {hasContent && (
              <div className="mt-3 p-2.5 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] flex flex-wrap items-center justify-between text-[12px] text-[var(--text-secondary)] font-mono">
                <div className="flex items-center gap-4">
                  <span>File: <strong className="text-[var(--text-main)]">{contractName || 'Contract.sol'}</strong></span>
                  <span>Lines: <strong className="text-[var(--text-main)] tnum">{linesCount}</strong></span>
                  <span>Size: <strong className="text-[var(--text-main)] tnum">{sizeKb} KB</strong></span>
                </div>
                <button
                  type="button"
                  onClick={handleClearCode}
                  className="text-xs text-[var(--text-muted)] hover:text-[var(--critical)] cursor-pointer"
                >
                  Clear source
                </button>
              </div>
            )}
          </div>
        </Card>

        {/* Submission Controls & Local Privacy Note */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={!hasContent || backendStatus === 'offline'}
              disabledReason={
                !hasContent
                  ? 'Add a Solidity file or paste source code to enable analysis.'
                  : backendStatus === 'offline'
                  ? 'Start local backend service to enable analysis.'
                  : ''
              }
            >
              Run analysis
            </Button>

            {hasContent && (
              <Button
                type="button"
                variant="tertiary"
                size="md"
                onClick={handleClearCode}
              >
                Clear source
              </Button>
            )}
          </div>

          {/* Local Processing / Privacy Note */}
          <p className="text-[12px] text-[var(--text-muted)]">
            Analysis runs locally. Source code is not sent anywhere.
          </p>
        </div>
      </form>
    </div>
  );
};

export default NewAnalysis;
