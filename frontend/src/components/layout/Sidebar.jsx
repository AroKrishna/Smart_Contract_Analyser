import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Clock,
  FileText,
  Settings,
  X,
  Shield,
} from 'lucide-react';
import { APP_NAME } from '../../utils/constants';

const Sidebar = ({ isOpen, onClose }) => {
  const mainNavigation = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'New analysis', to: '/analysis/new', icon: PlusCircle },
    { name: 'Audit history', to: '/history', icon: Clock },
    { name: 'Audit reports', to: '/reports', icon: FileText },
  ];

  const secondaryNavigation = [
    { name: 'Settings', to: '/settings', icon: Settings },
  ];

  const navLinkClass = ({ isActive }) =>
    `flex items-center gap-3 px-3 py-2 text-[14px] rounded-[3px] transition-colors focus-ring ${
      isActive
        ? 'bg-[var(--accent-tint)] text-[var(--accent)] font-semibold border-l-[3px] border-[var(--accent)] -ml-[1px]'
        : 'text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] font-normal border-l-[3px] border-transparent -ml-[1px]'
    }`;

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-xs md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-[220px] border-r border-[var(--border)] bg-[var(--surface)] flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Sidebar navigation"
      >
        {/* Brand Header (48px matching header height) */}
        <div className="flex items-center justify-between h-[48px] px-4 border-b border-[var(--border)]">
          <Link
            to="/dashboard"
            onClick={onClose}
            className="flex items-center gap-2 text-[var(--text-main)] focus-ring"
          >
            <Shield className="w-4 h-4 text-[var(--accent)] shrink-0" />
            <span className="font-semibold text-[14px] tracking-tight text-[var(--text-main)] truncate">
              {APP_NAME}
            </span>
          </Link>

          {/* Close button for mobile */}
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-[3px] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] md:hidden focus-ring cursor-pointer"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Navigation */}
        <div className="flex-1 px-2.5 py-4 space-y-6 overflow-y-auto">
          <div>
            <div className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Workspace
            </div>
            <nav className="space-y-0.5" aria-label="Main Navigation">
              {mainNavigation.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.name}
                    to={item.to}
                    onClick={onClose}
                    className={navLinkClass}
                  >
                    <Icon className="w-4 h-4 shrink-0 text-current" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Preferences
            </div>
            <nav className="space-y-0.5" aria-label="Preferences Navigation">
              {secondaryNavigation.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.name}
                    to={item.to}
                    onClick={onClose}
                    className={navLinkClass}
                  >
                    <Icon className="w-4 h-4 shrink-0 text-current" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Bottom Local Session Status */}
        <div className="p-3 border-t border-[var(--border)] bg-[var(--surface-subtle)] text-[11px] text-[var(--text-muted)]">
          <div className="flex items-center justify-between">
            <span className="font-medium text-[var(--text-secondary)]">Single-User</span>
            <span className="inline-flex items-center gap-1 font-mono text-[var(--low)] font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--low)]" />
              Local
            </span>
          </div>
          <div className="mt-0.5 text-[10px] text-[var(--text-muted)] font-mono">
            Source stays on device
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
