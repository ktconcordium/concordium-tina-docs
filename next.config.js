// next.config.js
const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const redirects = require("./content/settings/config.json")?.redirects || [];

/** @type {import('next').NextConfig} */

const isStatic = process.env.EXPORT_MODE === "static";

const extraConfig = {};
if (isStatic) {
  extraConfig.output = "export";
  extraConfig.trailingSlash = true;
  extraConfig.skipTrailingSlashRedirect = true;
}

const nextConfig = {
  ...extraConfig,

  // We are at root: https://tinacms.concordium.com
  // so NO basePath / NO assetPrefix
  images: {
    // Required for GitHub Pages / static export
    unoptimized: true,
  },

  // For static export, rewrites / redirects don’t truly work,
  // but leaving redirects here is OK if you accept they’re just no-ops on GH Pages.
  async rewrites() {
    // no special rewrite for /admin needed:
    // GitHub Pages serves public/admin/index.html at /admin automatically.
    return [];
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

module.exports = nextConfig;