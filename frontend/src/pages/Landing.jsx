import { Link } from 'react-router-dom';
import {
  FileCode,
  ArrowRight,
  Layers,
  Lock,
  Ban,
  FileCheck2,
  Scale,
  CreditCard,
} from 'lucide-react';
import { APP_NAME } from '../utils/constants';
import Button from '../components/common/Button';
import Card from '../components/common/Card';

const Landing = () => {
  return (
    <div className="flex flex-col w-full text-[var(--text-main)]">
      {/* 1. HERO SECTION: Calm, clear statement, single primary action */}
      <section id="overview" className="border-b border-[var(--border)] py-16 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[720px] mx-auto space-y-5 text-left">
          <div className="inline-flex items-center gap-2 text-[12px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            <span>Pre-Deployment Decision Support</span>
            <span>•</span>
            <span>Legal-BERT v3.3.0</span>
          </div>

          <h1 className="text-[32px] sm:text-[40px] font-bold tracking-tight text-[var(--text-main)] leading-tight">
            Solidity contract review, focused on operational risk.
          </h1>

          <p className="text-[15px] sm:text-[16px] text-[var(--text-secondary)] leading-relaxed">
            {APP_NAME} answers four questions before deployment: how risky is this contract, where in the source is the issue, why was it flagged, and what could be changed.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link to="/analysis/new">
              <Button variant="primary" size="lg" icon={FileCode}>
                Analyze a contract
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="secondary" size="lg">
                View dashboard
              </Button>
            </Link>
          </div>

          <p className="text-[12px] text-[var(--text-muted)] pt-1">
            Runs 100% locally. Source code never leaves your device.
          </p>
        </div>
      </section>

      {/* 2. THE 4 QUESTIONS (Core Philosophy) */}
      <section className="border-b border-[var(--border)] py-12 sm:py-16 px-4 sm:px-6 lg:px-8 bg-[var(--surface)]">
        <div className="max-w-[1000px] mx-auto space-y-8">
          <div className="max-w-[720px]">
            <h2 className="text-[20px] font-semibold text-[var(--text-main)]">
              Organized around four practical questions
            </h2>
            <p className="text-[14px] text-[var(--text-secondary)] mt-1">
              Every layout decision shortens the path between these answers.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-2">
              <div className="font-mono text-[11px] font-bold uppercase text-[var(--accent)]">
                01. Severity
              </div>
              <h3 className="text-[15px] font-semibold text-[var(--text-main)]">
                How risky is this contract?
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Overall score (0–100) and risk level word paired with severity shape.
              </p>
            </div>

            <div className="p-4 rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-2">
              <div className="font-mono text-[11px] font-bold uppercase text-[var(--accent)]">
                02. Location
              </div>
              <h3 className="text-[15px] font-semibold text-[var(--text-main)]">
                Where is the issue?
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Highlighted line ranges in the source viewer with gutter markers and edge styles.
              </p>
            </div>

            <div className="p-4 rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-2">
              <div className="font-mono text-[11px] font-bold uppercase text-[var(--accent)]">
                03. Reason
              </div>
              <h3 className="text-[15px] font-semibold text-[var(--text-main)]">
                Why was it flagged?
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Clause evidence, risk rationale, and SHAP/LIME token attribution.
              </p>
            </div>

            <div className="p-4 rounded-[4px] border border-[var(--border)] bg-[var(--surface-subtle)] space-y-2">
              <div className="font-mono text-[11px] font-bold uppercase text-[var(--accent)]">
                04. Remediation
              </div>
              <h3 className="text-[15px] font-semibold text-[var(--text-main)]">
                What should I change?
              </h3>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Safer implementation guidance and statutory consumer protection notes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. 5 RISK CATEGORIES TAXONOMY */}
      <section id="categories" className="border-b border-[var(--border)] py-12 sm:py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <div className="max-w-[720px]">
            <h2 className="text-[20px] font-semibold text-[var(--text-main)]">
              5 Primary Legal Risk Categories
            </h2>
            <p className="text-[14px] text-[var(--text-secondary)] mt-1">
              Evaluated against multi-label classification standards.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card className="space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <Ban className="w-4 h-4 text-[var(--high)]" />
                <span>Termination</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Unilateral emergency destruction (selfdestruct), withdrawal holds, and unconstrained administrative pause.
              </p>
            </Card>

            <Card className="space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <CreditCard className="w-4 h-4 text-[var(--high)]" />
                <span>Payment / Financial</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Arbitrary fee adjustment without timelocks, unilateral collateral liquidation, and unbalanced revenue distribution.
              </p>
            </Card>

            <Card className="space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <Scale className="w-4 h-4 text-[var(--medium)]" />
                <span>Liability</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Total disclaimers of settlement delay, user indemnity clauses, and unilateral dispute resolution terms.
              </p>
            </Card>

            <Card className="space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <FileCheck2 className="w-4 h-4 text-[var(--accent)]" />
                <span>Legal Compliance</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                Consumer protection standards, unfair contract terms directives, and statutory regulatory alignment.
              </p>
            </Card>

            <Card className="space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <Lock className="w-4 h-4 text-[var(--low)]" />
                <span>Privacy</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                On-chain storage of personal identifiable information (PII) and GDPR Article 17 tension with immutability.
              </p>
            </Card>

            <Card className="space-y-2 bg-[var(--surface-subtle)]">
              <div className="flex items-center gap-2 font-semibold text-[14px] text-[var(--text-main)]">
                <Layers className="w-4 h-4 text-[var(--accent)]" />
                <span>Explainability (XAI)</span>
              </div>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
                SHAP Shapley values and LIME linear surrogate regression weights showing token-level influence.
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* 4. CALL TO ACTION */}
      <section className="py-12 sm:py-16 px-4 sm:px-6 lg:px-8 bg-[var(--surface)] text-left">
        <div className="max-w-[720px] mx-auto space-y-4">
          <h2 className="text-[20px] font-semibold text-[var(--text-main)]">
            Ready to review a Solidity smart contract?
          </h2>
          <p className="text-[14px] text-[var(--text-secondary)] leading-relaxed">
            Upload your Solidity source code to inspect operational hazards with line-linked findings and model explanations.
          </p>
          <div className="pt-2">
            <Link to="/analysis/new">
              <Button variant="primary" size="lg" icon={ArrowRight} iconPosition="right">
                Start new analysis
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;
