/**
 * IAM policy helpers for Remotion Lambda.
 *
 * CEX-32: Provides getUserPolicy() and getRolePolicy() for setting up
 * AWS IAM permissions required by Remotion Lambda.
 *
 * Usage:
 *   npx tsx iam-setup.ts user   # Print user policy JSON
 *   npx tsx iam-setup.ts role   # Print role policy JSON
 */

import { getUserPolicy, getRolePolicy } from "@remotion/lambda";

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

export function printUserPolicy(): string {
  const policy = getUserPolicy();
  const json = JSON.stringify(policy, null, 2);
  console.log("=== IAM User Policy ===");
  console.log("Attach this inline policy to the IAM user whose credentials");
  console.log("are used by the deploy script and the Python API:\n");
  console.log(json);
  return json;
}

export function printRolePolicy(): string {
  const policy = getRolePolicy(REGION);
  const json = JSON.stringify(policy, null, 2);
  console.log("=== IAM Role Policy ===");
  console.log("Attach this inline policy to the 'remotion-lambda-role' IAM role.");
  console.log("The Lambda function assumes this role at runtime:\n");
  console.log(json);
  return json;
}

// CLI entrypoint
const arg = process.argv[2];

if (arg === "user") {
  printUserPolicy();
} else if (arg === "role") {
  printRolePolicy();
} else if (arg) {
  console.error(`Unknown argument: ${arg}. Use 'user' or 'role'.`);
  process.exit(1);
} else {
  console.log("Remotion Lambda IAM Setup\n");
  printUserPolicy();
  console.log("\n");
  printRolePolicy();
}
