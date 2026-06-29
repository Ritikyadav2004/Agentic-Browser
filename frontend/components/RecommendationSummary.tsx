import { Sparkles } from "lucide-react";
import type { ComparisonRow } from "@/types/api";
import RecommendationBadge, { BadgeType } from "./RecommendationBadge";

interface PickCardProps {
  type: BadgeType;
  pick: Partial<ComparisonRow>;
}

function PickCard({ type, pick }: PickCardProps) {
  if (!pick || !pick.title) return null;

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-2">
        <RecommendationBadge type={type} />
      </div>
      {pick.url ? (
        <a href={pick.url} target="_blank" rel="noopener noreferrer" className="hover:text-brand-600 dark:hover:text-brand-400">
          <h4 className="mb-1 line-clamp-2 text-sm font-semibold text-slate-800 hover:underline dark:text-zinc-200">{pick.title}</h4>
        </a>
      ) : (
        <h4 className="mb-1 line-clamp-2 text-sm font-semibold text-slate-800 dark:text-zinc-200">{pick.title}</h4>
      )}
      <p className="mb-2 text-xs text-slate-500 dark:text-zinc-400">{pick.source}</p>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-lg font-bold text-slate-900 dark:text-zinc-50">
          {pick.price !== null && pick.price !== undefined
            ? `₹${pick.price.toLocaleString("en-IN")}`
            : "—"}
        </span>
        {pick.rating !== null && pick.rating !== undefined && (
          <span className="text-xs text-slate-500 dark:text-zinc-400">{pick.rating.toFixed(1)} ★</span>
        )}
      </div>
      {pick.reason && <p className="text-xs leading-relaxed text-slate-500 dark:text-zinc-450">{pick.reason}</p>}
      {pick.url && (
        <a
          href={pick.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center justify-center rounded-xl border border-slate-200 py-2 text-xs font-medium text-slate-700 transition hover:border-brand-300 hover:text-brand-700 dark:border-zinc-800 dark:text-zinc-300 dark:hover:border-brand-500/50 dark:hover:text-brand-400"
        >
          View product
        </a>
      )}
    </div>
  );
}

interface RecommendationSummaryProps {
  bestChoice: Partial<ComparisonRow>;
  budgetChoice: Partial<ComparisonRow>;
  premiumChoice: Partial<ComparisonRow>;
  whyRecommended: string;
}

export default function RecommendationSummary({
  bestChoice,
  budgetChoice,
  premiumChoice,
  whyRecommended,
}: RecommendationSummaryProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <PickCard type="best" pick={bestChoice} />
        <PickCard type="budget" pick={budgetChoice} />
        <PickCard type="premium" pick={premiumChoice} />
      </div>

      {whyRecommended && (
        <div className="flex gap-3 rounded-2xl border border-brand-100 bg-brand-50 p-4 dark:border-brand-900/30 dark:bg-brand-950/20">
          <Sparkles className="mt-0.5 h-5 w-5 flex-shrink-0 text-brand-600 dark:text-brand-400" />
          <p className="text-sm leading-relaxed text-slate-700 dark:text-zinc-300">{whyRecommended}</p>
        </div>
      )}
    </div>
  );
}
