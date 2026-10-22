"""
analysis/seed_db.py - Seed persistent database with initial demo and benchmark audits
"""

import os
import json
import datetime
from analysis.db import init_db, insert_analysis

SAMPLE_ESCROW = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VulnerableEscrow
 * @dev Benchmark contract demonstrating emergency killswitch and unconstrained fees.
 */
contract VulnerableEscrow {
    address payable public owner;
    uint256 public settlementFee;

    constructor() {
        owner = payable(msg.sender);
    }

    function setFee(uint256 newFee) external {
        require(msg.sender == owner, "Only owner");
        settlementFee = newFee; // Unconstrained fee
    }

    function emergencyKill() external {
        require(msg.sender == owner, "Only owner");
        selfdestruct(owner); // Unilateral killswitch
    }
}
"""

SAMPLE_TIMELOCKED = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SafeTimelockedEscrow
 * @dev Safe bounded escrow contract with ceiling checks.
 */
contract SafeTimelockedEscrow {
    address public owner;
    uint256 public constant MAX_FEE = 500; // 5% ceiling
    uint256 public settlementFee;

    constructor() {
        owner = msg.sender;
    }

    function setFee(uint256 newFee) external {
        require(msg.sender == owner, "Only owner");
        require(newFee <= MAX_FEE, "Fee exceeds ceiling");
        settlementFee = newFee;
    }
}
"""

SAMPLE_IDENTITY = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UserIdentityRegistry
 * @dev Identity registry storing unencrypted natural-person identifying data.
 */
contract UserIdentityRegistry {
    string public userEmail;
    string public physicalAddress;

    function registerUser(string calldata _email, string calldata _address) external {
        userEmail = _email;
        physicalAddress = _address;
    }
}
"""


def seed():
    init_db()
    print("Database initialized.")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Record 1: Vulnerable Escrow
    rec1 = {
        "analysisId": "audit-101",
        "id": "audit-101",
        "contractName": "VulnerableEscrow.sol",
        "contractType": "DeFi Escrow Settlement",
        "solidityCode": SAMPLE_ESCROW,
        "solidityVersion": "^0.8.20",
        "status": "completed",
        "riskScore": 88,
        "riskLevel": "Critical",
        "riskBreakdown": {
            "Termination": 90,
            "Payment / Financial": 85,
            "Legal Compliance": 30,
            "Liability": 15,
            "Privacy": 0
        },
        "categories": [
            {"name": "Termination", "riskLevel": "Critical", "severity": "Critical", "score": 90, "detectedClauses": 1, "summary": "Unilateral selfdestruct killswitch capable of sweeping balances without counterparty notice."},
            {"name": "Payment / Financial", "riskLevel": "High", "severity": "High", "score": 85, "detectedClauses": 1, "summary": "Unconstrained fee alteration lacking an immutable upper ceiling check."},
            {"name": "Legal Compliance", "riskLevel": "Medium", "severity": "Medium", "score": 30, "detectedClauses": 0, "summary": "Absence of multi-sig timelock governance for privileged operations."},
            {"name": "Liability", "riskLevel": "Low", "severity": "Low", "score": 15, "detectedClauses": 0, "summary": "Standard operational documentation."},
            {"name": "Privacy", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "No plaintext PII state variables identified."}
        ],
        "findings": [
            {
                "findingId": "find-1",
                "category": "Termination",
                "title": "Unilateral Termination Killswitch",
                "severity": "Critical",
                "description": "emergencyKill executes selfdestruct opcode transferring contract funds to deployer and destroying bytecode.",
                "snippet": "selfdestruct(owner);",
                "lineNumbers": [22]
            },
            {
                "findingId": "find-2",
                "category": "Payment / Financial",
                "title": "Unbounded Fee Escalation",
                "severity": "High",
                "description": "setFee updates settlementFee without checking against a constant ceiling.",
                "snippet": "settlementFee = newFee;",
                "lineNumbers": [17]
            }
        ],
        "shapValues": [
            {"feature": "selfdestruct(owner)", "token": "selfdestruct", "value": 0.42, "contribution": 0.42, "category": "Termination", "impact": "positive"},
            {"feature": "settlementFee = newFee", "token": "settlementFee", "value": 0.35, "contribution": 0.35, "category": "Payment / Financial", "impact": "positive"}
        ],
        "limeExplanations": [
            {"token": "selfdestruct", "weight": 0.42, "line": 22, "code": "selfdestruct(owner);", "explanation": "Direct invocation of bytecode termination instruction."},
            {"token": "settlementFee", "weight": 0.35, "line": 17, "code": "settlementFee = newFee;", "explanation": "Unconstrained state variable modification."}
        ],
        "recommendations": [
            {
                "id": "rec-1",
                "category": "Termination",
                "riskLevel": "Critical",
                "title": "Deprecate Irreversible selfdestruct Opcode",
                "clause": "function emergencyKill() external { selfdestruct(owner); }",
                "suggestion": "Replace selfdestruct with OpenZeppelin Pausable circuit breaker.",
                "beforeCode": "selfdestruct(owner);",
                "afterCode": "_pause(); emit EmergencyPaused(msg.sender);"
            },
            {
                "id": "rec-2",
                "category": "Payment / Financial",
                "riskLevel": "High",
                "title": "Enforce Immutable Maximum Fee Ceiling",
                "clause": "function setFee(uint256 newFee) external { settlementFee = newFee; }",
                "suggestion": "Add require(newFee <= MAX_FEE, 'Fee cap exceeded');",
                "beforeCode": "settlementFee = newFee;",
                "afterCode": "require(newFee <= MAX_FEE, 'Exceeds cap'); settlementFee = newFee;"
            }
        ],
        "complianceMatrix": [
            {"area": "Consumer Law Protections", "assessment": "Potential Operational Hazard", "status": "Warning", "note": "Unilateral termination and unbounded fee alterations conflict with fairness standards."},
            {"area": "Privacy Standards (GDPR / CCPA)", "assessment": "Compliant Scope", "status": "Pass", "note": "Zero plaintext personal identifiable information stored."},
            {"area": "Contract Fairness & Governance", "assessment": "Potential Operational Hazard", "status": "Warning", "note": "Unilateral execution without timelock delay."}
        ],
        "summary": "Legal assessment identified 2 operational hazards across Termination and Payment categories.",
        "created_at": now
    }
    insert_analysis(rec1)

    # Record 2: Safe Timelocked Escrow
    rec2 = {
        "analysisId": "audit-102",
        "id": "audit-102",
        "contractName": "SafeTimelockedEscrow.sol",
        "contractType": "DeFi Escrow Settlement",
        "solidityCode": SAMPLE_TIMELOCKED,
        "solidityVersion": "^0.8.20",
        "status": "completed",
        "riskScore": 12,
        "riskLevel": "Low",
        "riskBreakdown": {
            "Termination": 0,
            "Payment / Financial": 10,
            "Legal Compliance": 15,
            "Liability": 0,
            "Privacy": 0
        },
        "categories": [
            {"name": "Termination", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "No contract killswitches or selfdestruct opcodes present."},
            {"name": "Payment / Financial", "riskLevel": "Low", "severity": "Low", "score": 10, "detectedClauses": 0, "summary": "Fee modifications are strictly bounded against immutable MAX_FEE ceiling."},
            {"name": "Legal Compliance", "riskLevel": "Low", "severity": "Low", "score": 15, "detectedClauses": 0, "summary": "Governance parameters adhere to bounded execution."},
            {"name": "Liability", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "Standard NatSpec notices."},
            {"name": "Privacy", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "Zero personal identifiable data."}
        ],
        "findings": [],
        "shapValues": [],
        "limeExplanations": [],
        "recommendations": [],
        "complianceMatrix": [
            {"area": "Consumer Law Protections", "assessment": "Compliant Scope", "status": "Pass", "note": "Bounded fee adjustments protect counterparties from surprise charges."},
            {"area": "Privacy Standards (GDPR / CCPA)", "assessment": "Compliant Scope", "status": "Pass", "note": "Zero PII on-chain."},
            {"area": "Contract Fairness & Governance", "assessment": "Compliant Scope", "status": "Pass", "note": "Balanced operational controls."}
        ],
        "summary": "Completed analysis with zero critical operational hazards.",
        "created_at": now
    }
    insert_analysis(rec2)

    # Record 3: User Identity Registry
    rec3 = {
        "analysisId": "audit-103",
        "id": "audit-103",
        "contractName": "UserIdentityRegistry.sol",
        "contractType": "Decentralized Identity (DID)",
        "solidityCode": SAMPLE_IDENTITY,
        "solidityVersion": "^0.8.20",
        "status": "completed",
        "riskScore": 76,
        "riskLevel": "High",
        "riskBreakdown": {
            "Privacy": 85,
            "Legal Compliance": 40,
            "Termination": 0,
            "Liability": 0,
            "Payment / Financial": 0
        },
        "categories": [
            {"name": "Privacy", "riskLevel": "Critical", "severity": "Critical", "score": 85, "detectedClauses": 1, "summary": "Plaintext string storage of email and physical address on public ledger."},
            {"name": "Legal Compliance", "riskLevel": "Medium", "severity": "Medium", "score": 40, "detectedClauses": 0, "summary": "Potential conflict with statutory right-to-erasure requirements."},
            {"name": "Termination", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "No killswitches."},
            {"name": "Liability", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "Standard notices."},
            {"name": "Payment / Financial", "riskLevel": "Low", "severity": "Low", "score": 0, "detectedClauses": 0, "summary": "No fee setters."}
        ],
        "findings": [
            {
                "findingId": "find-priv-1",
                "category": "Privacy",
                "title": "Plaintext PII Storage on Public Blockchain",
                "severity": "Critical",
                "description": "userEmail and physicalAddress state variables store unencrypted identifying info permanently.",
                "snippet": "string public userEmail; string public physicalAddress;",
                "lineNumbers": [9, 10]
            }
        ],
        "shapValues": [
            {"feature": "userEmail", "token": "userEmail", "value": 0.48, "contribution": 0.48, "category": "Privacy", "impact": "positive"},
            {"feature": "physicalAddress", "token": "physicalAddress", "value": 0.45, "contribution": 0.45, "category": "Privacy", "impact": "positive"}
        ],
        "limeExplanations": [
            {"token": "userEmail", "weight": 0.48, "line": 9, "code": "string public userEmail;", "explanation": "Direct public ledger storage of email addresses."},
            {"token": "physicalAddress", "weight": 0.45, "line": 10, "code": "string public physicalAddress;", "explanation": "Direct public ledger storage of physical addresses."}
        ],
        "recommendations": [
            {
                "id": "rec-priv-1",
                "category": "Privacy",
                "riskLevel": "Critical",
                "title": "Migrate Plaintext PII to Salted Hashes or Off-Chain Storage",
                "clause": "string public userEmail; string public physicalAddress;",
                "suggestion": "Store keccak256(email, salt) or use off-chain encrypted IPFS/DID resolvers.",
                "beforeCode": "string public userEmail;",
                "afterCode": "bytes32 public emailHash;"
            }
        ],
        "complianceMatrix": [
            {"area": "Consumer Law Protections", "assessment": "Compliant Scope", "status": "Pass", "note": "No unfair consumer fee or killswitch clauses."},
            {"area": "Privacy Standards (GDPR / CCPA)", "assessment": "Potential Operational Hazard", "status": "Warning", "note": "Permanent plaintext PII conflicts with Article 17 Right to Erasure."},
            {"area": "Contract Fairness & Governance", "assessment": "Compliant Scope", "status": "Pass", "note": "Open access registration."}
        ],
        "summary": "Identified critical operational privacy risks involving plaintext PII on-chain.",
        "created_at": now
    }
    insert_analysis(rec3)
    print("Database seeded with initial audit records.")


if __name__ == "__main__":
    seed()
