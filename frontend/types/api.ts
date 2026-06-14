export interface ParsedQuery {
  category: string;
  budget: number | null;
  min_budget: number | null;
  purpose: string | null;
  preferences: string[];
  raw_query: string;
  search_keywords: string;
  sites: string[];
}

export interface ProductSpec {
  source: string;
  title: string;
  price: number | null;
  currency: string;
  rating: number | null;
  reviews_count: number | null;
  availability: string | null;
  specifications: Record<string, unknown>;
  url: string | null;
  image_url: string | null;
  scraped_at: string;
}

export interface ComparisonRow {
  title: string;
  source: string;
  price: number | null;
  rating: number | null;
  reviews_count: number | null;
  performance_score: number | null;
  durability_score: number | null;
  value_for_money_score: number | null;
  use_case_fit_score: number | null;
  overall_score: number | null;
  url: string | null;
  reason?: string;
}

export interface RecommendationResult {
  best_choice: Partial<ComparisonRow>;
  budget_choice: Partial<ComparisonRow>;
  premium_choice: Partial<ComparisonRow>;
  comparison_table: ComparisonRow[];
  why_recommended: string;
}

export interface SearchProductsResponse {
  parsed_query: ParsedQuery;
  products: ProductSpec[];
  recommendation: RecommendationResult;
  session_id: string;
}

export interface SearchHistoryItem {
  session_id: string;
  user_id: string;
  query: string;
  parsed_query: Record<string, unknown>;
  created_at: string;
}

export interface SearchHistoryResponse {
  items: SearchHistoryItem[];
}
