type ArticleNumberSource = {
  ItemNo?: string | null;
  itemNo?: string | null;
  article_number?: string | null;
  item_no?: string | null;
  external_id?: string | null;
};

export function isCleanArticleNumber(value: string | null | undefined): value is string {
  if (!value) return false;

  const trimmed = value.trim();
  if (!trimmed) return false;

  if (/^\d{11,}$/.test(trimmed)) {
    return false;
  }

  const normalized = trimmed.toLowerCase();
  if (
    normalized.includes("xl") ||
    normalized.includes("xs") ||
    normalized.includes("s-") ||
    normalized.includes("m-") ||
    normalized.includes("l-") ||
    normalized.includes("--")
  ) {
    return false;
  }

  return true;
}

export function getCleanArticleNumber(product: ArticleNumberSource | null | undefined): string | null {
  if (!product) return null;

  const candidates = [
    product.ItemNo,
    product.itemNo,
    product.item_no,
  ];

  for (const candidate of candidates) {
    if (isCleanArticleNumber(candidate)) {
      return candidate.trim();
    }
  }

  return null;
}
