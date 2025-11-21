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

/**
 * Pre-generate all possible slug params from Tina docs.
 */
export async function generateStaticParams() {
  try {
    let pageListData = await client.queries.docsConnection();
    const edges: any[] = [];

    // Collect first page
    if (pageListData.data.docsConnection.edges) {
      edges.push(...pageListData.data.docsConnection.edges);
    }

    // Paginate if needed
    while (pageListData.data.docsConnection.pageInfo.hasNextPage) {
      const lastCursor = pageListData.data.docsConnection.pageInfo.endCursor;
      pageListData = await client.queries.docsConnection({ after: lastCursor });

      if (pageListData.data.docsConnection.edges) {
        edges.push(...pageListData.data.docsConnection.edges);
      }
    }

    const pages =
      edges.map((edge) => {
        const path: string = edge?.node?._sys?.path || "";
        if (!path) return null;

        // content/docs/foo/bar.mdx -> foo/bar
        const slugWithoutExtension = path.replace(/\.mdx$/, "");
        const pathWithoutPrefix = slugWithoutExtension.replace(
          /^content\/docs\//,
          ""
        );

        const slugArray = pathWithoutPrefix
          .split("/")
          .filter((segment) => segment.length > 0);

        return { slug: slugArray };
      }).filter(Boolean) || [];

    return pages as { slug: string[] }[];
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("Error in generateStaticParams:", error);
    return [];
  }
}

/**
 * SEO metadata for each docs page.
 */
export async function generateMetadata({
  params,
}: {
  params: { slug: string[] };
}) {
  const slug = params?.slug?.join("/") || "";
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

/**
 * Docs page component.
 */
export default async function DocsPage({
  params,
}: {
  params: { slug: string[] };
}) {
  const slug = params?.slug?.join("/") || "";
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