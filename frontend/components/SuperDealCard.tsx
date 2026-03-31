"use client";

import Link from "next/link";

import type { SuperDeal } from "@/lib/api";

function getSuperDealHref(deal: SuperDeal): string {
  if (deal.article_number) {
    return `/shop?q=${encodeURIComponent(deal.article_number)}`;
  }

  if (deal.pdf_url) {
    return deal.pdf_url;
  }

  return "/kontakt";
}

export function SuperDealCard({ deal }: { deal: SuperDeal }) {
  const href = getSuperDealHref(deal);
  const isExternal = href.startsWith("http");

  const content = (
    <>
      <div className="flex justify-center mb-4">
        <div className="w-32 h-32 rounded-full bg-[#f5efe6] flex items-center justify-center overflow-hidden flex-shrink-0">
          <img
            src={deal.image_url || "/images/placeholder.webp"}
            alt={deal.title}
            className="max-h-[90%] max-w-[90%] object-contain"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.src = "/images/placeholder.webp";
            }}
          />
        </div>
      </div>

      <h3 className="text-sm font-medium text-gray-800 mb-1 line-clamp-2 leading-snug">
        {deal.title}
      </h3>

      {deal.article_number && (
        <p className="text-xs text-gray-400 mb-2">Art.nr: {deal.article_number}</p>
      )}

      {deal.price_text && (
        <p className="text-sm font-semibold text-stone-900 mb-2">{deal.price_text}</p>
      )}

      <div className="mt-auto">
        <span className="inline-block bg-blue-500 text-white text-xs px-4 py-2 rounded-md group-hover:bg-blue-600 transition">
          Visa erbjudande
        </span>
      </div>
    </>
  );

  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="relative group bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm hover:shadow-md transition-all duration-200 flex flex-col"
      >
        {content}
      </a>
    );
  }

  return (
    <Link
      href={href}
      className="relative group bg-white border border-gray-200 rounded-xl p-4 text-center shadow-sm hover:shadow-md transition-all duration-200 flex flex-col"
    >
      {content}
    </Link>
  );
}

export default SuperDealCard;
