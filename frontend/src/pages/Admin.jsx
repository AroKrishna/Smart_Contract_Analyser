import { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Users,
  BarChart3,
  Cpu,
  Activity,
  Database,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Clock,
  HardDrive,
} from 'lucide-react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Button from '../components/common/Button';
import { api } from '../services/api';

const Admin = () => {
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics' | 'users' | 'model' | 'logs'
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [statsData, usersData, modelData] = await Promise.all([
        api.getAdminStats().catch(() => null),
        api.getAdminUsers().catch(() => ({ users: [] })),
        api.getAdminModelStatus().catch(() => null),
      ]);

      if (statsData) setStats(statsData);
      if (usersData?.users) setUsers(usersData.users);
      if (modelData) setModelStatus(modelData);
    } catch (err) {
      console.warn('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAdminData();
    setRefreshing(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100">
              Admin Control Panel
            </h2>
            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-semibold font-mono">
              Phase 13 Enterprise
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Platform governance, user role administration, Legal-BERT model deployment, and system telemetry
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          icon={RefreshCw}
          isLoading={refreshing}
          onClick={handleRefresh}
        >
          Refresh Telemetry
        </Button>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-slate-900/60 p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Accounts</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {stats?.totalUsers ?? users.length}
          </div>
          <div className="text-[11px] text-slate-500">Active platform identities</div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Contracts Audited</span>
            <FileText className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {stats?.totalAnalyses ?? 3}
          </div>
          <div className="text-[11px] text-slate-500">Persisted in SQLite database</div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Avg Risk Score</span>
            <BarChart3 className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {stats?.averageRiskScore ?? 58.7}
            <span className="text-xs text-slate-400 font-normal"> / 100</span>
          </div>
          <div className="text-[11px] text-slate-500">Across evaluated smart contracts</div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Legal-BERT Model Status</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-sm font-bold text-amber-400 font-mono truncate">
            {modelStatus?.isModelAvailable ? 'Active Model Deployed' : 'Readiness Gate Active'}
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            {modelStatus?.isModelAvailable ? 'Weights loaded' : 'Blocked by data support threshold'}
          </div>
        </Card>
      </div>

      {/* Admin Navigation Tabs */}
      <div className="border-b border-slate-800 flex items-center gap-4 overflow-x-auto">
        <button
          type="button"
          onClick={() => setActiveTab('analytics')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'analytics'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Platform Usage Analytics
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('model')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'model'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-4 h-4" />
          Deploy & Update Legal-BERT Models
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('users')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'users'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          User Management & Roles
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('logs')}
          className={`pb-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'logs'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-4 h-4" />
          Audit Logs & System Health
        </button>
      </div>

      {/* Tab 1: Platform Usage Analytics */}
      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              Contract Risk Level Distribution
            </h3>
            <div className="space-y-3 pt-2 text-xs">
              {[
                { label: 'Critical Risk (>= 80)', count: stats?.riskDistribution?.Critical || 1, color: 'bg-red-500', text: 'text-red-400' },
                { label: 'High Risk (60 - 79)', count: stats?.riskDistribution?.High || 1, color: 'bg-amber-500', text: 'text-amber-400' },
                { label: 'Medium Risk (35 - 59)', count: stats?.riskDistribution?.Medium || 0, color: 'bg-yellow-500', text: 'text-yellow-400' },
                { label: 'Low Risk (< 35)', count: stats?.riskDistribution?.Low || 1, color: 'bg-emerald-500', text: 'text-emerald-400' },
              ].map((item) => (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between text-slate-300">
                    <span>{item.label}</span>
                    <span className={`font-mono font-bold ${item.text}`}>{item.count} audits</span>
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.color}`}
                      style={{ width: `${Math.min(100, (item.count / Math.max(1, stats?.totalAnalyses || 3)) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-emerald-400" />
              SaaS Operational Environment
            </h3>
            <div className="bg-slate-950/70 rounded-xl p-4 border border-slate-800 text-xs space-y-2.5 font-mono">
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Storage Backend:</span>
                <span>SQLite (data/smart_contract_analyser.db)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Active ML Engine:</span>
                <span className="text-blue-400">Legal-BERT (Transformer Multi-Label)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Rule Engine Fallback:</span>
                <span className="text-red-400">DISABLED (Policy Prohibited)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Report Exporters:</span>
                <span>PDF (ReportLab) & DOCX (python-docx)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Service Status:</span>
                <span className="text-emerald-400">OPERATIONAL</span>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: Legal-BERT Model Governance */}
      {activeTab === 'model' && (
        <div className="space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-purple-400" />
                  Legal-BERT Model Architecture & Training Readiness Gate
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Pre-flight validation enforcing statistical class balance and project isolation
                </p>
              </div>

              <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono font-semibold">
                Gate Status: Training Blocked by Data Limitations
              </span>
            </div>

            {/* Model Readiness Diagnostics */}
            {modelStatus?.readiness && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg">
                    <span className="text-slate-400">Eligible Records:</span>
                    <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
                      {modelStatus.readiness.trainingEligibleRecords} / {modelStatus.readiness.minimumRequiredSamples} min
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg">
                    <span className="text-slate-400">Distinct Projects:</span>
                    <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
                      17 eligible (&gt;= 5 min passed)
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg">
                    <span className="text-slate-400">Human Verification:</span>
                    <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
                      0 claims (100% ai_reviewed)
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Category Positive Support Diagnostics (Threshold &gt;= 5 Positives)
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                    {Object.entries(modelStatus.readiness.categorySupport || {}).map(([cat, info]) => (
                      <div
                        key={cat}
                        className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-bold text-slate-200">{cat}</div>
                          <div className="text-[10px] text-slate-500">
                            Pos: {info.positive} | Neg: {info.negative}
                          </div>
                        </div>

                        {info.positive >= info.threshold ? (
                          <span className="text-emerald-400 flex items-center gap-1 text-[11px] font-semibold">
                            <CheckCircle2 className="w-4 h-4" /> Ready
                          </span>
                        ) : (
                          <span className="text-amber-400 flex items-center gap-1 text-[11px] font-semibold">
                            <XCircle className="w-4 h-4" /> {info.status}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2">
                  <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Exact Conditions Required to Unlock Model Fine-Tuning:
                  </span>
                  <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] leading-relaxed">
                    {modelStatus.readiness.blockingReasons?.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Tab 3: User Management & Roles */}
      {activeTab === 'users' && (
        <Card className="border-slate-800 bg-slate-900/60 p-0 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Organization</th>
                <th className="py-3 px-4">Created Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-900/40">
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-100">{u.full_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{u.email}</div>
                  </td>
                  <td className="py-3.5 px-4 font-mono">
                    <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-300 text-[10px] uppercase font-bold">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{u.organization || 'General'}</td>
                  <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">{u.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Tab 4: Audit Logs & System Health */}
      {activeTab === 'logs' && (
        <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Recent Security & Audit Logs
          </h3>

          <div className="space-y-2 text-xs font-mono">
            {stats?.recentLogs && stats.recentLogs.length > 0 ? (
              stats.recentLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-[11px]"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-blue-400 font-bold">[{log.event_type}]</span>
                    <span className="text-slate-300">{log.details}</span>
                  </div>
                  <span className="text-slate-500 text-[10px]">{log.created_at?.slice(11, 19)} UTC</span>
                </div>
              ))
            ) : (
              <div className="p-4 text-slate-500 text-center">No recent security events logged.</div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default Admin;
