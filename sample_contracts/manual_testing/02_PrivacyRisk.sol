// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title UserIdentityDirectory
 * @notice On-chain directory storing natural-person personal identifying information.
 * @dev Intended to exercise the Privacy risk category (unencrypted PII on public ledger).
 */
contract UserIdentityDirectory {
    address public registrar;

    struct IdentityProfile {
        string userEmail;
        string physicalAddress;
        string fullName;
        bool isVerified;
    }

    mapping(address => IdentityProfile) public userProfiles;

    // Public state variables exposing individual identifiers in plaintext
    string public userEmail;
    string public physicalAddress;

    event ProfileRegistered(address indexed userAccount, string email);

    modifier onlyRegistrar() {
        require(msg.sender == registrar, "Caller is not registrar");
        _;
    }

    constructor() {
        registrar = msg.sender;
    }

    function registerIdentity(
        string calldata _email,
        string calldata _physicalAddress,
        string calldata _fullName
    ) external {
        userProfiles[msg.sender] = IdentityProfile({
            userEmail: _email,
            physicalAddress: _physicalAddress,
            fullName: _fullName,
            isVerified: true
        });

        userEmail = _email;
        physicalAddress = _physicalAddress;

        emit ProfileRegistered(msg.sender, _email);
    }
}
