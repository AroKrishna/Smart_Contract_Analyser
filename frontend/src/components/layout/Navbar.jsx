import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, X, ArrowRight } from 'lucide-react';
import { APP_NAME } from '../../utils/constants';
import Button from '../common/Button';
import SettingsPopover from './SettingsPopover';

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[var(--border)] bg-[var(--surface)] select-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-[48px] items-center justify-between gap-4">
          {/* Logo / Brand */}
          <Link to="/" className="flex items-center gap-2 text-[var(--text-main)] focus-ring">
            <Shield className="w-4 h-4 text-[var(--accent)] shrink-0" />
            <span className="font-semibold text-[15px] tracking-tight text-[var(--text-main)]">
              {APP_NAME}
            </span>
          </Link>

          {/* Nav Links */}
          {!isAuthPage && (
            <nav className="hidden md:flex items-center gap-6 text-[13px] text-[var(--text-secondary)]" aria-label="Landing Page Navigation">
              <a href="#overview" className="hover:text-[var(--text-main)] transition-colors focus-ring">
                Overview
              </a>
              <a href="#pipeline" className="hover:text-[var(--text-main)] transition-colors focus-ring">
                AI Pipeline
              </a>
              <a href="#categories" className="hover:text-[var(--text-main)] transition-colors focus-ring">
                Risk Categories
              </a>
              <a href="#xai" className="hover:text-[var(--text-main)] transition-colors focus-ring">
                Explainability (XAI)
              </a>
            </nav>
          )}

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-2.5">
            <Link to="/dashboard">
              <Button variant="secondary" size="sm">
                Dashboard
              </Button>
            </Link>
            <Link to="/analysis/new">
              <Button variant="primary" size="sm" icon={ArrowRight} iconPosition="right">
                Analyze contract
              </Button>
            </Link>
            <SettingsPopover />
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="flex items-center gap-2 sm:hidden">
            <SettingsPopover />
            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className="p-1.5 rounded-[4px] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-main)] focus-ring"
              aria-label="Toggle mobile menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden border-t border-[var(--border)] bg-[var(--surface-raised)] px-4 py-3 space-y-3">
          <nav className="flex flex-col space-y-2 text-sm text-[var(--text-secondary)]">
            <a
              href="#overview"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 hover:text-[var(--text-main)]"
            >
              Overview
            </a>
            <a
              href="#pipeline"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 hover:text-[var(--text-main)]"
            >
              AI Pipeline
            </a>
            <a
              href="#categories"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 hover:text-[var(--text-main)]"
            >
              Risk Categories
            </a>
            <a
              href="#xai"
              onClick={() => setMobileMenuOpen(false)}
              className="py-1 hover:text-[var(--text-main)]"
            >
              Explainability (XAI)
            </a>
          </nav>
          <div className="pt-2 border-t border-[var(--border)] flex flex-col gap-2">
            <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="secondary" size="sm" className="w-full">
                Dashboard
              </Button>
            </Link>
            <Link to="/analysis/new" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="sm" className="w-full">
                Analyze contract
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
