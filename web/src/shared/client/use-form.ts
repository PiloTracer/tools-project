"use client";

import { useState, useCallback } from "react";

export function useForm<T extends Record<string, unknown>>(initial: T) {
  const [values, setValues] = useState<T>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const reset = useCallback((vals?: Partial<T>) => {
    setValues(vals ? { ...initial, ...vals } : initial);
    setError(null);
  }, [initial]);

  const clearError = useCallback(() => setError(null), []);

  return { values, busy, error, set, setBusy, setError, reset, clearError };
}
