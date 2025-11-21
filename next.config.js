const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const redirects = require("./content/settings/config.json")?.redirects || [];

/** @type {import('next').NextConfig} */

// GitHub Pages repo name
const repoName = "concordium-tina-docs";
const isProd = process.env.NODE_ENV === "production";

// When building for GitHub Pages:
const basePath = isProd ? `/${repoName}` : "";
const assetPrefix = isProd ? `/${repoName}` : "";

// Static export config for GitHub Pages
const isStatic = process.env.EXPORT_MODE === "static";

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
    unoptimized: true, // REQUIRED for GitHub Pages
  },

  async rewrites() {
    return [
      {
        // Corrected rewrite for GitHub Pages
        source: `${basePath}/admin`,
        destination: `${basePath}/admin/index.html`,
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