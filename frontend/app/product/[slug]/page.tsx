import { notFound } from "next/navigation";

import { ProductDetailClient } from "@/components/ProductDetailClient";
import { fetchProductOverrides } from "@/lib/api";
import {
  applyProductOverrides,
  getItemNo,
  getProductImage,
  isVisibleStorefrontProduct,
} from "@/lib/product-utils";

async function getProducts() {
  const res = await fetch("https://uniforma.livosys.se/api/v1/products?limit=2000", {
    cache: "no-store",
  });

  if (!res.ok) {
    return [];
  }

  const data = await res.json();

  console.log("ALL PRODUCTS:", data.length);

  return Array.isArray(data) ? data : [];
}

export default async function ProductPage({ params }: { params: { slug: string } }) {
  const [products, overrides] = await Promise.all([
    getProducts(),
    fetchProductOverrides(),
  ]);
  const itemNo = params.slug;

  console.log("PARAMS:", itemNo);

  const product = products.find((p: any) => {
    try {
      return getItemNo(p) === itemNo;
    } catch {
      return false;
    }
  });

  console.log("FOUND PRODUCT:", product);

  if (!product) {
    notFound();
  }

  const visibleProduct = applyProductOverrides(product, overrides);

  if (!isVisibleStorefrontProduct(visibleProduct)) {
    notFound();
  }

  visibleProduct.image = getProductImage(visibleProduct);

  return <ProductDetailClient product={visibleProduct} />;
}
