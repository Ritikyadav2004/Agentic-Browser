import { Tag, Wallet, Target } from "lucide-react";
import type { ParsedQuery } from "@/types/api";

export default function QuerySummary({ parsedQuery }: { parsedQuery: ParsedQuery }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
        <Tag className="h-3.5 w-3.5" />
        Category: {parsedQuery.category}
      </span>
      {parsedQuery.budget !== null && (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
          <Wallet className="h-3.5 w-3.5" />
          Budget: ₹{parsedQuery.budget.toLocaleString("en-IN")}
        </span>
      )}
      {parsedQuery.purpose && (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
          <Target className="h-3.5 w-3.5" />
          Purpose: {parsedQuery.purpose}
        </span>
      )}
      {parsedQuery.preferences.map((pref) => (
        <span
          key={pref}
          className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700"
        >
          {pref}
        </span>
      ))}
    </div>
  );
}
