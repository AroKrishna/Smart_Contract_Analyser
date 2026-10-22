import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileCode,
  Upload,
  Code2,
  Play,
  AlertCircle,
  Sparkles,
  Activity,
  Cpu,
  RotateCcw,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Card from '../components/common/Card';
import Textarea from '../components/common/Textarea';
import AnalysisProgress from '../components/analysis/AnalysisProgress';
import { PIPELINE_STAGES } from '../utils/constants';
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
  const [activeTab, setActiveTab] = useState('paste'); // 'paste' | 'upload'
  const [solidityCode, setSolidityCode] = useState(SAMPLE_SOL_CODE);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'online' | 'offline'

  // Live real processing state (driven by backend job status)
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [realProgress, setRealProgress] = useState(15);
  const [realStageMessage, setRealStageMessage] = useState('Initializing pipeline...');
  const [realStageName, setRealStageName] = useState('Validating');
  const [isDragging, setIsDragging] = useState(false);

  // Check backend service status on mount
  useEffect(() => {
    let isMounted = true;
    api.checkHealth()
      .then((res) => {
        if (isMounted) {
          setBackendStatus(res.status === 'healthy' ? 'online' : 'offline');
        }
      })
      .catch(() => {
        if (isMounted) setBackendStatus('offline');
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLoadSample = (sampleKey = 'escrow') => {
    setErrorMessage('');
    if (sampleKey === 'escrow') {
      setContractName('EscrowSettlement.sol');
      setDescription('Two-party commercial settlement with emergency recovery');
      setSolidityCode(SAMPLE_SOL_CODE);
      setActiveTab('paste');
    } else {
      setContractName('TokenLendingPool.sol');
      setDescription('Collateralized token deposit and lending vault');
      setSolidityCode(SAMPLE_TOKEN_VAULT);
      setActiveTab('paste');
    }
  };

  const handleClearCode = () => {
    setSolidityCode('');
    setUploadedFileName('');
    setContractName('');
    setDescription('');
    setErrorMessage('');
  };

  const processFile = (file) => {
    if (!file) return;

    if (!file.name.endsWith('.sol')) {
      setErrorMessage('Invalid file type: Please select a valid Solidity smart contract file ending in .sol');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setErrorMessage('Selected file exceeds the 2MB size limit.');
      return;
    }

    setErrorMessage('');
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
      setErrorMessage('Please paste or upload Solidity smart contract code.');
      return;
    }

    if (solidityCode.length > 2 * 1024 * 1024) {
      setErrorMessage('Source code exceeds maximum permitted payload size of 2MB.');
      return;
    }

    // Begin live asynchronous pipeline processing
    setIsAnalyzing(true);
    setCurrentStepIndex(0);
    setRealProgress(15);
    setRealStageMessage('Validating Solidity syntax and structure...');
    setRealStageName('Validating');

    try {
      // 1. Initiate backend job
      const job = await api.startAnalysisJob(solidityCode, contractName, description);
      const jobId = job.jobId;

      // Stage index mapping for PIPELINE_STAGES (8 stages)
      const stageMap = {
        validating: 0,
        preprocessing: 1,
        tokenizing: 2,
        inferring: 3,
        synthesizing: 4,
        completed: 7,
      };

      // 2. Poll real job status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await api.getJobStatus(jobId);
          setRealProgress(statusRes.progress || 20);
          setRealStageMessage(statusRes.stageMessage || 'Executing Legal-BERT analysis...');
          setRealStageName(statusRes.stage || 'Inference');

          if (typeof stageMap[statusRes.stage] === 'number') {
            setCurrentStepIndex(stageMap[statusRes.stage]);
          }

          if (statusRes.status === 'completed') {
            clearInterval(pollInterval);
            setIsAnalyzing(false);
            const finalResult = statusRes.result;
            navigate(`/analysis/${finalResult.analysisId}`, {
              state: { analysisResult: finalResult }
            });
          } else if (statusRes.status === 'failed') {
            clearInterval(pollInterval);
            setIsAnalyzing(false);
            setErrorMessage(statusRes.error?.message || 'Analysis execution failed on the backend.');
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setIsAnalyzing(false);
          setErrorMessage(pollErr.message || 'Lost connection to analysis job.');
        }
      }, 250);

    } catch (err) {
      setIsAnalyzing(false);
      setErrorMessage(err.message || 'Analysis could not be started.');
    }
  };

  // If running the pipeline, render the real progress tracker
  if (isAnalyzing) {
    return (
      <AnalysisProgress
        currentStepIndex={currentStepIndex}
        contractName={contractName}
        progressPercent={realProgress}
        stageMessage={realStageMessage}
        stageName={realStageName}
      />
    );
  }

  const linesCount = solidityCode ? solidityCode.split('\n').length : 0;
  const charsCount = solidityCode ? solidityCode.length : 0;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100">
              New Smart Contract Audit
            </h2>
            {/* Live Backend Status Indicator */}
            {backendStatus === 'online' ? (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Legal-BERT Engine Online
              </span>
            ) : backendStatus === 'offline' ? (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[11px] font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                Backend Standby (Port 8000)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[11px] font-mono">
                <Activity className="w-3 h-3 animate-spin" />
                Checking API...
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Phase 1 No-Login Audit: Upload or paste a Solidity contract (.sol) for Legal-BERT multi-label operational hazard classification.
          </p>
        </div>

        {/* Quick Sample Selector */}
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            icon={Sparkles}
            onClick={() => handleLoadSample('escrow')}
          >
            Escrow Sample
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleLoadSample('vault')}
          >
            Lending Vault Sample
          </Button>
        </div>
      </div>

      {/* Ephemeral Notice Banner */}
      <div className="p-3.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-200 flex items-start gap-3">
        <Cpu className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-semibold text-blue-100">Phase 1 Ephemeral Session: </span>
          Uploaded contracts and generated reports are held strictly in temporary memory (30-minute retention) and are never permanently stored.
        </div>
      </div>

      {/* Error Alert Bar */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 space-y-3">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-red-200">Analysis Submission Error:</span>
              <p className="leading-relaxed">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Intake Form */}
      <form onSubmit={handleStartAnalysis} className="space-y-6">
        <Card className="border-slate-800 bg-slate-900/60 p-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contract / Project Name"
              id="contractName"
              placeholder="e.g., EscrowSettlement.sol"
              value={contractName}
              onChange={(e) => setContractName(e.target.value)}
              required
            />

            <Input
              label="Description (Optional)"
              id="description"
              placeholder="e.g., Two-party settlement escrow"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {/* Mode Switch Tabs */}
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 mb-4">
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setActiveTab('paste')}
                  className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
                    activeTab === 'paste'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Code2 className="w-4 h-4" />
                  Paste Solidity Code
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('upload')}
                  className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
                    activeTab === 'upload'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Upload className="w-4 h-4" />
                  Upload .sol File
                </button>
              </div>

              <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                <span>{linesCount} lines ({Math.round(charsCount / 1024 * 10) / 10} KB)</span>
                {solidityCode && (
                  <button
                    type="button"
                    onClick={handleClearCode}
                    className="text-slate-400 hover:text-red-400 flex items-center gap-1 transition-colors"
                  >
                    <RotateCcw className="w-3 h-3" /> Clear
                  </button>
                )}
              </div>
            </div>

            {/* Tab 1: Paste Code */}
            {activeTab === 'paste' && (
              <div className="space-y-2">
                <Textarea
                  id="soliditySource"
                  rows={14}
                  placeholder="// Paste Solidity contract source code here..."
                  value={solidityCode}
                  onChange={(e) => setSolidityCode(e.target.value)}
                  className="font-mono text-xs bg-slate-950/70 border-slate-800"
                  required
                />
              </div>
            )}

            {/* Tab 2: Upload File Dropzone */}
            {activeTab === 'upload' && (
              <div className="space-y-4">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                    isDragging
                      ? 'border-blue-400 bg-blue-950/20'
                      : 'border-slate-700 hover:border-blue-500 bg-slate-950/40'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".sol"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                  <div className="flex flex-col items-center justify-center space-y-3">
                    <div className="p-3 bg-blue-600/10 rounded-full border border-blue-500/20 text-blue-400">
                      <FileCode className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">
                        {uploadedFileName || 'Click or drag and drop your Solidity contract (.sol) here'}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        Accepts standard Solidity files (.sol up to 2MB). Ephemeral analysis without registration.
                      </p>
                    </div>
                  </div>
                </div>

                {solidityCode && (
                  <div>
                    <div className="flex items-center justify-between text-xs font-medium text-slate-400 mb-1.5">
                      <span>Loaded Source Preview ({linesCount} lines)</span>
                      <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Ready for Legal-BERT
                      </span>
                    </div>
                    <div className="bg-slate-950 rounded-lg p-3 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto border border-slate-800/80">
                      <pre>{solidityCode}</pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Submit Actions */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-400">
            Automated operational hazard assessment using Legal-BERT transformer classification.
          </div>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            icon={Play}
            className="w-full sm:w-auto shadow-lg shadow-blue-600/20"
          >
            Start Legal-BERT & XAI Analysis
          </Button>
        </div>
      </form>
    </div>
  );
};

export default NewAnalysis;
