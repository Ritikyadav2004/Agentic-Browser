import type { ComparisonRow } from "@/types/api";

interface ComparisonTableProps {
  rows: ComparisonRow[];
}

function ScoreCell({ value }: { value: number | null | undefined }) {
  if (value === null || value === undefined) {
    return <span className="text-slate-300 dark:text-zinc-650">—</span>;
  }
  const pct = Math.max(0, Math.min(10, value)) * 10;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100 dark:bg-zinc-800">
        <div className="h-full bg-brand-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-slate-600 dark:text-zinc-400">{value.toFixed(1)}</span>
    </div>
  );
}

export default function ComparisonTable({ rows }: ComparisonTableProps) {
  if (!rows.length) {
    return null;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm scrollbar-thin dark:border-zinc-800 dark:bg-zinc-900">
      <table className="min-w-full divide-y divide-slate-100 dark:divide-zinc-800 text-sm">
        <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-zinc-900/50 dark:text-zinc-450">
          <tr>
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Price</th>
            <th className="px-4 py-3">Rating</th>
            <th className="px-4 py-3">Performance</th>
            <th className="px-4 py-3">Durability</th>
            <th className="px-4 py-3">Value</th>
            <th className="px-4 py-3">Use-case fit</th>
            <th className="px-4 py-3">Overall</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-zinc-800">
          {rows.map((row, idx) => (
            <tr key={`${row.source}-${idx}`} className="hover:bg-slate-50 dark:hover:bg-zinc-800/30">
              <td className="max-w-xs px-4 py-3 font-medium text-slate-800 dark:text-zinc-200">
                {row.url ? (
                  <a
                    href={row.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="line-clamp-2 hover:text-brand-700 hover:underline dark:hover:text-brand-400"
                  >
                    {row.title}
                  </a>
                ) : (
                  <span className="line-clamp-2">{row.title}</span>
                )}
              </td>
              <td className="px-4 py-3 text-slate-500 dark:text-zinc-400">{row.source}</td>
              <td className="px-4 py-3 font-semibold text-slate-900 dark:text-zinc-50">
                {row.price !== null ? `₹${row.price.toLocaleString("en-IN")}` : "—"}
              </td>
              <td className="px-4 py-3 text-slate-600 dark:text-zinc-350">
                {row.rating !== null ? `${row.rating.toFixed(1)} ★` : "—"}
              </td>
              <td className="px-4 py-3">
                <ScoreCell value={row.performance_score} />
              </td>
              <td className="px-4 py-3">
                <ScoreCell value={row.durability_score} />
              </td>
              <td className="px-4 py-3">
                <ScoreCell value={row.value_for_money_score} />
              </td>
              <td className="px-4 py-3">
                <ScoreCell value={row.use_case_fit_score} />
              </td>
              <td className="px-4 py-3 font-semibold text-slate-900 dark:text-zinc-50">
                {row.overall_score !== null && row.overall_score !== undefined
                  ? row.overall_score.toFixed(1)
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
