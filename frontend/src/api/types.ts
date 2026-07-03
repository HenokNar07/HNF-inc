/**
 * Hand-mirrors backend/app/schemas.py and math_engine/types.py. Kept in sync
 * manually rather than codegen'd -- the schema is small and stable enough
 * that a generator would be more ceremony than it's worth right now.
 */

export interface AssetStats {
  ticker: string;
  mean_return: number;
  std_dev: number;
  beta: number;
  factor_betas: Record<string, number> | null;
}

export interface PortfolioStats {
  weights: Record<string, number>;
  expected_return: number;
  std_dev: number;
  sharpe_ratio: number;
}

export interface FrontierPoint {
  expected_return: number;
  std_dev: number;
  weights: Record<string, number>;
}

export type ReturnModel = "historical" | "fama_french";

export interface MVOResult {
  tickers: string[];
  lookback_years: number;
  return_model: ReturnModel;
  risk_free_rate: number;
  risk_free_source: "treasury" | "fallback";
  frontier: FrontierPoint[];
  max_sharpe: PortfolioStats;
  min_variance: PortfolioStats;
  current_portfolio: PortfolioStats;
  asset_stats: AssetStats[];
  warnings: string[];
}

export interface AnalyzeRequest {
  tickers: string[];
  weights: number[];
  lookback_years?: number;
  max_weight?: number | null;
  n_frontier_points?: number;
  return_model?: ReturnModel;
}
