/**
 * Smart Contract Analyser - Mock Data Container
 * Adheres strictly to the 5 primary risk categories:
 * - Privacy
 * - Termination
 * - Legal Compliance
 * - Liability
 * - Payment / Financial
 */

export const mockDashboardStats = {
  totalAnalyzed: 48,
  averageRiskScore: 54, // Medium
  highRiskCount: 11,
  lowRiskCount: 24,
  criticalCount: 4,
};

export const mockRiskCategoryDistribution = [
  { name: 'Termination', count: 28, percentage: 32, color: '#f97316' },
  { name: 'Liability', count: 22, percentage: 25, color: '#eab308' },
  { name: 'Payment / Financial', count: 18, percentage: 20, color: '#a855f7' },
  { name: 'Legal Compliance', count: 12, percentage: 14, color: '#3b82f6' },
  { name: 'Privacy', count: 8, percentage: 9, color: '#06b6d4' },
];

export const mockContracts = [
  {
    id: 'audit-101',
    name: 'EscrowSettlement.sol',
    description: 'Two-party decentralized commercial settlement contract with emergency recovery',
    contractType: 'Commercial Escrow',
    auditDate: '2026-03-28 14:32',
    overallRiskScore: 78,
    overallRiskLevel: 'High',
    confidence: '92.4%',
    summary:
      'Legal-BERT identified significant unilateral termination risks via unconstrained selfdestruct and unlimited fee alteration without counterparty notice.',
    categories: [
      {
        name: 'Termination',
        riskLevel: 'High',
        severity: 'High',
        score: 82,
        detectedClauses: 2,
        summary: 'Emergency kill function allows owner to unilaterally terminate contract and seize remaining escrow funds.',
      },
      {
        name: 'Payment / Financial',
        riskLevel: 'Medium',
        severity: 'Medium',
        score: 64,
        detectedClauses: 1,
        summary: 'Platform fee percentage can be modified up to 25% without prior timelock or depositor consent.',
      },
      {
        name: 'Liability',
        riskLevel: 'Medium',
        severity: 'Medium',
        score: 58,
        detectedClauses: 1,
        summary: 'Total disclaimer of settlement delays and unilateral dispute waiver.',
      },
      {
        name: 'Legal Compliance',
        riskLevel: 'Low',
        severity: 'Low',
        score: 35,
        detectedClauses: 0,
        summary: 'Complies with basic multi-party execution guidelines.',
      },
      {
        name: 'Privacy',
        riskLevel: 'Low',
        severity: 'Low',
        score: 20,
        detectedClauses: 0,
        summary: 'No PII or identity metadata stored on-chain.',
      },
    ],
    solidityCode: `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EscrowSettlement {
    address payable public owner;
    address public buyer;
    address payable public seller;
    uint256 public feeRate = 200; // 2%
    bool public locked = false;

    event PaymentReleased(address indexed to, uint256 amount);

    constructor(address _buyer, address payable _seller) payable {
        owner = payable(msg.sender);
        buyer = _buyer;
        seller = _seller;
    }

    // High Risk: Unilateral Emergency Termination
    function emergencyKill() external {
        require(msg.sender == owner, "Only owner");
        selfdestruct(owner);
    }

    // Medium Risk: Arbitrary Fee Adjustment
    function setFeeRate(uint256 newRate) external {
        require(msg.sender == owner, "Only owner");
        feeRate = newRate;
    }

    function release() external {
        require(msg.sender == buyer || msg.sender == owner, "Unauthorized");
        uint256 fee = (address(this).balance * feeRate) / 10000;
        owner.transfer(fee);
        seller.transfer(address(this).balance);
    }
}`,
    shapExplanations: [
      { token: 'selfdestruct(owner)', contribution: 0.44, impact: 'positive', category: 'Termination' },
      { token: 'require(msg.sender == owner)', contribution: 0.28, impact: 'positive', category: 'Termination' },
      { token: 'feeRate = newRate', contribution: 0.22, impact: 'positive', category: 'Payment / Financial' },
      { token: 'seller.transfer', contribution: -0.18, impact: 'negative', category: 'Payment / Financial' },
      { token: 'msg.sender == buyer', contribution: -0.14, impact: 'negative', category: 'Liability' },
    ],
    limeExplanations: [
      {
        line: 20,
        code: 'selfdestruct(owner);',
        explanation: 'Local perturbation confirms severe unilateral asset seizure risk absent multi-signature approval.',
        weight: 0.89,
      },
      {
        line: 26,
        code: 'feeRate = newRate;',
        explanation: 'Local surrogate model identifies unconstrained variable modification without an upper limit cap.',
        weight: 0.65,
      },
    ],
    recommendations: [
      {
        id: 'rec-1',
        title: 'Replace selfdestruct with Timelocked Refund Mechanism',
        category: 'Termination',
        riskLevel: 'High',
        clause: 'emergencyKill() -> selfdestruct(owner)',
        suggestion: 'Avoid selfdestruct. Implement a two-step timelock that returns escrow balances to the depositing buyer rather than sending all funds to the owner.',
      },
      {
        id: 'rec-2',
        title: 'Impose Fee Rate Ceiling and Timelock Delay',
        category: 'Payment / Financial',
        riskLevel: 'Medium',
        clause: 'setFeeRate(uint256 newRate)',
        suggestion: 'Cap feeRate to a maximum allowable threshold (e.g., 500 bps = 5%) and require a 7-day timelock before fee changes activate.',
      },
    ],
    complianceMatrix: [
      { area: 'Consumer Law Protections', assessment: 'Potential Compliance Risk', status: 'Warning', note: 'Unilateral termination without mutual consent conflicts with consumer fairness principles.' },
      { area: 'Privacy Standards (GDPR / CCPA)', assessment: 'Compliant Scope', status: 'Pass', note: 'Only pseudonymized wallet addresses handled.' },
      { area: 'Contract Fairness (Unfair Terms)', assessment: 'Critical Non-Compliance Risk', status: 'Warning', note: 'Arbitrary fee modification without notice is categorized as an unfair contract term.' },
    ],
  },
  {
    id: 'audit-102',
    name: 'DAOVotingGovernance.sol',
    description: 'Decentralized token-weighted voting protocol with proposal execution delays',
    contractType: 'Governance Protocol',
    auditDate: '2026-03-27 10:15',
    overallRiskScore: 32,
    overallRiskLevel: 'Low',
    confidence: '95.1%',
    summary:
      'Well-balanced governance contract with robust timelocks and proportional voting rights. Minor ambiguity in emergency cancellation authority.',
    categories: [
      { name: 'Termination', riskLevel: 'Low', severity: 'Low', score: 28, detectedClauses: 0, summary: 'No unilateral cancellation.' },
      { name: 'Payment / Financial', riskLevel: 'Low', severity: 'Low', score: 25, detectedClauses: 0, summary: 'Staking requirements well defined.' },
      { name: 'Liability', riskLevel: 'Low', severity: 'Low', score: 30, detectedClauses: 0, summary: 'Balanced governance liability terms.' },
      { name: 'Legal Compliance', riskLevel: 'Low', severity: 'Low', score: 38, detectedClauses: 1, summary: 'Review jurisdictional token classification guidelines.' },
      { name: 'Privacy', riskLevel: 'Low', severity: 'Low', score: 18, detectedClauses: 0, summary: 'Voting records are pseudonymous.' },
    ],
  },
  {
    id: 'audit-103',
    name: 'TokenLendingPool.sol',
    description: 'Automated collateralized lending pool with variable interest rate mechanics',
    contractType: 'DeFi Lending',
    auditDate: '2026-03-25 18:40',
    overallRiskScore: 89,
    overallRiskLevel: 'Critical',
    confidence: '96.8%',
    summary:
      'Multiple high-severity clauses detected: arbitrary liquidation threshold changes, total owner immunity, and unilateral collateral confiscation.',
    categories: [
      { name: 'Liability', riskLevel: 'Critical', severity: 'Critical', score: 92, detectedClauses: 3, summary: 'Complete developer disclaimer for contract failure alongside user indemnity.' },
      { name: 'Payment / Financial', riskLevel: 'Critical', severity: 'Critical', score: 88, detectedClauses: 2, summary: 'Unilateral collateral seizure upon subjective insolvency determinations.' },
      { name: 'Termination', riskLevel: 'High', severity: 'High', score: 76, detectedClauses: 1, summary: 'Permanent withdrawal pause without exit grace period.' },
      { name: 'Legal Compliance', riskLevel: 'High', severity: 'High', score: 74, detectedClauses: 2, summary: 'Severe conflict with financial lending disclosures.' },
      { name: 'Privacy', riskLevel: 'Low', severity: 'Low', score: 24, detectedClauses: 0, summary: 'On-chain balances only.' },
    ],
  },
  {
    id: 'audit-104',
    name: 'KYCRegistryState.sol',
    description: 'On-chain whitelist and compliance tier mapping registry',
    contractType: 'Identity Registry',
    auditDate: '2026-03-24 11:20',
    overallRiskScore: 65,
    overallRiskLevel: 'Medium',
    confidence: '88.9%',
    summary:
      'Identified potential privacy risks regarding immutable storage of hashed identity data and unrevokable compliance flags.',
    categories: [
      { name: 'Privacy', riskLevel: 'High', severity: 'High', score: 79, detectedClauses: 2, summary: 'Identity metadata hashes stored permanently on public ledger.' },
      { name: 'Legal Compliance', riskLevel: 'Medium', severity: 'Medium', score: 62, detectedClauses: 1, summary: 'Tension with GDPR Right to Erasure (Article 17).' },
      { name: 'Termination', riskLevel: 'Low', severity: 'Low', score: 22, detectedClauses: 0, summary: 'Registry status updateable.' },
      { name: 'Liability', riskLevel: 'Medium', severity: 'Medium', score: 55, detectedClauses: 1, summary: 'Unilateral de-whitelisting without appeal.' },
      { name: 'Payment / Financial', riskLevel: 'Low', severity: 'Low', score: 15, detectedClauses: 0, summary: 'Zero financial operations.' },
    ],
  },
  {
    id: 'audit-105',
    name: 'StakingRewardsV2.sol',
    description: 'ERC20 staking contract with continuous block-based emissions',
    contractType: 'Staking Protocol',
    auditDate: '2026-03-22 09:12',
    overallRiskScore: 24,
    overallRiskLevel: 'Low',
    confidence: '97.2%',
    summary:
      'Standard staking contract with deterministic reward calculation, no unilateral freeze mechanisms, and transparent slashing conditions.',
    categories: [
      { name: 'Payment / Financial', riskLevel: 'Low', severity: 'Low', score: 22, detectedClauses: 0, summary: 'Transparent reward distribution.' },
      { name: 'Termination', riskLevel: 'Low', severity: 'Low', score: 18, detectedClauses: 0, summary: 'Emergency exit allows withdraw without rewards.' },
      { name: 'Liability', riskLevel: 'Low', severity: 'Low', score: 20, detectedClauses: 0, summary: 'Standard open-source liability disclaimer.' },
      { name: 'Legal Compliance', riskLevel: 'Low', severity: 'Low', score: 28, detectedClauses: 0, summary: 'Staking yield disclosures recommended.' },
      { name: 'Privacy', riskLevel: 'Low', severity: 'Low', score: 10, detectedClauses: 0, summary: 'No personal data.' },
    ],
  },
];

export const mockReports = mockContracts.map((c) => ({
  id: `rep-${c.id}`,
  contractId: c.id,
  contractName: c.name,
  contractType: c.contractType,
  generatedDate: c.auditDate,
  riskLevel: c.overallRiskLevel,
  riskScore: c.overallRiskScore,
  downloadFormats: ['PDF', 'DOCX'],
}));
