const { expect } = require("chai");

describe("PostVerification", function () {
  async function deployed() {
    const Factory = await ethers.getContractFactory("PostVerification");
    const contract = await Factory.deploy();
    await contract.waitForDeployment();
    return contract;
  }

  it("uploads and retrieves a record", async function () {
    const c = await deployed();
    await c.uploadPost(ethers.id("post"), "https://example.test/post", 1700000000);
    const record = await c.getPost(1);
    expect(record.id).to.equal(1n);
    expect(record.postHash).to.equal(ethers.id("post"));
    expect(record.postUrl).to.equal("https://example.test/post");
    expect(record.verified).to.equal(false);
  });

  it("verifies unchanged data and rejects changed hash", async function () {
    const c = await deployed();
    await c.uploadPost(ethers.id("unchanged"), "url", 1);
    await expect(c.verifyPost(1, ethers.id("unchanged"))).to.emit(c, "PostVerified").withArgs(1, true);
    await expect(c.verifyPost(1, ethers.id("caption changed"))).to.emit(c, "PostVerified").withArgs(1, false);
    expect((await c.getPost(1)).verified).to.equal(false);
  });

  it("rejects a nonexistent record", async function () {
    const c = await deployed();
    await expect(c.getPost(99)).to.be.revertedWith("Post not found");
    await expect(c.verifyPost(99, ethers.id("missing"))).to.be.revertedWith("Post not found");
  });
});
