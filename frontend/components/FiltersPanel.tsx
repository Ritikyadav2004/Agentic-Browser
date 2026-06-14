"use client";

import { SlidersHorizontal } from "lucide-react";

interface FiltersPanelProps {
  budget: number;
  onBudgetChange: (value: number) => void;
  minRating: number;
  onMinRatingChange: (value: number) => void;
  selectedSources: string[];
  availableSources: string[];
  onToggleSource: (source: string) => void;
}

const STEP = 1000;

export default function FiltersPanel({
  budget,
  onBudgetChange,
  minRating,
  onMinRatingChange,
  selectedSources,
  availableSources,
  onToggleSource,
}: FiltersPanelProps) {
  const maxLimit = Math.max(200000, budget * 1.5);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700">
        <SlidersHorizontal className="h-4 w-4" />
        Filters
      </div>

      <div className="mb-5">
        <div className="mb-1 flex items-center justify-between text-sm text-slate-600">
          <span>Max budget</span>
          <span className="font-semibold text-slate-900">₹{budget.toLocaleString("en-IN")}</span>
        </div>
        <input
          type="range"
          min={0}
          max={maxLimit}
          step={STEP}
          value={budget}
          onChange={(e) => onBudgetChange(Number(e.target.value))}
          className="w-full accent-brand-600"
        />
        <div className="mt-1 flex justify-between text-xs text-slate-400">
          <span>₹0</span>
          <span>₹{maxLimit.toLocaleString("en-IN")}</span>
        </div>
      </div>

      <div className="mb-5">
        <div className="mb-1 flex items-center justify-between text-sm text-slate-600">
          <span>Minimum rating</span>
          <span className="font-semibold text-slate-900">{minRating.toFixed(1)}+</span>
        </div>
        <input
          type="range"
          min={0}
          max={5}
          step={0.5}
          value={minRating}
          onChange={(e) => onMinRatingChange(Number(e.target.value))}
          className="w-full accent-brand-600"
        />
      </div>

      <div>
        <div className="mb-2 text-sm text-slate-600">Sources</div>
        <div className="flex flex-wrap gap-2">
          {availableSources.map((source) => {
            const active = selectedSources.includes(source);
            return (
              <button
                key={source}
                type="button"
                onClick={() => onToggleSource(source)}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                  active
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
                }`}
              >
                {source}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
