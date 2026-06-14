"use client";

import { useMemo, useState } from "react";
import { ShoppingBag, AlertCircle } from "lucide-react";
import SearchBar from "@/components/SearchBar";
import FiltersPanel from "@/components/FiltersPanel";
import ProductCard from "@/components/ProductCard";
import ComparisonTable from "@/components/ComparisonTable";
import RecommendationSummary from "@/components/RecommendationSummary";
import QuerySummary from "@/components/QuerySummary";
import { searchProducts } from "@/lib/api";
import type { SearchProductsResponse } from "@/types/api";
import type { BadgeType } from "@/components/RecommendationBadge";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchProductsResponse | null>(null);

  const [budget, setBudget] = useState(200000);
  const [minRating, setMinRating] = useState(0);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  const handleSearch = async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await searchProducts(query);
      setResult(response);
      setBudget(response.parsed_query.budget || 200000);
      setSelectedSources([]);
      setMinRating(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const availableSources = useMemo(() => {
    if (!result) return [];
    return Array.from(new Set(result.products.map((p) => p.source)));
  }, [result]);

  const filteredProducts = useMemo(() => {
    if (!result) return [];
    return result.products.filter((p) => {
      if (p.price !== null && p.price > budget) return false;
      if (minRating > 0 && (p.rating || 0) < minRating) return false;
      if (selectedSources.length > 0 && !selectedSources.includes(p.source)) return false;
      return true;
    });
  }, [result, budget, minRating, selectedSources]);

  const toggleSource = (source: string) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  const badgeForProduct = (title: string): BadgeType | undefined => {
    if (!result) return undefined;
    const { best_choice, budget_choice, premium_choice } = result.recommendation;
    if (best_choice?.title === title) return "best";
    if (budget_choice?.title === title) return "budget";
    if (premium_choice?.title === title) return "premium";
    return undefined;
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-600 text-white">
          <ShoppingBag className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">AI Shopping Agent</h1>
          <p className="text-sm text-slate-500">
            Tell me what you need, and I&apos;ll search the web and find the best deals for you.
          </p>
        </div>
      </header>

      <div className="mb-8">
        <SearchBar onSearch={handleSearch} loading={loading} />
      </div>

      {error && (
        <div className="mb-6 flex items-center gap-2 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle className="h-5 w-5" />
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-20 text-slate-500">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
          <p className="text-sm">
            Searching Amazon, Flipkart, Croma and more — this can take a minute...
          </p>
        </div>
      )}

      {!loading && result && (
        <div className="space-y-8">
          <section>
            <QuerySummary parsedQuery={result.parsed_query} />
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Top Recommendations</h2>
            <RecommendationSummary
              bestChoice={result.recommendation.best_choice}
              budgetChoice={result.recommendation.budget_choice}
              premiumChoice={result.recommendation.premium_choice}
              whyRecommended={result.recommendation.why_recommended}
            />
          </section>

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-4">
            <div className="lg:col-span-1">
              <FiltersPanel
                budget={budget}
                onBudgetChange={setBudget}
                minRating={minRating}
                onMinRatingChange={setMinRating}
                selectedSources={selectedSources}
                availableSources={availableSources}
                onToggleSource={toggleSource}
              />
            </div>

            <div className="lg:col-span-3">
              <h2 className="mb-3 text-lg font-semibold text-slate-900">
                Products ({filteredProducts.length})
              </h2>
              {filteredProducts.length === 0 ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
                  No products match your current filters.
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredProducts.map((product, idx) => (
                    <ProductCard
                      key={`${product.source}-${idx}`}
                      product={product}
                      badge={badgeForProduct(product.title)}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {result.recommendation.comparison_table.length > 0 && (
            <section>
              <h2 className="mb-3 text-lg font-semibold text-slate-900">Comparison Table</h2>
              <ComparisonTable rows={result.recommendation.comparison_table} />
            </section>
          )}
        </div>
      )}

      {!loading && !result && !error && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 py-20 text-center text-slate-400">
          <ShoppingBag className="h-10 w-10" />
          <p className="text-sm">
            Start by typing a query above, e.g. &quot;Best laptop under ₹50,000 for coding&quot;
          </p>
        </div>
      )}
    </main>
  );
}
