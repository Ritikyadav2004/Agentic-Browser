import { Award, Wallet, Sparkles } from "lucide-react";

export type BadgeType = "best" | "budget" | "premium";

const BADGE_CONFIG: Record<
  BadgeType,
  { label: string; className: string; icon: React.ReactNode }
> = {
  best: {
    label: "Best Choice",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-900/30",
    icon: <Award className="h-3.5 w-3.5" />,
  },
  budget: {
    label: "Budget Pick",
    className: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900/30",
    icon: <Wallet className="h-3.5 w-3.5" />,
  },
  premium: {
    label: "Premium Pick",
    className: "bg-violet-100 text-violet-700 border-violet-200 dark:bg-violet-950/30 dark:text-violet-400 dark:border-violet-900/30",
    icon: <Sparkles className="h-3.5 w-3.5" />,
  },
};

export default function RecommendationBadge({ type }: { type: BadgeType }) {
  const config = BADGE_CONFIG[type];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.className}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
}
