"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, ShieldCheck, Tag } from "lucide-react";

import {
  resolveImageUrl,
  resolveProductImage,
  type StoreImage,
  type StoreImageLike,
  type StoreProduct,
  type StoreVariant,
} from "@/components/ProductCard";
import { VariantSelector } from "@/components/VariantSelector";

type Props = {
  product: StoreProduct;
};

const CARE_INSTRUCTION_META: Record<
  string,
  { icon: string; label: string }
> = {
  wash_60: { icon: "60°", label: "Tvätt 60°" },
  no_bleach: { icon: "No", label: "Ingen blekning" },
  tumble_dry_low: { icon: "TD", label: "Torktumla låg värme" },
  iron_medium: { icon: "IR", label: "Stryk medelvärme" },
};

function isStoreImage(image: StoreImageLike): image is StoreImage {
  return typeof image !== "string";
}

function sortImages(images: StoreImageLike[]) {
  return [...images].sort((left, right) => {
    const a = isStoreImage(left) ? left : null;
    const b = isStoreImage(right) ? right : null;

    if (!a && !b) return 0;
    if (!a) return 1;
    if (!b) return -1;

    if (a.is_primary && !b.is_primary) return -1;
    if (!a.is_primary && b.is_primary) return 1;
    return (a.sort_order ?? 0) - (b.sort_order ?? 0);
  });
}

function dedupeImages(images: StoreImageLike[]) {
  const seen = new Set<string>();

  return sortImages(images).filter((image) => {
    const key =
      typeof image === "string"
        ? image
        : image.url ?? image.local_path ?? image.external_path ?? String(image.id);

    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Safe image component that falls back to /placeholder.jpg on load error.
 * Resets the error state whenever the `src` prop changes so switching gallery
 * images never leaves a stale error fallback on screen.
 */
function ProductImage({
  src,
  alt,
  priority = false,
}: {
  src: string;
  alt: string;
  priority?: boolean;
}) {
  const [error, setError] = useState(false);

  // Reset error when src changes (e.g. user clicks a different gallery thumbnail)
  useEffect(() => {
    setError(false);
  }, [src]);

  const displaySrc = error ? "/placeholder.jpg" : src;

  if (displaySrc.startsWith("data:")) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={displaySrc} alt={alt} className="h-full w-full object-cover" />;
  }

  return (
    <Image
      src={displaySrc}
      alt={alt}
      width={1200}
      height={1500}
      unoptimized
      className="h-full w-full object-cover"
      sizes="(max-width: 1024px) 100vw, 55vw"
      priority={priority}
      onError={() => setError(true)}
    />
  );
}

function QrPreview({ value, alt }: { value: string; alt: string }) {
  const src = `https://api.qrserver.com/v1/create-qr-code/?size=112x112&data=${encodeURIComponent(value)}`;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className="h-20 w-20 rounded-lg border border-stone-200 bg-white p-1"
      loading="lazy"
    />
  );
}

function DetailBlock({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-stone-400">
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </div>
  );
}

export function ProductDetailClient({ product }: Props) {
  const tags = product.tags ?? [];
  const care = product.care_instructions ?? [];
  const certs = product.certifications ?? [];
  const attrs = product.attributes ?? {};
  const safeVariants = product.variants ?? [];
  const safeName = product.name || "Uniforma";
  const safeImages = product.images ?? [];

  const variants = useMemo(
    () => safeVariants.filter((variant) => variant.is_active ?? true),
    [safeVariants],
  );

  const productGallery = useMemo(() => {
    if (safeImages.length > 0) {
      return dedupeImages(safeImages);
    }
    return dedupeImages(variants.flatMap((variant) => variant.images ?? []));
  }, [safeImages, variants]);

  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<StoreVariant | null>(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  const activeGallery = useMemo(() => {
    const variantImages = selectedVariant?.images ?? [];
    return variantImages.length > 0 ? dedupeImages(variantImages) : productGallery;
  }, [productGallery, selectedVariant]);

  // Reset gallery index when the active gallery changes (variant switch or initial load)
  useEffect(() => {
    setSelectedImageIndex(0);
  }, [selectedVariant]);

  // Clamp index to gallery bounds defensively
  const safeImageIndex = Math.min(
    selectedImageIndex,
    Math.max(0, activeGallery.length - 1),
  );

  const mainImageSrc = activeGallery[safeImageIndex]
    ? resolveImageUrl(activeGallery[safeImageIndex])
    : resolveProductImage(product);

  const visibleCareInstructions = care.filter(
    (item) => Boolean(item) && CARE_INSTRUCTION_META[item],
  );
  const visibleTags = tags.filter(Boolean);
  const visibleCertifications = certs.filter(Boolean);
  const visibleAttributes = Object.entries(attrs).filter(
    ([key, value]) => Boolean(key) && Boolean(value),
  );

  return (
    <section className="grid gap-12 lg:grid-cols-[1fr_480px] xl:grid-cols-[1fr_520px]">
      <div className="flex flex-col gap-3">
        <div className="overflow-hidden rounded-2xl bg-stone-100 shadow-sm ring-1 ring-stone-200/60">
          <div className="aspect-[4/5]">
            <ProductImage src={mainImageSrc} alt={safeName} priority />
          </div>
        </div>

        {activeGallery.length > 1 && (
          <div className="grid grid-cols-5 gap-2">
            {activeGallery.slice(0, 5).map((image, index) => {
              const src = resolveImageUrl(image);
              const isActive = index === safeImageIndex;

              return (
                <button
                  key={typeof image === "string" ? image : image.id}
                  type="button"
                  onClick={() => setSelectedImageIndex(index)}
                  className={`overflow-hidden rounded-xl bg-stone-100 ring-1 transition ${
                    isActive
                      ? "ring-stone-950"
                      : "ring-stone-200/60 hover:ring-stone-400"
                  }`}
                >
                  <div className="aspect-square">
                    <ProductImage src={src} alt={safeName} />
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex flex-col">
        <div className="flex flex-wrap items-center gap-2">
          {product.category && (
            <Link
              href={`/shop?category=${product.category.slug}`}
              className="inline-flex items-center gap-1.5 rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-600 transition hover:bg-stone-200"
            >
              <Tag className="h-3 w-3" />
              {product.category.name}
            </Link>
          )}
        </div>

        <h1 className="mt-4 text-3xl font-bold tracking-tight text-stone-950 sm:text-4xl">
          {safeName}
        </h1>

        <p className="mt-5 text-sm leading-7 text-stone-600">
          {product.description ||
            "Produktinformation kommer snart. Kontakta Uniforma för material, profilering och leveransalternativ."}
        </p>

        <div className="mt-8 space-y-4">
          {product.material && (
            <DetailBlock title="Material">
              <p className="text-sm leading-7 text-stone-700">
                {product.material}
              </p>
            </DetailBlock>
          )}

          {visibleCareInstructions.length > 0 && (
            <DetailBlock title="Tvättråd">
              <div className="flex flex-wrap gap-2.5">
                {visibleCareInstructions.map((instruction) => {
                  const meta = CARE_INSTRUCTION_META[instruction];

                  return (
                    <div
                      key={instruction}
                      className="inline-flex items-center gap-2 rounded-xl border border-stone-200 bg-stone-50 px-3 py-2 text-sm text-stone-700"
                    >
                      <span className="inline-flex h-8 min-w-8 items-center justify-center rounded-lg bg-white px-2 text-xs font-semibold text-stone-950 ring-1 ring-stone-200">
                        {meta.icon}
                      </span>
                      <span>{meta.label}</span>
                    </div>
                  );
                })}
              </div>
            </DetailBlock>
          )}

          {visibleTags.length > 0 && (
            <DetailBlock title="Taggar">
              <div className="flex flex-wrap gap-2">
                {visibleTags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-xs font-medium text-stone-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </DetailBlock>
          )}

          {visibleCertifications.length > 0 && (
            <DetailBlock title="Certifieringar">
              <div className="space-y-3">
                {visibleCertifications.map((certification, index) => (
                  <div
                    key={`${certification.name}-${index}`}
                    className="flex flex-col gap-3 rounded-2xl border border-stone-200 bg-stone-50 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-white text-stone-700 ring-1 ring-stone-200">
                        <ShieldCheck className="h-5 w-5" />
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-stone-950">
                          {certification.name}
                          {certification.label ? ` ${certification.label}` : ""}
                        </p>
                        <p className="mt-1 text-xs text-stone-500">
                          Kvalitets- och materialcertifiering
                        </p>
                      </div>
                    </div>
                    {certification.qr && (
                      <div className="flex items-center gap-3 rounded-xl border border-stone-200 bg-white px-3 py-2 text-xs text-stone-500">
                        <QrPreview
                          value={certification.qr}
                          alt={`${certification.name} QR-kod`}
                        />
                        <div>
                          <p className="font-medium text-stone-700">QR</p>
                          <a
                            href={certification.qr}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-1 block max-w-[180px] truncate text-stone-500 transition hover:text-stone-950"
                          >
                            {certification.qr}
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </DetailBlock>
          )}

          {visibleAttributes.length > 0 && (
            <DetailBlock title="Specifikation">
              <dl className="space-y-3">
                {visibleAttributes.map(([label, value]) => (
                  <div
                    key={label}
                    className="flex items-start justify-between gap-6 border-b border-stone-100 pb-3 last:border-b-0 last:pb-0"
                  >
                    <dt className="text-sm text-stone-500">{label}</dt>
                    <dd className="text-right text-sm font-medium text-stone-800">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </DetailBlock>
          )}

          {product.qr_code && visibleCertifications.length === 0 && (
            <DetailBlock title="QR">
              <div className="flex items-center gap-3">
                <QrPreview value={product.qr_code} alt={`${safeName} QR-kod`} />
                <a
                  href={product.qr_code}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-stone-600 transition hover:text-stone-950"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Öppna produktlänk
                </a>
              </div>
            </DetailBlock>
          )}
        </div>

        {safeVariants.length > 0 && (
          <div className="mt-8">
            <VariantSelector
              variants={safeVariants}
              selectedSize={selectedSize}
              selectedColor={selectedColor}
              onSizeChange={setSelectedSize}
              onColorChange={setSelectedColor}
              onVariantChange={setSelectedVariant}
            />
          </div>
        )}

        <div className="mt-8 rounded-2xl bg-stone-950 p-6 text-white">
          <p className="text-sm font-semibold">Kontakta oss för offert</p>
          <p className="mt-1 text-sm text-stone-400">
            Vi hjälper dig med profilering, storleksfrågor och anpassade beställningar.
          </p>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/#kontakt"
              className="inline-flex items-center justify-center rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-stone-950 transition hover:bg-stone-100"
            >
              Skicka förfrågan
            </Link>
          </div>
        </div>

        <Link
          href="/shop"
          className="mt-6 flex items-center gap-2 self-start text-sm font-medium text-stone-500 transition hover:text-stone-950"
        >
          <ArrowLeft className="h-4 w-4" />
          Tillbaka till produkter
        </Link>
      </div>
    </section>
  );
}
