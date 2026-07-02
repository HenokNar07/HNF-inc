import { useCallback, useState } from "react";
import { analyzePortfolio, ApiError } from "../api/client";
import type { AnalyzeRequest, MVOResult } from "../api/types";

interface UseAnalyzeState {
  result: MVOResult | null;
  loading: boolean;
  error: string | null;
}

export function useAnalyze() {
  const [state, setState] = useState<UseAnalyzeState>({
    result: null,
    loading: false,
    error: null,
  });

  const analyze = useCallback(async (request: AnalyzeRequest) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await analyzePortfolio(request);
      setState({ result, loading: false, error: null });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Try again.";
      // Keep the last successful result on screen rather than clearing it --
      // a failed retry (e.g. a typo'd ticker) shouldn't blank out the chart
      // the user was just looking at.
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  return { ...state, analyze };
}
