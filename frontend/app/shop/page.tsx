import {
  filterStorefrontProducts,
  getItemNo,
  getProductCategory,
  normalizeCategorySlug,
} from "@/lib/product-utils";
import { ProductCard } from "@/components/ProductCard";
import { fetchProductOverrides } from "@/lib/api";

async function getProducts(searchParams?: { category?: string; sector?: string }) {
  const params = new URLSearchParams();
  params.set("limit", "2000");

  if (searchParams && searchParams.category) {
    params.set("category", String(searchParams.category));
  }

  if (searchParams && searchParams.sector) {
    params.set("sector", String(searchParams.sector));
  }

  const query = params.toString();
  const url = query
    ? `https://uniforma.livosys.se/api/v1/products?${query}`
    : "https://uniforma.livosys.se/api/v1/products";
  const res = await fetch(url, {
    cache: "no-store",
  });

  if (!res.ok) {
    return [];
  }

  return res.json();
}

function normalizeSearchValue(value: string) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[^a-z0-9-]/g, "");
}

function searchProducts(products: any[], query: string) {
  const q = query.toLowerCase().trim();
  const qNorm = normalizeSearchValue(query);

  return products.filter((p: any) => {
    const itemNo = getItemNo(p);
    const article = String(p.article_number || "");
    const external = String(p.external_id || "");
    const itemNorm = normalizeSearchValue(itemNo);
    const articleNorm = normalizeSearchValue(article);
    const externalNorm = normalizeSearchValue(external);
    const name = String(p.name || "").toLowerCase();
    const nameNorm = normalizeSearchValue(p.name || "");

    console.log("SHOP SEARCH DEBUG:", {
      query,
      itemNo: getItemNo(p),
    });

    return (
      itemNorm.includes(qNorm) ||
      articleNorm.includes(qNorm) ||
      externalNorm.includes(qNorm) ||
      name.includes(q) ||
      nameNorm.includes(qNorm)
    );
  });
}

export default async function ShopPage({
  searchParams,
}: {
  searchParams?: { q?: string; category?: string; sector?: string };
}) {
  const [rawProducts, overrides] = await Promise.all([
    getProducts(searchParams),
    fetchProductOverrides(),
  ]);
  const filteredProducts = filterStorefrontProducts(rawProducts || [], overrides);
  const query = searchParams?.q ? String(searchParams.q).trim() : "";
  const category = searchParams?.category ? String(searchParams.category).trim() : "";
  const normalizedCategory = category ? normalizeCategorySlug(category.toLowerCase()) : "";
  const categoryProducts = normalizedCategory
    ? filteredProducts.filter((p: any) => {
        const productCategory = getProductCategory(p);

        console.log("CATEGORY MATCH:", {
          category,
          productCategory,
        });

        return productCategory.includes(normalizedCategory);
      })
    : filteredProducts;
  const products = query
    ? searchProducts(categoryProducts, query)
    : categoryProducts;
  console.log("RAW PRODUCTS:", rawProducts.length);
  console.log("VISIBLE PRODUCTS:", products.length);
  console.log("SHOP SEARCH QUERY:", query);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {products.map((product: any) => (
        <ProductCard key={getItemNo(product)} product={product} />
      ))}
    </div>
  );
}
