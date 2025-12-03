import { defineConfig } from "tinacms";
import { schema } from "./schema";

export const config = defineConfig({
  schema,

  // TinaCloud auth
  clientId: process.env.NEXT_PUBLIC_TINA_CLIENT_ID,
  token: process.env.TINA_TOKEN,

  // Branch resolution (GitHub Pages uses main)
  branch:
    process.env.NEXT_PUBLIC_TINA_BRANCH ||
    process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_REF ||
    process.env.HEAD ||
    "main",

  media: {
    tina: {
      publicFolder: "public",
      mediaRoot: "",
    },
    accept: ["image/*", "video/*", "application/json", ".json"],
  },

  build: {
    publicFolder: "public", // where Next serves static assets from
    outputFolder: "admin",  // so we get public/admin/index.html, etc.
    basePath: "",
  },

  search: {
    tina: {
      indexerToken: '9953e40ff9b09ac907c76decf924c1a3fea6bb89',
      stopwordLanguages: ['eng'],
    },
    indexBatchSize: 100,
    maxSearchIndexFieldLength: 100,
  },
});

export default config;