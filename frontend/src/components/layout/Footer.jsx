import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { APP_NAME } from '../../utils/constants';

const Footer = () => {
  return (
    <footer className="w-full border-t border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] text-[13px]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2 text-[var(--text-main)]">
              <Shield className="w-4 h-4 text-[var(--accent)] shrink-0" />
              <span className="font-semibold text-[15px] tracking-tight">{APP_NAME}</span>
            </div>
            <p className="text-[var(--text-muted)] text-[12px] max-w-md leading-relaxed">
              A local-first explainable AI framework utilizing Legal-BERT classification with SHAP and LIME
              interpretability to analyze Solidity smart contracts for potential operational hazards before blockchain deployment.
            </p>
          </div>

          {/* Research Architecture */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-main)] mb-2.5">
              Research Pipeline
            </h4>
            <ul className="space-y-1.5 text-[12px] text-[var(--text-muted)]">
              <li>Solidity Syntax Parsing</li>
              <li>Legal-BERT Inference</li>
              <li>SHAP Shapley Contributions</li>
              <li>LIME Local Linear Surrogates</li>
              <li>Structured Audit Reports</li>
            </ul>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-main)] mb-2.5">
              Workspace
            </h4>
            <ul className="space-y-1.5 text-[12px] text-[var(--text-muted)]">
              <li>
                <Link to="/dashboard" className="hover:text-[var(--text-main)] transition-colors">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link to="/analysis/new" className="hover:text-[var(--text-main)] transition-colors">
                  New analysis
                </Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-[var(--text-main)] transition-colors">
                  Audit history
                </Link>
              </li>
              <li>
                <Link to="/reports" className="hover:text-[var(--text-main)] transition-colors">
                  Audit reports
                </Link>
              </li>
              <li>
                <Link to="/settings" className="hover:text-[var(--text-main)] transition-colors">
                  Settings
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-[var(--border)] flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-[var(--text-muted)]">
          <div>
            Pre-deployment decision-support framework. Absence of detected findings is not proof of contract safety.
          </div>
          <div className="font-mono">
            Legal-BERT Checkpoint: legal_bert_v3.3.0
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
