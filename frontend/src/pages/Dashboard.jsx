import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileCheck,
  Activity,
  AlertTriangle,
  ShieldCheck,
  Plus,
  ArrowRight,
} from 'lucide-react';
import StatCard from '../components/dashboard/StatCard';
import RiskOverview from '../components/dashboard/RiskOverview';
import RecentAnalysis from '../components/dashboard/RecentAnalysis';
import Button from '../components/common/Button';
import { api } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentAnalyses, setRecentAnalyses] = useState([]);

  useEffect(() => {
    let isCancelled = false;

    async function fetchStats() {
      try {
        const data = await api.getUserStats();
        if (!isCancelled && data) {
          setStats(data);
          if (data.recentAnalyses && data.recentAnalyses.length > 0) {
            setRecentAnalyses(data.recentAnalyses);
          }
        }
      } catch (err) {
        console.warn('Failed to load local dashboard stats:', err);
      }
    }

    fetchStats();

    return () => {
      isCancelled = true;
    };
  }, []);

  const activeStats = stats || {
    totalAnalyzed: 0,
    averageRiskScore: 0,
    highRiskCount: 0,
    lowRiskCount: 0,
  };
  const activeRecent = recentAnalyses || [];

  return (
    <div className="space-y-6">
      {/* 1. Header & Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[12px] font-mono text-[var(--text-muted)]">
            <span>Local workspace</span>
            <span>•</span>
            <span>Legal-BERT v3.3.0</span>
          </div>
          <h1 className="text-[24px] font-semibold text-[var(--text-main)] leading-tight">
            Dashboard
          </h1>
          <p className="text-[14px] text-[var(--text-secondary)]">
            Pre-deployment decision support and operational legal risk assessment for Solidity smart contracts.
          </p>
        </div>

        <div className="shrink-0 flex items-center gap-3">
          <Link to="/analysis/new">
            <Button variant="primary" size="md" icon={Plus}>
              New analysis
            </Button>
          </Link>
        </div>
      </div>

      {/* 2. Core Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Contracts Audited"
          value={activeStats.totalAnalyzed ?? 0}
          subtitle="Analyzed on this machine"
          icon={FileCheck}
          badgeText="Local"
        />

        <StatCard
          title="Average Legal Risk"
          value={`${activeStats.averageRiskScore ?? 0}/100`}
          subtitle="Cross-category average"
          icon={Activity}
          badgeText="Score"
          badgeVariant="warning"
        />

        <StatCard
          title="High Risk Flagged"
          value={activeStats.highRiskCount ?? 0}
          subtitle="Critical or High severity flags"
          icon={AlertTriangle}
          badgeText="Review"
          badgeVariant="danger"
        />

        <StatCard
          title="Low Risk Baseline"
          value={activeStats.lowRiskCount ?? 0}
          subtitle="Evaluated below hazard thresholds"
          icon={ShieldCheck}
          badgeText="Baseline"
          badgeVariant="success"
        />
      </div>

      {/* 3. Main Dashboard Content (Split) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2">
          <RecentAnalysis contracts={activeRecent} />
        </div>

        <div className="space-y-4">
          <RiskOverview />

          {/* Quick Info Box */}
          <div className="p-4 rounded-[4px] border border-[var(--border)] bg-[var(--surface)] text-[12px] text-[var(--text-secondary)] space-y-2">
            <div className="font-semibold text-[13px] text-[var(--text-main)]">
              Decision Support Notice
            </div>
            <p className="leading-relaxed">
              Legal-BERT inferences evaluate clauses against the 5 standard categories: Privacy, Termination, Legal Compliance, Liability, and Payment / Financial.
            </p>
            <div className="pt-2 border-t border-[var(--border)]">
              <Link
                to="/analysis/new"
                className="text-[12px] text-[var(--accent)] hover:underline font-medium inline-flex items-center gap-1 focus-ring"
              >
                Analyze a contract now <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
