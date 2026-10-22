// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CentralizedTreasuryGovernance
 * @notice Multi-faceted treasury management contract with centralized administrative authority.
 * @dev Intended to exercise the Legal Compliance risk category (centralized execution without timelock governance).
 */
contract CentralizedTreasuryGovernance {
    address public rootAdmin;
    bool public systemPaused;
    mapping(address => bool) public blacklistedAccounts;
    mapping(address => uint256) public treasuryAllocations;

    event EmergencyPauseTriggered(bool isPaused);
    event AccountBlacklisted(address indexed account, bool status);
    event AdminOwnershipTransferred(address indexed oldAdmin, address indexed newAdmin);
    event AllocationModified(address indexed beneficiary, uint256 newAllocation);

    modifier onlyRootAdmin() {
        require(msg.sender == rootAdmin, "Only root admin can execute");
        _;
    }

    constructor() {
        rootAdmin = msg.sender;
    }

    // Sensitive function 1: Immediate arbitrary pausing without timelock delay
    function toggleEmergencyPause(bool _paused) external onlyRootAdmin {
        systemPaused = _paused;
        emit EmergencyPauseTriggered(_paused);
    }

    // Sensitive function 2: Unilateral blacklisting freezing user interaction
    function setBlacklistStatus(address account, bool isBlacklisted) external onlyRootAdmin {
        blacklistedAccounts[account] = isBlacklisted;
        emit AccountBlacklisted(account, isBlacklisted);
    }

    // Sensitive function 3: Unilateral balance allocation manipulation
    function overrideAllocation(address beneficiary, uint256 newAmount) external onlyRootAdmin {
        treasuryAllocations[beneficiary] = newAmount;
        emit AllocationModified(beneficiary, newAmount);
    }

    // Sensitive function 4: Instantaneous admin transfer without multi-sig or timelock
    function changeRootAdmin(address newAdmin) external onlyRootAdmin {
        require(newAdmin != address(0), "Zero address disallowed");
        emit AdminOwnershipTransferred(rootAdmin, newAdmin);
        rootAdmin = newAdmin;
    }
}
