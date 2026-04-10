// SPDX-License-Identifier: MIT
pragma solidity ^0.7.4;

contract BallotContract {
    struct Ballot {
        bytes ballotSignature;
        bytes publicKey;
        bytes registerSignedPublicKey;
        uint256 timestamp;
    }

    Ballot[] public ballots;
    mapping(uint256 => uint256) public candidateVotes;
    
    event BallotCast(bytes ballotSignature, uint256 timestamp);

    function castBallot(
        bytes memory _ballotSignature,
        bytes memory _publicKey,
        bytes memory _registerSignedPublicKey,
        uint256 _candidateId
    ) public {
        ballots.push(Ballot({
            ballotSignature: _ballotSignature,
            publicKey: _publicKey,
            registerSignedPublicKey: _registerSignedPublicKey,
            timestamp: block.timestamp
        }));
        
        candidateVotes[_candidateId]++;
        emit BallotCast(_ballotSignature, block.timestamp);
    }

    function getBallotCount() public view returns (uint256) {
        return ballots.length;
    }

    function getCandidateVotes(uint256 _candidateId) public view returns (uint256) {
        return candidateVotes[_candidateId];
    }
}