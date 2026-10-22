// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VulnerableEscrow
 * @dev Benchmark contract exhibiting unilateral termination and unconstrained fee escalation.
 */
contract VulnerableEscrow {
    address payable public owner;
    uint256 public settlementFee;
    bool public isPaused;

    constructor() {
        owner = payable(msg.sender);
        settlementFee = 100;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function setFee(uint256 newFee) external onlyOwner {
        settlementFee = newFee; // Unconstrained: no maximum ceiling check
    }

    function emergencyKill() external onlyOwner {
        selfdestruct(owner); // Unilateral killswitch
    }
}
