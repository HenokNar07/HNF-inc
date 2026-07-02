import { useCallback, useState } from "react";
import { explainResult, ApiError } from "../api/client";
import type { MVOResult } from "../api/types";

interface UseExplainState {
  explanation: string | null;
  loading: boolean;
  error: string | null;
}

export function useExplain() {
  const [state, setState] = useState<UseExplainState>({
    explanation: null,
    loading: false,
    error: null,
  });

  const explain = useCallback(async (result: MVOResult) => {
    setState({ explanation: null, loading: true, error: null });
    try {
      const explanation = await explainResult(result);
      setState({ explanation, loading: false, error: null });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong. Try again.";
      setState({ explanation: null, loading: false, error: message });
    }
  }, []);

  const reset = useCallback(() => {
    setState({ explanation: null, loading: false, error: null });
  }, []);

  return { ...state, explain, reset };
}
