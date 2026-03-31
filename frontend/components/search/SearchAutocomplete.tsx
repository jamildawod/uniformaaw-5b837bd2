"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { fetchProductOverrides } from "@/lib/api";
import { filterStorefrontProducts, getItemNo, getProductImage } from "@/lib/product-utils";

const BLUR_DATA_URL =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1NiIgaGVpZ2h0PSI1NiIgdmlld0JveD0iMCAwIDU2IDU2Ij48cmVjdCB3aWR0aD0iNTYiIGhlaWdodD0iNTYiIGZpbGw9IiNmNWVmZTYiLz48L3N2Zz4=";

export default function SearchAutocomplete({ onNavigate }: { onNavigate?: () => void }) {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);

  // 🔥 Fetch ALL products once
  useEffect(() => {
    Promise.all([
      fetch("https://uniforma.livosys.se/api/v1/products?limit=2000").then((res) => res.json()),
      fetchProductOverrides(),
    ])
      .then(([data, overrides]) => {
        const visibleProducts = filterStorefrontProducts(Array.isArray(data) ? data : [], overrides);
        console.log("LOADED PRODUCTS:", visibleProducts.length);
        setProducts(visibleProducts);
      })
      .catch((err) => console.log("FETCH ERROR:", err));
  }, []);

  // 🔥 Filter on typing
  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    const q = query.toLowerCase();

    const filtered = products
      .filter((p) => {
        const item = getItemNo(p).toLowerCase();
        const name = String(p.name || "").toLowerCase();

        return item.includes(q) || name.includes(q);
      })
      .slice(0, 5);

    console.log("AUTOCOMPLETE RESULTS:", filtered);

    setResults(filtered);
  }, [query, products]);

  return (
    <div className="relative w-full max-w-xl">

      {/* INPUT */}
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Sök artikelnummer eller produkt..."
        className="w-full border rounded px-4 py-2"
      />

      {/* DROPDOWN */}
      {query.length >= 2 && results.length > 0 && (
        <div className="absolute top-full left-0 w-full bg-white border shadow-lg mt-2 z-50">

          {results.map((product) => (
            <a
              key={product.id}
              href={`/product/${getItemNo(product)}`}
              className="flex items-center gap-4 px-4 py-3 hover:bg-gray-50"
            >
              <div className="relative w-14 h-14 rounded shrink-0 overflow-hidden bg-[#f5efe6]">
                {getProductImage(product) && (
                  <Image
                    src={getProductImage(product)}
                    alt={product.name}
                    fill
                    className="object-cover rounded"
                    loading="lazy"
                    placeholder="blur"
                    blurDataURL={BLUR_DATA_URL}
                    sizes="56px"
                  />
                )}
              </div>

              <div>
                <div className="text-sm font-medium">
                  {product.name}
                </div>
                <div className="text-xs text-gray-500">
                  {getItemNo(product)}
                </div>
              </div>
            </a>
          ))}

          <a
            href={`/shop?q=${query}`}
            className="block px-4 py-3 text-sm text-gray-600 hover:bg-gray-50"
          >
            Visa alla resultat →
          </a>

        </div>
      )}
    </div>
  );
}
