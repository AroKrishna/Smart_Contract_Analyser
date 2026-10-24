/**
 * Smart Contract Analyser - Professional Redline Severity System
 * Adheres strictly to Section 2 of the UI Design Guide:
 * 4 channels together: Word, Shape, Line Style in Code, Edge Treatment.
 */

export const SEVERITY_CONFIG = {
  Critical: {
    level: 'Critical',
    word: 'CRITICAL',
    shape: '◆', // Filled diamond
    shapeAria: 'Critical risk filled diamond marker',
    edgeWidth: '3px',
    edgeClass: 'border-l-[3px]',
    lineStyle: 'solid',
    underlineClass: 'underline decoration-2 decoration-solid',
    cssVar: 'var(--critical)',
    tintVar: 'var(--critical-tint)',
  },
  High: {
    level: 'High',
    word: 'HIGH',
    shape: '▲', // Filled triangle
    shapeAria: 'High risk filled triangle marker',
    edgeWidth: '3px',
    edgeClass: 'border-l-[3px]',
    lineStyle: 'dashed',
    underlineClass: 'underline decoration-1 decoration-dashed',
    cssVar: 'var(--high)',
    tintVar: 'var(--high-tint)',
  },
  Medium: {
    level: 'Medium',
    word: 'MEDIUM',
    shape: '◧', // Half-filled square
    shapeAria: 'Medium risk half-filled square marker',
    edgeWidth: '2px',
    edgeClass: 'border-l-[2px]',
    lineStyle: 'dotted',
    underlineClass: 'underline decoration-1 decoration-dotted',
    cssVar: 'var(--medium)',
    tintVar: 'var(--medium-tint)',
  },
  Low: {
    level: 'Low',
    word: 'LOW',
    shape: '○', // Hollow circle
    shapeAria: 'Low risk hollow circle marker',
    edgeWidth: '1px',
    edgeClass: 'border-l-[1px]',
    lineStyle: 'none',
    underlineClass: '',
    cssVar: 'var(--low)',
    tintVar: 'var(--low-tint)',
  },
};

export function normalizeSeverity(severity) {
  if (!severity) return 'Low';
  const clean = String(severity).trim().toLowerCase();
  if (clean === 'critical') return 'Critical';
  if (clean === 'high') return 'High';
  if (clean === 'medium') return 'Medium';
  if (clean === 'low') return 'Low';
  return 'Medium';
}

export function getSeverityConfig(severity) {
  const norm = normalizeSeverity(severity);
  return SEVERITY_CONFIG[norm] || SEVERITY_CONFIG.Low;
}
