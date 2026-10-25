import { Link } from 'react-router-dom';
import { ShieldCheck, AlertCircle } from 'lucide-react';
import { APP_NAME } from '../../utils/constants';

const Footer = () => {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5 text-slate-100">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/30 text-blue-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <span className="font-semibold text-base tracking-tight">{APP_NAME}</span>
            </div>
            <p className="text-slate-400 text-sm max-w-md leading-relaxed">
              An Explainable AI (XAI) framework utilizing Legal-BERT-based classification with SHAP and LIME
              interpretability to analyze Solidity smart contracts for potential pre-deployment legal and compliance risks.
            </p>
          </div>

          {/* Core Architecture */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">
              Research Pipeline
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>Solidity Tokenization</li>
              <li>Legal-BERT Analysis</li>
              <li>SHAP Contribution Values</li>
              <li>LIME Local Interpretability</li>
              <li>Structured Audit Reports</li>
            </ul>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-200 mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link to="/dashboard" className="hover:text-slate-200 transition-colors">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link to="/analysis/new" className="hover:text-slate-200 transition-colors">
                  New Analysis
                </Link>
              </li>
              <li>
                <Link to="/history" className="hover:text-slate-200 transition-colors">
                  Audit History
                </Link>
              </li>
              <li>
                <Link to="/settings" className="hover:text-slate-200 transition-colors">
                  Settings
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Responsible Legal Disclaimer (Section 2) */}
        <div className="pt-6 border-t border-slate-900 bg-slate-900/30 rounded-lg p-4 mb-8">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-amber-400/90 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-400 leading-relaxed">
              <strong className="text-slate-300">Auditing Disclaimer:</strong> {APP_NAME} is an automated, pre-deployment decision-support tool. It is not intended to replace professional legal counsel, guarantee absolute legal compliance, prove legal validity, or provide definitive legal advice. Smart contract developers and organizations should always consult qualified legal professionals for official contract validation.
            </p>
          </div>
        </div>

        {/* Copyright */}
        <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 pt-4 border-t border-slate-900">
          <p>© {new Date().getFullYear()} {APP_NAME}. Built for smart contract pre-deployment compliance auditing.</p>
          <p className="mt-2 sm:mt-0">Explainable AI & Legal-BERT Research Architecture</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
