// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title HighRiskStaking
 * @notice Staking contract provided strictly as is without warranty of any kind.
 * The operator accepts no liability whatsoever for lost funds. Stake at your own risk.
 */
contract HighRiskStaking {
    address public owner;
    uint256 public rewardTax;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function setTax(uint256 _newTax) external onlyOwner {
        rewardTax = _newTax; // Unconstrained fee
    }
}
