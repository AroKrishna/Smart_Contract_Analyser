// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TerminationRiskVault
 * @notice Vault contract with an emergency unilateral killswitch.
 * @dev Intended to exercise the Termination risk category (killswitch / selfdestruct).
 */
contract TerminationRiskVault {
    address payable public owner;
    mapping(address => uint256) public userBalances;

    event Deposited(address indexed user, uint256 amount);
    event EmergencyTerminated(address indexed recipient, uint256 recoveredBalance);

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the contract owner");
        _;
    }

    constructor() {
        owner = payable(msg.sender);
    }

    function deposit() external payable {
        require(msg.value > 0, "Deposit must be greater than zero");
        userBalances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice Unilateral killswitch destroying the contract and forwarding all pooled funds to owner.
     * @dev Executes selfdestruct opcode without notice or counterparty consent.
     */
    function emergencyKill() external onlyOwner {
        emit EmergencyTerminated(owner, address(this).balance);
        selfdestruct(owner);
    }
}
