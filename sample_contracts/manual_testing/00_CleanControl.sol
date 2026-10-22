// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CleanEscrowControl
 * @notice Standard bilateral escrow contract with balanced deposits, dispute settlement, and release.
 * @dev Used as a benign baseline control sample to test standard contract workflows.
 */
contract CleanEscrowControl {
    address public immutable buyer;
    address payable public immutable seller;
    address public immutable arbiter;
    uint256 public immutable escrowAmount;

    enum EscrowState { AwaitingDeposit, Funded, Completed, Refunded }
    EscrowState public state;

    event Deposited(address indexed payer, uint256 amount);
    event Released(address indexed payee, uint256 amount);
    event Refunded(address indexed buyer, uint256 amount);

    modifier onlyBuyer() {
        require(msg.sender == buyer, "Unauthorized: caller is not buyer");
        _;
    }

    modifier onlyArbiter() {
        require(msg.sender == arbiter, "Unauthorized: caller is not arbiter");
        _;
    }

    modifier inState(EscrowState expected) {
        require(state == expected, "Invalid state for action");
        _;
    }

    constructor(address payable _seller, address _arbiter, uint256 _escrowAmount) {
        require(_seller != address(0), "Invalid seller address");
        require(_arbiter != address(0), "Invalid arbiter address");
        require(_escrowAmount > 0, "Escrow amount must exceed zero");

        buyer = msg.sender;
        seller = _seller;
        arbiter = _arbiter;
        escrowAmount = _escrowAmount;
        state = EscrowState.AwaitingDeposit;
    }

    function deposit() external payable onlyBuyer inState(EscrowState.AwaitingDeposit) {
        require(msg.value == escrowAmount, "Deposit must match agreed escrow amount");
        state = EscrowState.Funded;
        emit Deposited(msg.sender, msg.value);
    }

    function releaseFunds() external onlyBuyer inState(EscrowState.Funded) {
        state = EscrowState.Completed;
        emit Released(seller, address(this).balance);
        seller.transfer(address(this).balance);
    }

    function resolveDispute(bool refundBuyer) external onlyArbiter inState(EscrowState.Funded) {
        if (refundBuyer) {
            state = EscrowState.Refunded;
            emit Refunded(buyer, address(this).balance);
            payable(buyer).transfer(address(this).balance);
        } else {
            state = EscrowState.Completed;
            emit Released(seller, address(this).balance);
            seller.transfer(address(this).balance);
        }
    }
}
