import { Link, NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  LayoutDashboard,
  PlusCircle,
  Clock,
  FileText,
  Settings,
  X,
  Scale,
} from 'lucide-react';
import { APP_NAME } from '../../utils/constants';

const Sidebar = ({ isOpen, onClose }) => {

  const mainNavigation = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'New Analysis', to: '/analysis/new', icon: PlusCircle },
    { name: 'Audit History', to: '/history', icon: Clock },
    { name: 'Audit Reports', to: '/reports', icon: FileText },
  ];

  const secondaryNavigation = [
    { name: 'Workspace Settings', to: '/settings', icon: Settings },
  ];

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
      isActive
        ? 'bg-blue-600/15 text-blue-400 border border-blue-500/25'
        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
    }`;

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-xs md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 border-r border-slate-800/80 bg-slate-950 flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand / Logo Header */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-slate-800/80">
          <Link
            to="/dashboard"
            onClick={onClose}
            className="flex items-center gap-2.5 text-slate-100 group"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/30 text-blue-400 group-hover:border-blue-400 transition-colors">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-sm tracking-tight text-slate-100 leading-none">
                {APP_NAME}
              </span>
              <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                Legal-BERT Auditing
              </span>
            </div>
          </Link>

          {/* Close button for mobile */}
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-200 md:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Primary Navigation */}
        <div className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
          <div>
            <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Audit Workspace
            </div>
            <nav className="space-y-1">
              {mainNavigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.to}
                  onClick={onClose}
                  className={navLinkClass}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Preferences
            </div>
            <nav className="space-y-1">
              {secondaryNavigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.to}
                  onClick={onClose}
                  className={navLinkClass}
                >
                  <item.icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Quick Legal Taxonomy Pill */}
          <div className="p-3 mx-1 rounded-lg bg-slate-900/60 border border-slate-800/80 text-[11px] text-slate-400 space-y-1.5">
            <div className="flex items-center gap-1.5 text-slate-300 font-medium text-xs">
              <Scale className="w-3.5 h-3.5 text-blue-400" />
              <span>5 Risk Categories</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-relaxed">
              Privacy, Termination, Legal Compliance, Liability, Payment / Financial.
            </p>
          </div>
        </div>

        {/* Bottom Local Session Indicator */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950">
          <div className="flex items-center gap-2.5 p-2 rounded-lg bg-slate-900/40 border border-slate-800/60">
            <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-[10px] font-bold text-blue-300 shrink-0">
              LOC
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-medium text-slate-200 truncate">
                Local Edition
              </div>
              <div className="text-[10px] text-emerald-400 font-mono">
                100% Offline &amp; Private
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
