import { useState } from 'react';
import {
  Sun,
  Moon,
  Laptop,
  Check,
} from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { useTheme } from '../context/ThemeContext';

const Settings = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const [sensitivity, setSensitivity] = useState(65);
  const [alertCritical, setAlertCritical] = useState(true);
  const [alertWeekly, setAlertWeekly] = useState(false);
  const [defaultFormat, setDefaultFormat] = useState('PDF');
  const [strictMode, setStrictMode] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const themeOptions = [
    { id: 'light', label: 'Light', desc: 'Light background with high contrast dark text', icon: Sun },
    { id: 'dark', label: 'Dark', desc: 'Dark gray surface with calibrated severity tones', icon: Moon },
    { id: 'system', label: 'System', desc: 'Automatically match your operating system theme', icon: Laptop },
  ];

  return (
    <div className="max-w-[720px] mx-auto py-2 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-[24px] font-semibold text-[var(--text-main)] leading-tight">
          Settings
        </h1>
        <p className="text-[14px] text-[var(--text-secondary)]">
          Manage appearance themes, Legal-BERT model sensitivity, and audit report preferences.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-[4px] bg-[var(--low-tint)] border border-[var(--low)] text-[13px] text-[var(--low)] flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>Workspace preferences saved successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Appearance & Theme Selector */}
        <Card
          title="Appearance & Theme"
          subtitle="Choose between Light, Dark, or System mode to control the application colors"
        >
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" role="radiogroup" aria-label="Theme Mode Selection">
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
                    className={`p-3.5 rounded-[4px] border text-left flex flex-col justify-between transition-colors focus-ring cursor-pointer ${
                      isSelected
                        ? 'border-[var(--accent)] bg-[var(--accent-tint)]'
                        : 'border-[var(--border)] bg-[var(--surface-subtle)] hover:bg-[var(--surface)] hover:border-[var(--border-strong)]'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full mb-2">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-[var(--text-main)]" />
                        <span className="font-semibold text-[14px] text-[var(--text-main)]">
                          {opt.label}
                        </span>
                      </div>
                      {isSelected && (
                        <span className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                      )}
                    </div>
                    <p className="text-[12px] text-[var(--text-muted)] leading-normal">
                      {opt.desc}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="pt-2 text-[12px] text-[var(--text-muted)] font-mono">
              Active theme: <strong className="text-[var(--text-main)] capitalize">{resolvedTheme}</strong> mode
              {theme === 'system' && ' (following OS preference)'}
            </div>
          </div>
        </Card>

        {/* Section 2: AI Model Classification Threshold */}
        <Card
          title="Legal-BERT Classification Sensitivity"
          subtitle="Decision boundary threshold for multi-label operational hazard classification"
        >
          <div className="space-y-4 text-[13px]">
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[var(--text-secondary)] font-medium">
                  Decision Threshold:
                </span>
                <span className="font-mono text-[var(--accent)] font-bold text-sm tnum">
                  {sensitivity}%
                </span>
              </div>

              <input
                type="range"
                min="40"
                max="90"
                value={sensitivity}
                onChange={(e) => setSensitivity(Number(e.target.value))}
                className="w-full h-1.5 bg-[var(--surface-subtle)] rounded-[2px] appearance-none cursor-pointer accent-[var(--accent)] border border-[var(--border)]"
              />

              <div className="flex justify-between text-[11px] text-[var(--text-muted)] pt-1 font-mono tnum">
                <span>Sensitive (40%)</span>
                <span>Balanced (65%)</span>
                <span>Strict Precision (90%)</span>
              </div>
            </div>

            <div className="pt-3 border-t border-[var(--border)]">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={strictMode}
                  onChange={(e) => setStrictMode(e.target.checked)}
                  className="w-4 h-4 mt-0.5 rounded-[2px] border-[var(--border-strong)] text-[var(--accent)] focus-ring"
                />
                <div>
                  <span className="text-[13px] font-semibold text-[var(--text-main)]">
                    Strict statutory consumer protections flagging
                  </span>
                  <p className="text-[12px] text-[var(--text-muted)] mt-0.5">
                    Flags unilateral contract freezes or termination hold mechanisms regardless of threshold.
                  </p>
                </div>
              </label>
            </div>
          </div>
        </Card>

        {/* Section 3: Notification Options */}
        <Card
          title="Audit Notifications"
          subtitle="Local notification options for contract analysis completions"
        >
          <div className="space-y-3 text-[13px]">
            <label className="flex items-center justify-between p-3 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] cursor-pointer">
              <div>
                <span className="text-[13px] font-medium text-[var(--text-main)]">
                  Immediate Alert for Critical Risks
                </span>
                <p className="text-[12px] text-[var(--text-muted)]">
                  Highlight notifications when unilateral selfdestruct or unlimited fee alterations are flagged.
                </p>
              </div>
              <input
                type="checkbox"
                checked={alertCritical}
                onChange={(e) => setAlertCritical(e.target.checked)}
                className="w-4 h-4 rounded-[2px] border-[var(--border-strong)] text-[var(--accent)] focus-ring ml-3"
              />
            </label>

            <label className="flex items-center justify-between p-3 rounded-[4px] bg-[var(--surface-subtle)] border border-[var(--border)] cursor-pointer">
              <div>
                <span className="text-[13px] font-medium text-[var(--text-main)]">
                  Weekly Audit Digest
                </span>
                <p className="text-[12px] text-[var(--text-muted)]">
                  Summary digest of all Solidity contracts analyzed in the previous 7 days.
                </p>
              </div>
              <input
                type="checkbox"
                checked={alertWeekly}
                onChange={(e) => setAlertWeekly(e.target.checked)}
                className="w-4 h-4 rounded-[2px] border-[var(--border-strong)] text-[var(--accent)] focus-ring ml-3"
              />
            </label>
          </div>
        </Card>

        {/* Section 4: Export Format Default */}
        <Card
          title="Report Defaults"
          subtitle="Default document format used when triggering single-click report exports"
        >
          <div className="max-w-xs">
            <label className="block text-[12px] font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-1.5">
              Default Export Format
            </label>
            <select
              value={defaultFormat}
              onChange={(e) => setDefaultFormat(e.target.value)}
              className="w-full h-[36px] bg-[var(--surface)] border border-[var(--border-strong)] rounded-[4px] text-[14px] text-[var(--text-main)] px-3 focus-ring cursor-pointer"
            >
              <option value="PDF">PDF (Executive Decision Support)</option>
              <option value="DOCX">DOCX (Editable Audit Report)</option>
            </select>
          </div>
        </Card>

        {/* Save Action */}
        <div className="flex items-center justify-end pt-2">
          <Button type="submit" variant="primary" size="md">
            Save preferences
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
