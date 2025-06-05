'use client';
import { useEffect, useState } from 'react';

/**
 * Small wrapper around the native fetch API. It performs the request when the
 * provided `url` changes and exposes `data`, `loading` and `error` state.
 */
export default function useFetchData<T = unknown>(
  url: string | null,
  options?: RequestInit
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!url) return;

    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(res.statusText);
        const json = (await res.json()) as T;
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setError(err as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [url, options]);

  return { data, loading, error };
}
