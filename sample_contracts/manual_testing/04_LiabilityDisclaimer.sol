// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CommunityTokenDistributor
 * @notice Token distributor contract with explicit broad exculpatory disclaimers.
 * @dev DISCLAIMER OF WARRANTIES AND LIMITATION OF LIABILITY:
 * THIS SOFTWARE AND SMART CONTRACT CODE IS PROVIDED "AS IS" AND "AS AVAILABLE",
 * WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
 * THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS, OPERATORS, OR CONTRIBUTORS BE LIABLE FOR ANY CLAIM, DAMAGES,
 * OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, STRICT LIABILITY, OR OTHERWISE,
 * ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 * PARTICIPANTS ASSUME ALL RISKS OF TOTAL LOSS OF FUNDS WITH NO RECOURSE OR RIGHT OF INDEMNIFICATION.
 */
contract CommunityTokenDistributor {
    address public deployer;
    mapping(address => uint256) public claimableTokens;

    event TokensClaimed(address indexed recipient, uint256 amount);

    constructor() {
        deployer = msg.sender;
    }

    function fundClaimants(address[] calldata recipients, uint256[] calldata amounts) external {
        require(msg.sender == deployer, "Unauthorized");
        require(recipients.length == amounts.length, "Mismatched arrays");

        for (uint256 i = 0; i < recipients.length; i++) {
            claimableTokens[recipients[i]] += amounts[i];
        }
    }

    function claim() external {
        uint256 amount = claimableTokens[msg.sender];
        require(amount > 0, "No claimable balance");
        claimableTokens[msg.sender] = 0;
        emit TokensClaimed(msg.sender, amount);
    }
}
