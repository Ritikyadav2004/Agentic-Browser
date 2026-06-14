import type { SearchHistoryResponse, SearchProductsResponse } from "@/types/api";

const API_BASE = "/api";

export async function searchProducts(
  query: string,
  userId: string = "anonymous"
): Promise<SearchProductsResponse> {
  const res = await fetch(`${API_BASE}/search-products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, user_id: userId }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Search failed (${res.status}): ${text}`);
  }

  return res.json();
}

export async function getSearchHistory(
  userId: string = "anonymous"
): Promise<SearchHistoryResponse> {
  const res = await fetch(`${API_BASE}/search-history?user_id=${encodeURIComponent(userId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch search history (${res.status})`);
  }
  return res.json();
}
