const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const redirects = require("./content/settings/config.json")?.redirects || [];

/** @type {import('next').NextConfig} */

const isStatic = process.env.EXPORT_MODE === "static";

// 👇 key part for GitHub Pages
const basePath =
  process.env.NEXT_PUBLIC_BASE_PATH ||
  (process.env.NODE_ENV === "production" ? "/concordium-tina-docs" : "");

const assetPrefix =
  process.env.NEXT_PUBLIC_ASSET_PREFIX || basePath || undefined;

const extraConfig = {};

if (isStatic) {
  extraConfig.output = "export";
  extraConfig.trailingSlash = true;
  extraConfig.skipTrailingSlashRedirect = true;
}

module.exports = {
  ...extraConfig,
  basePath,
  assetPrefix,
  images: {
    path: `${assetPrefix}/_next/image`,
    remotePatterns: [
      {
        protocol: "https",
        hostname: "assets.tina.io",
        port: "",
      },
    ],
  },

  outputFileTracingIncludes: {
    "/api/**/*": [],
  },
  outputFileTracingExcludes: {
    "/api/**/*": [
      ".next/cache/**/*",
      "node_modules/@swc/core-linux-x64-gnu",
      "node_modules/@swc/core-linux-x64-musl",
      "node_modules/@esbuild/",
      "node_modules/webpack",
      "node_modules/terser",
      ".git/**/*",
      "public/**/*",
    ],
  },

  async rewrites() {
    return [
      {
        // Note: basePath is handled automatically by Next,
        // so we leave this as "/admin"
        source: "/admin",
        destination: "/admin/index.html",
      },
    ];
  },

  async redirects() {
    return redirects.map((redirect) => ({
      source: redirect.source,
      destination: redirect.destination,
      permanent: redirect.permanent,
    }));
  },

  turbopack: {
    resolveExtensions: [".mdx", ".tsx", ".ts", ".jsx", ".js", ".mjs", ".json"],
    rules: {
      "*.svg": {
        loaders: ["@svgr/webpack"],
        as: "*.js",
      },
    },
  },

  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.plugins.push(
        new MonacoWebpackPlugin({
          languages: ["javascript"],
          filename: "static/[name].worker.js",
          features: ["!gotoSymbol"],
        })
      );
    }

    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });

    if (isServer) {
      config.externals = [...(config.externals || []), "fs", "path", "os"];
    }

    return config;
  },
};