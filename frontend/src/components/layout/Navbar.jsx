import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Menu, X, ArrowRight } from 'lucide-react';
import { APP_NAME } from '../../utils/constants';
import Button from '../common/Button';

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo / Brand */}
          <Link to="/" className="flex items-center gap-2.5 text-slate-100 hover:text-white group">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600/10 border border-blue-500/30 text-blue-400 group-hover:border-blue-400 transition-colors">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="font-semibold text-base tracking-tight text-slate-100">
              {APP_NAME}
            </span>
          </Link>

          {/* Desktop Nav Links (Visible on main landing page) */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#pipeline" className="hover:text-slate-200 transition-colors">
              AI Pipeline
            </a>
            <a href="#risk-categories" className="hover:text-slate-200 transition-colors">
              Risk Categories
            </a>
            <a href="#xai" className="hover:text-slate-200 transition-colors">
              Explainability (XAI)
            </a>
            <a href="#methodology" className="hover:text-slate-200 transition-colors">
              Auditing Scope
            </a>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            <Link to="/dashboard">
              <Button variant="secondary" size="sm">
                Dashboard
              </Button>
            </Link>
            <Link to="/analysis/new">
              <Button variant="primary" size="sm" icon={ArrowRight} iconPosition="right">
                Audit Contract
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-slate-950 px-4 py-5 space-y-4">
          <div className="flex flex-col space-y-3 text-sm text-slate-300">
            <a
              href="#pipeline"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-white py-1"
            >
              AI Pipeline
            </a>
            <a
              href="#risk-categories"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-white py-1"
            >
              Risk Categories
            </a>
            <a
              href="#xai"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-white py-1"
            >
              Explainability (XAI)
            </a>
            <a
              href="#methodology"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-white py-1"
            >
              Auditing Scope
            </a>
          </div>
            <Link to="/analysis/new" onClick={() => setMobileMenuOpen(false)} className="w-full">
              <Button variant="primary" size="md" className="w-full">
                Audit Contract
              </Button>
            </Link>
        </div>
      )}
    </header>
  );
};

export default Navbar;
