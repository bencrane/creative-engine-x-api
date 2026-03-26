/**
 * Remotion Lambda deployment script.
 *
 * CEX-32: Idempotent deployment of Remotion site and Lambda function.
 * Outputs functionName and serveUrl for use by the Python API.
 *
 * Usage: npx tsx deploy.ts
 *
 * Required env vars:
 *   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION (default: us-east-1)
 */

import path from "path";
import {
  deploySite,
  deployFunction,
  getOrCreateBucket,
} from "@remotion/lambda";

const REGION = (process.env.AWS_REGION || "us-east-1") as
  | "us-east-1"
  | "us-east-2"
  | "us-west-2"
  | "eu-central-1"
  | "eu-west-1"
  | "eu-west-2"
  | "ap-south-1"
  | "ap-southeast-1"
  | "ap-southeast-2"
  | "ap-northeast-1";

const MEMORY_SIZE_MB = 2048;
const TIMEOUT_SECONDS = 240;
const DISK_SIZE_MB = 2048;

export interface DeployResult {
  functionName: string;
  serveUrl: string;
  bucketName: string;
  region: string;
}

export async function deploy(): Promise<DeployResult> {
  console.log(`Deploying to region: ${REGION}`);

  // Step 1: Ensure S3 bucket exists (one per region)
  console.log("Ensuring S3 bucket...");
  const { bucketName, alreadyExisted: bucketExisted } =
    await getOrCreateBucket({ region: REGION });
  console.log(
    `Bucket: ${bucketName} (${bucketExisted ? "already existed" : "created"})`,
  );

  // Step 2: Bundle and deploy the Remotion site to S3
  console.log("Deploying site...");
  const { serveUrl, siteName } = await deploySite({
    entryPoint: path.resolve(process.cwd(), "src/index.ts"),
    bucketName,
    region: REGION,
    siteName: "creative-engine-x",
  });
  console.log(`Site deployed: ${siteName}`);
  console.log(`Serve URL: ${serveUrl}`);

  // Step 3: Deploy (or reuse) the Lambda function
  console.log("Deploying Lambda function...");
  const { functionName, alreadyExisted: fnExisted } = await deployFunction({
    region: REGION,
    timeoutInSeconds: TIMEOUT_SECONDS,
    memorySizeInMb: MEMORY_SIZE_MB,
    createCloudWatchLogGroup: true,
    diskSizeInMb: DISK_SIZE_MB,
  });
  console.log(
    `Function: ${functionName} (${fnExisted ? "already existed" : "created"})`,
  );

  // Output summary
  const result: DeployResult = {
    functionName,
    serveUrl,
    bucketName,
    region: REGION,
  };

  console.log("\n--- Deployment Complete ---");
  console.log(`REMOTION_FUNCTION_NAME=${functionName}`);
  console.log(`REMOTION_SERVE_URL=${serveUrl}`);
  console.log(`AWS_REGION=${REGION}`);

  return result;
}

// Run if executed directly
const isMain =
  typeof require !== "undefined"
    ? require.main === module
    : process.argv[1]?.includes("deploy");

if (isMain) {
  deploy().catch((err) => {
    console.error("Deployment failed:", err);
    process.exit(1);
  });
}
