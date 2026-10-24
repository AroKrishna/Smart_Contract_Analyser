import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Settings as SettingsIcon, Sun, Moon, Laptop, ExternalLink } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

const SettingsPopover = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const popoverRef = useRef(null);
  const triggerRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const themeOptions = [
    { id: 'light', label: 'Light', icon: Sun },
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'system', label: 'System', icon: Laptop },
  ];

  return (
    <div className="relative inline-block text-left">
      <button
        ref={triggerRef}
        type="button"
        id="settings-menu-button"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-controls="settings-popover-panel"
        onClick={() => setIsOpen((prev) => !prev)}
        className="inline-flex items-center justify-center w-8 h-8 rounded-[4px] border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface-subtle)] focus-ring transition-colors"
        title="Settings & Appearance"
        aria-label="Settings and Appearance Preferences"
      >
        <SettingsIcon className="w-4 h-4" />
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          id="settings-popover-panel"
          role="dialog"
          aria-label="Application Settings"
          className="absolute right-0 mt-1.5 w-[280px] rounded-[4px] border border-[var(--border)] bg-[var(--surface-raised)] shadow-lg z-50 text-[13px] text-[var(--text-main)] divide-y divide-[var(--border)]"
        >
          {/* Header */}
          <div className="px-3.5 py-2.5 flex items-center justify-between">
            <span className="font-semibold text-[13px] text-[var(--text-main)]">
              Appearance & Settings
            </span>
            <span className="text-[11px] font-mono text-[var(--text-muted)] uppercase">
              {resolvedTheme} mode
            </span>
          </div>

          {/* Theme Selector */}
          <div className="p-3 space-y-2">
            <div className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">
              Theme Mode
            </div>
            <div className="grid grid-cols-3 gap-1 bg-[var(--surface-subtle)] p-1 rounded-[4px] border border-[var(--border)]" role="radiogroup" aria-label="Theme selector">
              {themeOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = theme === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    onClick={() => setTheme(opt.id)}
                    className={`flex flex-col items-center justify-center py-2 px-1 rounded-[3px] text-xs transition-colors focus-ring cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--surface)] text-[var(--text-main)] font-semibold shadow-xs border border-[var(--border)]'
                        : 'text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--surface)]'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 mb-1 shrink-0" />
                    <span className="text-[11px]">{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* System & Local Status Info */}
          <div className="p-3 text-[11px] text-[var(--text-muted)] leading-relaxed space-y-1">
            <div className="flex items-center justify-between">
              <span>Environment:</span>
              <span className="font-mono text-[var(--text-secondary)] font-medium">Local Single-User</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Model engine:</span>
              <span className="font-mono text-[var(--text-secondary)]">Legal-BERT v3.3.0</span>
            </div>
          </div>

          {/* Footer link to full settings */}
          <div className="p-2 bg-[var(--surface-subtle)]">
            <Link
              to="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center justify-between w-full px-2.5 py-1.5 rounded-[3px] text-xs text-[var(--accent)] hover:bg-[var(--accent-tint)] transition-colors focus-ring"
            >
              <span className="font-medium">All Workspace Settings</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPopover;
