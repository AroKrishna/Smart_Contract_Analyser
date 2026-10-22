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
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    dotClass: 'bg-emerald-400',
    barClass: 'bg-emerald-500',
  },
  [RISK_LEVELS.MEDIUM]: {
    label: 'Medium Risk',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    dotClass: 'bg-amber-400',
    barClass: 'bg-amber-500',
  },
  [RISK_LEVELS.HIGH]: {
    label: 'High Risk',
    badgeClass: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    dotClass: 'bg-orange-400',
    barClass: 'bg-orange-500',
  },
  [RISK_LEVELS.CRITICAL]: {
    label: 'Critical Risk',
    badgeClass: 'bg-red-500/10 text-red-400 border-red-500/20',
    dotClass: 'bg-red-400',
    barClass: 'bg-red-500',
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

