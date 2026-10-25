import { useState } from 'react';
import {
  Check,
  Moon,
  Sun,
  Laptop,
  Shield,
  Info,
  ServerOff,
} from 'lucide-react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import { useTheme } from '../context/ThemeContext';

const Settings = () => {
  const { theme, setTheme } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState(theme);
  const [defaultFormat, setDefaultFormat] = useState(() => {
    try {
      const stored = localStorage.getItem('sma_settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.defaultFormat) return parsed.defaultFormat;
      }
    } catch (e) {
      console.warn('Failed to load local settings:', e);
    }
    return 'PDF';
  });
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setTheme(selectedTheme);
    try {
      const payload = {
        defaultFormat,
        theme: selectedTheme,
        updatedAt: new Date().toISOString(),
      };
      localStorage.setItem('sma_settings', JSON.stringify(payload));
    } catch (e) {
      console.warn('Failed to save settings:', e);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-2xl font-bold tracking-tight text-slate-100">
          Workspace Settings
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Configure local workspace appearance, report export defaults, and inspect model calibration parameters.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>Workspace preferences saved successfully to local storage.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Appearance & Theme */}
        <Card
          title="Display Theme"
          subtitle="Choose your preferred workspace color theme"
          className="border-slate-800 bg-slate-900/60 p-6 space-y-4"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => setSelectedTheme('dark')}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                selectedTheme === 'dark'
                  ? 'border-blue-500 bg-blue-500/10 text-slate-100 shadow-sm'
                  : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <div className="p-2 rounded-lg bg-slate-850 text-blue-400">
                <Moon className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold">Dark Theme</p>
                <p className="text-[10px] text-slate-400">Deep slate interface</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setSelectedTheme('light')}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                selectedTheme === 'light'
                  ? 'border-blue-500 bg-blue-500/10 text-slate-100 shadow-sm'
                  : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <div className="p-2 rounded-lg bg-slate-850 text-amber-400">
                <Sun className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold">Light Theme</p>
                <p className="text-[10px] text-slate-400">Clean light contrast</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setSelectedTheme('system')}
              className={`flex items-center gap-3 p-3 rounded-xl border text-left transition-all ${
                selectedTheme === 'system'
                  ? 'border-blue-500 bg-blue-500/10 text-slate-100 shadow-sm'
                  : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <div className="p-2 rounded-lg bg-slate-850 text-purple-400">
                <Laptop className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-semibold">System Default</p>
                <p className="text-[10px] text-slate-400">Follows OS setting</p>
              </div>
            </button>
          </div>
        </Card>

        {/* Section 2: Audit Report Defaults */}
        <Card
          title="Audit Export Defaults"
          subtitle="Preferred document format for downloaded compliance audit packages"
          className="border-slate-800 bg-slate-900/60 p-6 space-y-4"
        >
          <div className="max-w-md">
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Default Download Format
            </label>
            <select
              value={defaultFormat}
              onChange={(e) => setDefaultFormat(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 px-3 py-2.5 focus:outline-none focus:border-blue-500"
            >
              <option value="PDF">PDF (Structured Executive Audit Report)</option>
              <option value="DOCX">DOCX (Editable Legal Draft Document)</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-2">
              You can still choose either format dynamically whenever downloading an individual contract audit report.
            </p>
          </div>
        </Card>

        {/* Section 3: Honest Model Parameters Disclosure */}
        <Card
          title="Legal-BERT Model Calibration"
          subtitle="Inference parameters and decision boundaries used by the local engine"
          className="border-slate-800 bg-slate-900/60 p-6 space-y-4"
        >
          <div className="space-y-3">
            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-3">
              <Shield className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-200">
                    Decision Boundary Threshold: 50% (0.50 Sigmoid)
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Calibrated
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  The local inference engine evaluates multi-label probabilities across 5 legal taxonomies (Termination, Liability, Payment / Financial, Legal Compliance, Privacy). Neural probabilities at or above 0.50 trigger category hazard flags.
                </p>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-3">
              <Info className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
              <div className="space-y-1">
                <span className="text-xs font-semibold text-slate-200">
                  Fixed Model Weights
                </span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Inference is determined by the trained model checkpoint (<code>legal_bert_v3.3.0</code>) and SHAP/LIME token attribution pipelines. Classification boundaries are fixed to maintain deterministic reproducibility across audits.
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Section 4: Offline Local Operation Notice */}
        <Card
          title="Offline Services & Telemetry"
          subtitle="Status of external network services and notification webhooks"
          className="border-slate-800 bg-slate-900/60 p-6 space-y-4"
        >
          <div className="p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/60 flex items-start gap-3 text-xs text-slate-400">
            <ServerOff className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-slate-300 font-medium">External Email Relays Disabled</p>
              <p className="text-[11px] leading-relaxed">
                This local-first single-user application runs entirely on your machine. External email dispatchers, cloud telemetry, and third-party tracking are disabled. All contracts, analyses, and embeddings remain strictly local in your workspace SQLite database.
              </p>
            </div>
          </div>
        </Card>

        {/* Save Actions */}
        <div className="flex justify-end pt-2">
          <Button type="submit" variant="primary" size="md">
            Save Workspace Settings
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
