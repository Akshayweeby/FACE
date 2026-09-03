// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PostVerification {
    struct Post {
        uint256 id;
        bytes32 postHash;
        string postUrl;
        uint256 originalTimestamp;
        address uploader;
        uint256 uploadedAt;
        bool verified;
    }

    uint256 public postCounter;
    mapping(uint256 => Post) private posts;

    event PostUploaded(uint256 indexed postId, bytes32 postHash, address indexed uploader);
    event PostVerified(uint256 indexed postId, bool isValid);

    function uploadPost(bytes32 postHash, string calldata postUrl, uint256 originalTimestamp)
        external returns (uint256 postId)
    {
        postId = ++postCounter;
        posts[postId] = Post(postId, postHash, postUrl, originalTimestamp, msg.sender, block.timestamp, false);
        emit PostUploaded(postId, postHash, msg.sender);
    }

    function getPost(uint256 postId) external view returns (Post memory) {
        require(postId > 0 && postId <= postCounter, "Post not found");
        return posts[postId];
    }

    function verifyPost(uint256 postId, bytes32 postHash) external returns (bool isValid) {
        require(postId > 0 && postId <= postCounter, "Post not found");
        isValid = posts[postId].postHash == postHash;
        posts[postId].verified = isValid;
        emit PostVerified(postId, isValid);
    }
}
