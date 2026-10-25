import { Link, useLocation } from 'react-router-dom';
import { Menu, PlusCircle, ShieldAlert } from 'lucide-react';
import Button from '../common/Button';

const DashboardNavbar = ({ onOpenSidebar }) => {
  const location = useLocation();

  const getPageTitle = (pathname) => {
    if (pathname === '/dashboard') return 'Auditor Dashboard';
    if (pathname === '/analysis/new') return 'New Contract Analysis';
    if (pathname.startsWith('/analysis/')) return 'Analysis Result';
    if (pathname === '/history') return 'Audit History';
    if (pathname === '/reports') return 'Audit Reports';
    if (pathname === '/settings') return 'Workspace Settings';
    return 'Dashboard';
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-4 sm:px-6 backdrop-blur-md">
      {/* Left: Mobile Sidebar Toggle & Page Title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenSidebar}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 md:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-base font-semibold text-slate-100">
            {getPageTitle(location.pathname)}
          </h1>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Pre-deployment decision-support framework
          </p>
        </div>
      </div>

      {/* Right: Mode Badge & Quick New Analysis Action */}
      <div className="flex items-center gap-3">
        {/* Responsible auditing reminder badge */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
          <ShieldAlert className="w-3.5 h-3.5 text-blue-400" />
          <span>Decision Support Mode</span>
        </div>

        {location.pathname !== '/analysis/new' && (
          <Link to="/analysis/new">
            <Button variant="primary" size="sm" icon={PlusCircle}>
              New Analysis
            </Button>
          </Link>
        )}
      </div>
    </header>
  );
};

export default DashboardNavbar;
