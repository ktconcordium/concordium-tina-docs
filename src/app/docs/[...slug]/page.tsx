// src/app/docs/[...slug]/page.tsx
// @ts-nocheck

import { TinaClient } from "@/app/tina-client";
import settings from "@/content/siteConfig.json";
import { fetchTinaData } from "@/services/tina/fetch-tina-data";
import client from "@/tina/__generated__/client";
import { getTableOfContents } from "@/utils/docs";
import { getSeo } from "@/utils/metadata/getSeo";
import Document from ".";

const siteUrl =
  process.env.NODE_ENV === "development"
    ? "http://localhost:3000"
    : settings.siteUrl;

export async function generateStaticParams() {
  try {
    // Get first page of docs
    let pageListData = await client.queries.docsConnection();

    // Collect all edges, including paginated ones
    const edges: any[] = [
      ...(pageListData.data.docsConnection.edges || []),
    ];

    while (pageListData.data.docsConnection.pageInfo.hasNextPage) {
      const lastCursor = pageListData.data.docsConnection.pageInfo.endCursor;
      pageListData = await client.queries.docsConnection({
        after: lastCursor,
      });

      if (pageListData.data.docsConnection.edges) {
        edges.push(...pageListData.data.docsConnection.edges);
      }
    }

    const pages =
      edges
        .map((page) => {
          const path = page?.node?._sys?.path as string | undefined;
          if (!path) return null;

          const slugWithoutExtension = path.replace(/\.mdx$/, "");
          const pathWithoutPrefix = slugWithoutExtension.replace(
            /^content\/docs\//,
            ""
          );
          const slugArray = pathWithoutPrefix.split("/");

          return { slug: slugArray };
        })
        .filter(Boolean) as { slug: string[] }[];

    return pages;
  } catch (error) {
    console.error("Error in generateStaticParams:", error);
    return [];
  }
}

export async function generateMetadata({ params }: any) {
  const slugArray: string[] = params?.slug || [];
  const slug = slugArray.join("/");

  const { data } = await fetchTinaData(client.queries.docs, slug);

  if (!data.docs.seo) {
    data.docs.seo = {
      __typename: "DocsSeo",
      canonicalUrl: `${siteUrl}/tinadocs/docs/${slug}`,
    };
  } else if (!data.docs.seo?.canonicalUrl) {
    data.docs.seo.canonicalUrl = `${siteUrl}/tinadocs/docs/${slug}`;
  }

  return getSeo(data.docs.seo, {
    pageTitle: data.docs.title,
    body: data.docs.body,
  });
}

async function getData(slug: string) {
  const data = await fetchTinaData(client.queries.docs, slug);
  return data;
}

export default async function DocsPage({ params }: any) {
  const slugArray: string[] = params?.slug || [];
  const slug = slugArray.join("/concordium-tina-docs/");

  const data = await getData(slug);
  const pageTableOfContents = getTableOfContents(data?.data.docs.body);

  return (
    <TinaClient
      Component={Document}
      props={{
        query: data.query,
        variables: data.variables,
        data: data.data,
        pageTableOfContents,
        documentationData: data,
        forceExperimental: data.variables.relativePath,
      }}
    />
  );
}