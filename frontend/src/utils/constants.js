export const APP_NAME = 'Smart Contract Analyser';
export const APP_TAGLINE = 'Explainable AI Framework for Smart Contract Legal-Risk Assessment';

/**
 * Official Legal Risk Categories
 * IMPORTANT: Use these exact category names as defined in project specifications.
 */
export const RISK_CATEGORIES = [
  'Privacy',
  'Termination',
  'Legal Compliance',
  'Liability',
  'Payment / Financial',
];

/**
 * Risk Levels & Associated Semantic Styles
 */
export const RISK_LEVELS = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  CRITICAL: 'Critical',
};

export const RISK_LEVEL_CONFIG = {
  [RISK_LEVELS.LOW]: {
    label: 'Low Risk',
    badgeClass: 'bg-[var(--low-tint)] text-[var(--low)] border-[var(--low)]',
    dotClass: 'bg-[var(--low)]',
    barClass: 'bg-[var(--low)]',
  },
  [RISK_LEVELS.MEDIUM]: {
    label: 'Medium Risk',
    badgeClass: 'bg-[var(--medium-tint)] text-[var(--medium)] border-[var(--medium)]',
    dotClass: 'bg-[var(--medium)]',
    barClass: 'bg-[var(--medium)]',
  },
  [RISK_LEVELS.HIGH]: {
    label: 'High Risk',
    badgeClass: 'bg-[var(--high-tint)] text-[var(--high)] border-[var(--high)]',
    dotClass: 'bg-[var(--high)]',
    barClass: 'bg-[var(--high)]',
  },
  [RISK_LEVELS.CRITICAL]: {
    label: 'Critical Risk',
    badgeClass: 'bg-[var(--critical-tint)] text-[var(--critical)] border-[var(--critical)]',
    dotClass: 'bg-[var(--critical)]',
    barClass: 'bg-[var(--critical)]',
  },
};

/**
 * 8-Stage AI Legal-Risk Pipeline representation
 */
export const PIPELINE_STAGES = [
  { id: 1, name: 'Uploading contract', detail: 'Parsing Solidity source code and metadata' },
  { id: 2, name: 'Preprocessing', detail: 'Normalizing contract syntax and stripping comments' },
  { id: 3, name: 'Tokenizing', detail: 'AST generation and sub-word tokenization for sequence models' },
  { id: 4, name: 'Running AI analysis', detail: 'Evaluating clause semantics via Legal-BERT classification' },
  { id: 5, name: 'Classifying legal risks', detail: 'Mapping probabilities across 5 primary risk taxonomies' },
  { id: 6, name: 'Generating explanations', detail: 'Computing SHAP token attributions & LIME local surrogates' },
  { id: 7, name: 'Generating recommendations', detail: 'Synthesizing contract remediation guidance' },
  { id: 8, name: 'Preparing report', detail: 'Compiling structured decision-support audit' },
];
