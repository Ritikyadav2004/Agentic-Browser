import { ExternalLink, Star, MessageSquare } from "lucide-react";
import Image from "next/image";
import type { ProductSpec } from "@/types/api";
import RecommendationBadge, { BadgeType } from "./RecommendationBadge";

interface ProductCardProps {
  product: ProductSpec;
  badge?: BadgeType;
}

export default function ProductCard({ product, badge }: ProductCardProps) {
  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-2">
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {product.source}
        </span>
        {badge && <RecommendationBadge type={badge} />}
      </div>

      {product.url ? (
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group/image mb-3 flex h-32 items-center justify-center overflow-hidden rounded-xl bg-slate-50"
        >
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.title}
              width={128}
              height={128}
              className="h-full w-auto object-contain transition duration-300 group-hover/image:scale-105"
              unoptimized
            />
          ) : (
            <span className="text-xs text-slate-400">No image</span>
          )}
        </a>
      ) : (
        <div className="mb-3 flex h-32 items-center justify-center overflow-hidden rounded-xl bg-slate-50">
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.title}
              width={128}
              height={128}
              className="h-full w-auto object-contain"
              unoptimized
            />
          ) : (
            <span className="text-xs text-slate-400">No image</span>
          )}
        </div>
      )}

      {product.url ? (
        <a href={product.url} target="_blank" rel="noopener noreferrer" className="hover:text-brand-600">
          <h3 className="mb-2 line-clamp-2 text-sm font-semibold text-slate-800 hover:underline" title={product.title}>
            {product.title}
          </h3>
        </a>
      ) : (
        <h3 className="mb-2 line-clamp-2 text-sm font-semibold text-slate-800" title={product.title}>
          {product.title}
        </h3>
      )}

      <div className="mb-2 flex items-center gap-3 text-xs text-slate-500">
        {product.rating !== null && (
          <span className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
            {product.rating.toFixed(1)}
          </span>
        )}
        {product.reviews_count !== null && (
          <span className="flex items-center gap-1">
            <MessageSquare className="h-3.5 w-3.5" />
            {product.reviews_count.toLocaleString("en-IN")}
          </span>
        )}
      </div>

      <div className="mb-3 flex items-center justify-between">
        <span className="text-lg font-bold text-slate-900">
          {product.price !== null ? `₹${product.price.toLocaleString("en-IN")}` : "—"}
        </span>
        {product.availability && (
          <span
            className={`text-xs font-medium ${
              product.availability.toLowerCase().includes("stock")
                ? "text-emerald-600"
                : "text-slate-400"
            }`}
          >
            {product.availability}
          </span>
        )}
      </div>

      {product.url && (
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 py-2 text-sm font-medium text-slate-700 transition hover:border-brand-300 hover:text-brand-700"
        >
          View on {product.source}
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      )}
    </div>
  );
}
