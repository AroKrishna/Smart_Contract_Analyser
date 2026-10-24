import { Link, useLocation } from 'react-router-dom';
import { Menu, Plus } from 'lucide-react';
import Button from '../common/Button';
import SettingsPopover from './SettingsPopover';
import { APP_NAME } from '../../utils/constants';

const DashboardNavbar = ({ onOpenSidebar, contractFilename, onExportReport, canExport }) => {
  const location = useLocation();

  const getPageTitle = (pathname) => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/analysis/new') return 'New analysis';
    if (pathname.startsWith('/analysis/')) return contractFilename ? `${contractFilename}` : 'Review workspace';
    if (pathname === '/history') return 'Audit history';
    if (pathname === '/reports') return 'Audit reports';
    if (pathname === '/settings') return 'Workspace settings';
    return 'Dashboard';
  };

  const isReviewPage = location.pathname.startsWith('/analysis/') && location.pathname !== '/analysis/new';

  return (
    <header className="sticky top-0 z-30 flex h-[48px] w-full items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4 sm:px-6 select-none">
      {/* Left: Mobile menu toggle + Brand & Current file / page title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="p-1.5 rounded-[4px] text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] border border-[var(--border)] md:hidden focus-ring"
          aria-label="Open navigation menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="flex items-baseline gap-2.5 min-w-0">
          <Link
            to="/dashboard"
            className="text-[15px] font-semibold text-[var(--text-main)] hover:text-[var(--accent)] transition-colors shrink-0 focus-ring"
          >
            {APP_NAME}
          </Link>
          <span className="text-[var(--border-strong)] hidden sm:inline select-none">/</span>
          <span className="text-[13px] text-[var(--text-muted)] truncate font-normal">
            {getPageTitle(location.pathname)}
          </span>
        </div>
      </div>

      {/* Right: Actions, Export (when available), and Settings Popover */}
      <div className="flex items-center gap-2 shrink-0">
        {/* If on review page and export is supported */}
        {isReviewPage && canExport && onExportReport && (
          <div className="hidden sm:flex items-center gap-1.5">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onExportReport('PDF')}
              className="text-xs"
            >
              Export PDF
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onExportReport('DOCX')}
              className="text-xs"
            >
              Export DOCX
            </Button>
          </div>
        )}

        {/* Quick New Analysis Action if not currently creating an analysis */}
        {location.pathname !== '/analysis/new' && (
          <Link to="/analysis/new">
            <Button variant="primary" size="sm" icon={Plus}>
              New analysis
            </Button>
          </Link>
        )}

        {/* Settings Popover Control */}
        <SettingsPopover />
      </div>
    </header>
  );
};

export default DashboardNavbar;
