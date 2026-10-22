import { Link } from 'react-router-dom';
import {
  Cpu,
  Layers,
  FileCode,
  ArrowRight,
  Lock,
  Ban,
  FileCheck2,
  Scale,
  CreditCard,
} from 'lucide-react';
import { APP_NAME } from '../utils/constants';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

const Landing = () => {
  return (
    <div className="flex flex-col w-full">
      {/* ============================================================ */}
      {/* 1. HERO SECTION                                              */}
      {/* ============================================================ */}
      <section className="relative pt-16 pb-20 md:pt-24 md:pb-32 border-b border-slate-800/60 overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <div className="inline-flex items-center gap-2 mb-6">
              <Badge variant="info" size="md">
                Phase 1 Open Access • No Account Required
              </Badge>
              <span className="text-xs text-slate-400 font-mono">Pre-Deployment Decision Support</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-100 leading-tight">
              Automated Legal-Risk Assessment for{' '}
              <span className="text-blue-500">Solidity</span> Smart Contracts
            </h1>

            <p className="mt-6 text-base sm:text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
              {APP_NAME} leverages fine-tuned Legal-BERT multi-label classification paired with neural embedding gradient saliency to evaluate potential legal, termination, and financial operational hazards before irreversible blockchain deployment.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5">
              <Link to="/analysis/new" className="w-full sm:w-auto">
                <Button variant="primary" size="lg" icon={FileCode} className="w-full sm:w-auto shadow-lg shadow-blue-600/20">
                  Audit Smart Contract (No Login Required)
                </Button>
              </Link>
              <a href="#pipeline" className="w-full sm:w-auto">
                <Button variant="secondary" size="lg" icon={ArrowRight} iconPosition="right" className="w-full sm:w-auto">
                  How It Works
                </Button>
              </a>
            </div>
          </div>

          {/* Interactive UI Mock Preview */}
          <div className="max-w-4xl mx-auto rounded-xl border border-slate-800 bg-slate-900/90 shadow-2xl shadow-black/60 overflow-hidden">
            {/* Mock Window Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800 text-xs text-slate-400 font-mono">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                <span className="ml-2 text-slate-400">EscrowSettlement.sol — Legal-Risk Audit</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Legal-BERT + SHAP
                </span>
              </div>
            </div>

            {/* Split Preview: Code & Explanation */}
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800 font-mono text-xs">
              {/* Code Pane */}
              <div className="p-4 bg-slate-950/40 text-slate-300 overflow-x-auto space-y-1">
                <div className="text-slate-500">// Pragma & Contract Declaration</div>
                <div><span className="text-blue-400">contract</span> EscrowSettlement &#123;</div>
                <div className="pl-4 text-slate-400">address payable public owner;</div>
                <div className="pl-4 text-slate-400">bool public locked = false;</div>
                <br />
                <div className="text-slate-500">// High-risk unilateral termination detected</div>
                <div className="pl-4 bg-orange-950/30 border-l-2 border-orange-500 py-1 px-2 rounded-r">
                  <span className="text-purple-400">function</span> <span className="text-amber-300">emergencyKill</span>() <span className="text-blue-400">external</span> &#123;
                  <div className="pl-4 text-slate-300">require(msg.sender == owner);</div>
                  <div className="pl-4 text-orange-300 font-semibold">selfdestruct(owner);</div>
                  <div>&#125;</div>
                </div>
                <br />
                <div className="pl-4 text-slate-400">function releaseFunds() external &#123; ... &#125;</div>
                <div>&#125;</div>
              </div>

              {/* XAI Analysis Pane */}
              <div className="p-5 bg-slate-900/60 flex flex-col justify-between space-y-4 font-sans">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      Legal Risk Classification
                    </span>
                    <Badge riskLevel="High" size="sm" dot />
                  </div>
                  <h4 className="text-sm font-medium text-slate-100 mb-1">
                    Unilateral Termination & Asset Seizure
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Legal-BERT identified clause semantics matching unfair contract terms under statutory consumer protections.
                  </p>
                </div>

                <div className="space-y-2 border-t border-slate-800/80 pt-3">
                  <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>SHAP Token Attribution</span>
                    <span className="text-orange-400 font-mono">+0.68 impact</span>
                  </div>
                  <div className="space-y-1 font-mono text-[11px]">
                    <div className="flex justify-between items-center bg-slate-950/60 px-2 py-1 rounded">
                      <span className="text-orange-300">selfdestruct(owner)</span>
                      <span className="text-orange-400">+0.42</span>
                    </div>
                    <div className="flex justify-between items-center bg-slate-950/60 px-2 py-1 rounded">
                      <span className="text-amber-300">require(msg.sender == owner)</span>
                      <span className="text-amber-400">+0.26</span>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-950/20 border border-blue-900/40 rounded-lg p-2.5 text-xs text-blue-300 flex items-center justify-between">
                  <span>Recommendation: Multi-sig or time-locked withdrawal</span>
                  <ArrowRight className="w-3.5 h-3.5 shrink-0" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 2. THE PROBLEM: BEYOND CODE VULNERABILITIES                  */}
      {/* ============================================================ */}
      <section className="py-20 border-b border-slate-800/60 bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-14">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">
              Why Smart Contracts Need Legal & Compliance Auditing
            </h2>
            <p className="mt-3 text-sm sm:text-base text-slate-400 leading-relaxed">
              Existing audit tools primarily focus on technical execution flaws like reentrancy or integer overflows.
              However, technically executable code can still impose illegal terms, breach regulatory mandates, and create legal liability.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border-slate-800/80 bg-slate-900/50">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                Irreversible Blockchain Execution
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Smart contracts run autonomously once deployed. Rectifying unfair clauses, unconstitutional penalties, or compliance violations post-deployment is legally and technically arduous.
              </p>
            </Card>

            <Card className="border-slate-800/80 bg-slate-900/50">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400 mb-4">
                <Scale className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                Costly Manual Legal Review
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Specialized legal review for decentralized protocols is expensive, slow, and does not scale with rapid developer deployment cadences.
              </p>
            </Card>

            <Card className="border-slate-800/80 bg-slate-900/50">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-slate-100 mb-2">
                Pre-Deployment Decision Support
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                {APP_NAME} acts as an automated triage tool, highlighting potential legal risks and providing clear explanations before code is finalized.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 3. AI PIPELINE ARCHITECTURE                                  */}
      {/* ============================================================ */}
      <section id="pipeline" className="py-20 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <Badge variant="info" size="sm" className="mb-3">
              Research Pipeline
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">
              End-to-End Explainable AI Workflow
            </h2>
            <p className="mt-3 text-sm text-slate-400 leading-relaxed">
              From raw Solidity code to interpretable legal risk attribution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            {/* Step 1 */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 relative">
              <div className="text-xs font-mono text-blue-400 font-semibold mb-2">STEP 01</div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5 flex items-center gap-2">
                <FileCode className="w-4 h-4 text-blue-400" /> Tokenization & Prep
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Source code normalization, abstract syntax tree (AST) extraction, and token preparation suited for semantic sequence processing.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 relative">
              <div className="text-xs font-mono text-blue-400 font-semibold mb-2">STEP 02</div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" /> Legal-BERT Analysis
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Legal-BERT-based classification evaluates contract clause semantics against defined legal and regulatory taxonomies.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 relative">
              <div className="text-xs font-mono text-blue-400 font-semibold mb-2">STEP 03</div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" /> SHAP & LIME
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Dual XAI framework computes global feature contributions (SHAP) and local interpretable token segments (LIME) for complete auditing transparency.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 relative">
              <div className="text-xs font-mono text-blue-400 font-semibold mb-2">STEP 04</div>
              <h4 className="text-sm font-semibold text-slate-200 mb-1.5 flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-blue-400" /> Audit Report
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Categorized risk scores (Privacy, Termination, Compliance, Liability, Payment) paired with remediation recommendations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. THE 5 PRIMARY RISK CATEGORIES                             */}
      {/* ============================================================ */}
      <section id="risk-categories" className="py-20 border-b border-slate-800/60 bg-slate-950/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <Badge variant="warning" size="sm" className="mb-3">
              Taxonomy
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">
              The 5 Primary Legal Risk Categories
            </h2>
            <p className="mt-3 text-sm text-slate-400 leading-relaxed">
              Standardized classification targets based on prevalent smart-contract legal pitfalls.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Category 1: Privacy */}
            <Card hoverEffect className="border-slate-800/80">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">Privacy</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Identifies unintended exposure of personal data, storage of identifiable user records on public ledger states, and potential friction with data protection frameworks (e.g., GDPR right-to-be-forgotten conflicts).
              </p>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
                Pattern: Public storage of user identifiers, on-chain KYC leaks
              </div>
            </Card>

            {/* Category 2: Termination */}
            <Card hoverEffect className="border-slate-800/80">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                  <Ban className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">Termination</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Scrutinizes contract kill-switches, emergency freeze mechanisms, and unilateral contract self-destruction without proportional fallback or participant recourse.
              </p>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
                Pattern: Unilateral selfdestruct, indefinite freeze without arbitration
              </div>
            </Card>

            {/* Category 3: Legal Compliance */}
            <Card hoverEffect className="border-slate-800/80">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">Legal Compliance</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Evaluates alignment with statutory compliance expectations, consumer protection guidelines, and cross-border regulatory considerations.
              </p>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
                Pattern: Non-disclosed fee structures, anti-consumer execution rules
              </div>
            </Card>

            {/* Category 4: Liability */}
            <Card hoverEffect className="border-slate-800/80">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                  <Scale className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">Liability</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Analyzes punitive indemnification logic, complete exclusion of liability for intentional misconduct, and unbalanced risk allocation between developers and users.
              </p>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
                Pattern: Unbalanced damage waivers, excessive liquidated damages
              </div>
            </Card>

            {/* Category 5: Payment / Financial */}
            <Card hoverEffect className="border-slate-800/80 md:col-span-2 lg:col-span-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                  <CreditCard className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">Payment / Financial</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Examines token escrow lockups, unilateral withdrawal blocks, arbitrary fee modifications, and confiscation clauses that risk being ruled unenforceable.
              </p>
              <div className="text-[11px] font-mono text-slate-400 bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
                Pattern: Locked withdrawals, fee hikes exceeding agreed caps
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. EXPLAINABLE AI: SHAP & LIME                               */}
      {/* ============================================================ */}
      <section id="xai" className="py-20 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <Badge variant="info" size="sm" className="mb-3">
              Transparency by Design
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-100">
              Explainable AI (XAI) Framework
            </h2>
            <p className="mt-3 text-sm text-slate-400 leading-relaxed">
              Black-box AI is unacceptable for legal auditing. {APP_NAME} utilizes SHAP and LIME to show exactly which lines and tokens led to a risk prediction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* SHAP Explanation */}
            <Card className="border-slate-800/80 bg-slate-900/60">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono font-semibold text-blue-400 uppercase">
                  Global & Feature Attribution
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  SHAP
                </span>
              </div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">
                Shapley Additive Explanations
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Computes the game-theoretic marginal contribution of each code token to the final legal-risk classification score. Demonstrates which code constructs push the contract into higher risk categories.
              </p>
              <div className="space-y-2 font-mono text-xs bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                <div className="flex justify-between items-center text-slate-300">
                  <span>owner.transfer(balance)</span>
                  <span className="text-orange-400">+0.34 (Increases Risk)</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-orange-500 h-full rounded-full" style={{ width: '68%' }} />
                </div>

                <div className="flex justify-between items-center text-slate-300 pt-2">
                  <span>emit WithdrawalInitiated(recipient)</span>
                  <span className="text-emerald-400">-0.21 (Decreases Risk)</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: '42%' }} />
                </div>
              </div>
            </Card>

            {/* LIME Explanation */}
            <Card className="border-slate-800/80 bg-slate-900/60">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono font-semibold text-purple-400 uppercase">
                  Local Interpretability
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  LIME
                </span>
              </div>
              <h3 className="text-lg font-semibold text-slate-100 mb-2">
                Local Interpretable Model-agnostic Explanations
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Perturbs local input segments to build an interpretable surrogate model around a specific contract clause. Highlights exactly which phrases influenced the classifier's verdict in that specific context.
              </p>
              <div className="space-y-2 font-mono text-xs bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                <div className="text-slate-400">// Local clause influence</div>
                <div className="p-2 bg-slate-900 rounded border border-slate-800/80 leading-relaxed">
                  <span className="text-slate-400">modifier onlyAdmin &#123; </span>
                  <span className="bg-red-500/20 text-red-300 px-1 rounded font-semibold">
                    canOverrideTerms = true
                  </span>
                  <span className="text-slate-400">; _; &#125;</span>
                </div>
                <p className="text-[11px] font-sans text-slate-400">
                  Local perturbation highlights unilateral term modification rights as the key driver for Liability risk.
                </p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 6. CALL TO ACTION & DECISION SUPPORT DISCLAIMER              */}
      {/* ============================================================ */}
      <section className="py-20 bg-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="p-8 sm:p-12 rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/90 to-slate-950 shadow-xl">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 mb-4">
              Audit Your Smart Contracts Before Mainnet Deployment
            </h2>
            <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto mb-8 leading-relaxed">
              Upload your Solidity code to inspect legal risk levels, view token attributions, and receive actionable remediation guidance.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/analysis/new" className="w-full sm:w-auto">
                <Button variant="primary" size="lg" icon={FileCode} className="w-full sm:w-auto">
                  Start New Analysis
                </Button>
              </Link>
              <Link to="/dashboard" className="w-full sm:w-auto">
                <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                  Explore Audit Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;
