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
 * Pre-generate all static params for docs pages
 */
export async function generateStaticParams() {
  try {
    // First page of docs
    let pageListData = await client.queries.docsConnection({});
    const edges = [...(pageListData.data.docsConnection.edges ?? [])];

    // Collect all remaining pages if paginated
    while (pageListData.data.docsConnection.pageInfo.hasNextPage) {
      const lastCursor = pageListData.data.docsConnection.pageInfo.endCursor;
      pageListData = await client.queries.docsConnection({
        after: lastCursor,
      });

      edges.push(...(pageListData.data.docsConnection.edges ?? []));
    }

    // Map to the slug array expected by [...slug]
    return edges
      .map((edge) => edge?.node?._sys.path)
      .filter((path): path is string => !!path)
      .map((path) => {
        const withoutExt = path.replace(/\.mdx?$/, "");
        const withoutPrefix = withoutExt.replace(/^content\/docs\//, "");
        const slugArray = withoutPrefix.split("/");

        return { slug: slugArray };
      });
  } catch (error) {
    // biome-ignore lint/suspicious/noConsole
    console.error("Error in generateStaticParams:", error);
    return [];
  }
}

/**
 * Metadata generation for each docs page
 */
export async function generateMetadata({
  params,
}: {
  params: { slug: string[] };
}) {
  const slug = (params.slug || []).join("/");
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
 * Docs page component
 */
export default async function DocsPage({
  params,
}: {
  params: { slug: string[] };
}) {
  const slug = (params.slug || []).join("/");
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