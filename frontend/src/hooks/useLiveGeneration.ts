import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchHealth,
  pollGeneration,
  submitGeneration,
  type GenerateOptions,
  type HealthResponse,
} from "../api/client";

export function useLiveGeneration(debounceMs = 600) {
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<
    "idle" | "waiting" | "generating" | "error"
  >("idle");
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestGenRef = useRef(0);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({ status: "offline", model_loaded: false, device: "unknown" })
      );
    const id = setInterval(() => {
      fetchHealth().then(setHealth).catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, []);

  const runGeneration = useCallback(
    async (prompt: string, sketch: string, options?: GenerateOptions) => {
      if (!prompt.trim()) return;

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const gen = ++requestGenRef.current;
      setStatus("generating");
      setError(null);

      try {
        const { job_id } = await submitGeneration(
          {
            prompt: prompt.trim(),
            sketch,
            controlnet_scale: options?.controlnet_scale,
            guidance_scale: options?.guidance_scale,
          },
          controller.signal
        );

        const result = await pollGeneration(job_id, controller.signal, 300);

        if (gen !== requestGenRef.current) return;

        if (result.status === "completed" && result.image) {
          if (result.image.length < 100) {
            setError("Empty image from server — restart backend and try again.");
            setStatus("error");
            return;
          }
          setPreview(result.image);
          setStatus("idle");
        } else if (result.status === "cancelled") {
          setStatus("idle");
        } else {
          setError(result.error ?? "Generation failed");
          setStatus("error");
        }
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        if (gen !== requestGenRef.current) return;
        setError((e as Error).message);
        setStatus("error");
      }
    },
    []
  );

  const scheduleGeneration = useCallback(
    (prompt: string, getSketch: () => string, options?: GenerateOptions) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      setStatus("waiting");

      debounceRef.current = setTimeout(() => {
        const sketch = getSketch();
        if (!sketch) return;
        void runGeneration(prompt, sketch, options);
      }, debounceMs);
    },
    [debounceMs, runGeneration]
  );

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, []);

  const clearPreview = useCallback(() => {
    setPreview(null);
    setError(null);
    setStatus("idle");
  }, []);

  return {
    preview,
    status,
    error,
    health,
    scheduleGeneration,
    clearPreview,
  };
}
