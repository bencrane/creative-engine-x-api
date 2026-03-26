import { describe, it, expect, vi } from "vitest";

// Mock @remotion/lambda before importing deploy
vi.mock("@remotion/lambda", () => ({
  getOrCreateBucket: vi.fn().mockResolvedValue({
    bucketName: "remotionlambda-test-bucket",
    alreadyExisted: true,
  }),
  deploySite: vi.fn().mockResolvedValue({
    serveUrl: "https://remotionlambda-test.s3.amazonaws.com/sites/creative-engine-x",
    siteName: "creative-engine-x",
    stats: { uploadedFiles: 10, deletedFiles: 0, untouchedFiles: 5 },
  }),
  deployFunction: vi.fn().mockResolvedValue({
    functionName: "remotion-render-test-fn",
    alreadyExisted: false,
  }),
  getUserPolicy: vi.fn().mockReturnValue({
    Version: "2012-10-17",
    Statement: [{ Effect: "Allow", Action: ["lambda:*"], Resource: "*" }],
  }),
  getRolePolicy: vi.fn().mockReturnValue({
    Version: "2012-10-17",
    Statement: [{ Effect: "Allow", Action: ["s3:*"], Resource: "*" }],
  }),
}));

describe("deploy script", () => {
  it("exports deploy function", async () => {
    const { deploy } = await import("../deploy");
    expect(deploy).toBeDefined();
    expect(typeof deploy).toBe("function");
  });

  it("deploy returns functionName, serveUrl, bucketName, region", async () => {
    const { deploy } = await import("../deploy");
    const result = await deploy();

    expect(result.functionName).toBe("remotion-render-test-fn");
    expect(result.serveUrl).toContain("creative-engine-x");
    expect(result.bucketName).toBe("remotionlambda-test-bucket");
    expect(result.region).toBe("us-east-1");
  });

  it("deploy calls getOrCreateBucket", async () => {
    const lambda = await import("@remotion/lambda");
    const { deploy } = await import("../deploy");
    await deploy();

    expect(lambda.getOrCreateBucket).toHaveBeenCalledWith({
      region: "us-east-1",
    });
  });

  it("deploy calls deploySite with correct entryPoint", async () => {
    const lambda = await import("@remotion/lambda");
    const { deploy } = await import("../deploy");
    await deploy();

    expect(lambda.deploySite).toHaveBeenCalledWith(
      expect.objectContaining({
        bucketName: "remotionlambda-test-bucket",
        region: "us-east-1",
        siteName: "creative-engine-x",
      }),
    );
  });

  it("deploy calls deployFunction with correct params", async () => {
    const lambda = await import("@remotion/lambda");
    const { deploy } = await import("../deploy");
    await deploy();

    expect(lambda.deployFunction).toHaveBeenCalledWith(
      expect.objectContaining({
        region: "us-east-1",
        timeoutInSeconds: 240,
        memorySizeInMb: 2048,
        createCloudWatchLogGroup: true,
        diskSizeInMb: 2048,
      }),
    );
  });
});

describe("iam-setup", () => {
  it("exports printUserPolicy and printRolePolicy", async () => {
    const mod = await import("../iam-setup");
    expect(mod.printUserPolicy).toBeDefined();
    expect(mod.printRolePolicy).toBeDefined();
  });

  it("printUserPolicy returns JSON string", async () => {
    const { printUserPolicy } = await import("../iam-setup");
    const result = printUserPolicy();
    const parsed = JSON.parse(result);
    expect(parsed.Version).toBe("2012-10-17");
  });

  it("printRolePolicy returns JSON string", async () => {
    const { printRolePolicy } = await import("../iam-setup");
    const result = printRolePolicy();
    const parsed = JSON.parse(result);
    expect(parsed.Version).toBe("2012-10-17");
  });
});
