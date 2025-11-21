const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const redirects = require("./content/settings/config.json")?.redirects || [];

/** @type {import('next').NextConfig} */

// ---- GitHub Pages / basePath setup ----
const repoName = "concordium-tina-docs";
const isProd = process.env.NODE_ENV === "production";

// We still keep the EXPORT_MODE flag you already use
const isStatic = process.env.EXPORT_MODE === "static";

// For local dev: no basePath
// For GitHub Pages (production): use /concordium-tina-docs
const basePath = isProd ? `/${repoName}` : "";
const assetPrefix = isProd ? `/${repoName}` : "";

// Static export config for GitHub Pages
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
    // Static export on GitHub Pages => disable Next's image optimizer
    unoptimized: true,
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