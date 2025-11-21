import { defineConfig } from "tinacms";
import { schema } from "./schema";

const repoName = "concordium-tina-docs";

// Base path used by Tina admin assets (same as Next basePath)
const tinaBasePath =
  process.env.NEXT_PUBLIC_BASE_PATH ||
  (process.env.NODE_ENV === "production" ? `/${repoName}` : "");

export const config = defineConfig({
  schema,
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID,
  branch:
    process.env.NEXT_PUBLIC_TINA_BRANCH ||
    process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_REF ||
    process.env.HEAD ||
    "main",
  token: process.env.TINA_TOKEN,
  media: {
    tina: {
      publicFolder: "public",
      mediaRoot: "",
    },
    accept: ["image/*", "video/*", "application/json", ".json"],
  },
  build: {
    publicFolder: "public", // The public asset folder for your framework
    outputFolder: "admin",  // within the public folder
    basePath: tinaBasePath, // 🔹 NEW: prefix admin assets with /concordium-tina-docs in prod
  },
});

export default config;