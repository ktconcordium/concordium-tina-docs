import { defineConfig } from "tinacms";
import { schema } from "./schema";

const isProd = process.env.NODE_ENV === "production";
// name of your GitHub Pages subfolder
const repoBasePath = "concordium-tina-docs";

export const config = defineConfig({
  schema,
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID,
  branch:
    process.env.NEXT_PUBLIC_TINA_BRANCH || // custom override
    process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_REF || // Vercel
    process.env.HEAD, // Netlify
  token: process.env.TINA_TOKEN,
  media: {
    tina: {
      publicFolder: "public",
      mediaRoot: "",
    },
    accept: ["image/*", "video/*", "application/json", ".json"],
  },
  build: {
    publicFolder: "public",
    outputFolder: "admin",
    // 🔴 key line: only use the sub-path on production builds
    basePath: isProd ? repoBasePath : "",
  },
});

export default config;