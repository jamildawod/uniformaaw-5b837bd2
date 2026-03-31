export interface Category {
  id: number;
  name: string;
  slug: string;
  parent_id: number | null;
}

export interface ProductImage {
  id: number;
  variant_id: number | null;
  external_path: string;
  local_path: string | null;
  is_primary: boolean;
  sort_order: number;
  url: string;
}

export interface ProductVariant {
  id: number;
  sku: string;
  ean: string | null;
  color: string | null;
  size: string | null;
  price: string | null;
  currency: string | null;
  stock_quantity: number;
  is_active: boolean;
  images: ProductImage[];
}

export interface Product {
  id: string;
  external_id: string;
  ItemNo?: string | null;
  itemNo?: string | null;
  article_number?: string | null;
  item_no?: string | null;
  image?: string | null;
  image_url?: string | null;
  ProductLifeCycleStatus?: string | null;
  lifecycle_status?: string | null;
  name: string;
  slug: string;
  description: string | null;
  brand: string | null;
  material: string | null;
  fit: string | null;
  care_instructions: string[];
  tags: string[];
  certifications: string[];
  qr_code: string | null;
  attributes: Record<string, string> | null;
  is_active: boolean;
  price: string | null;
  primary_image?: string | null;
  created_at?: string;
  category: Category | null;
  images: ProductImage[];
  variants: ProductVariant[];
}

export interface Filters {
  colors: string[];
  sizes: string[];
  categories: Category[];
}
