// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UserIdentityRegistry
 * @dev Benchmark contract storing plaintext user personal information directly on public state slots.
 */
contract UserIdentityRegistry {
    address public admin;
    string public userEmail; // High-risk plaintext PII
    string public physicalAddress; // High-risk plaintext PII

    constructor() {
        admin = msg.sender;
    }

    function registerUser(string calldata _email, string calldata _address) external {
        userEmail = _email;
        physicalAddress = _address;
    }
}
