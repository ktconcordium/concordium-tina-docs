import { defineConfig } from "tinacms";
import { schema } from "./schema";

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
    publicFolder: "public",
    outputFolder: "admin",
    // 👇 IMPORTANT: no leading slash, just the repo name
    basePath: "concordium-tina-docs",
  },
});

export default config;