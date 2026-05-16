"use client";

import { useCallback, useState } from "react";

export type PendingImage = { key: string; file: File; url: string };

export function filterImageFiles(files: Iterable<File>): File[] {
  return Array.from(files).filter((f) => f.type.startsWith("image/"));
}

export function clipboardImageFiles(ev: ClipboardEvent): File[] {
  const items = ev.clipboardData?.items;
  if (!items) return [];
  const out: File[] = [];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    if (it.kind === "file" && it.type.startsWith("image/")) {
      const f = it.getAsFile();
      if (f) out.push(f);
    }
  }
  return out;
}

export function usePendingImages() {
  const [pending, setPending] = useState<PendingImage[]>([]);

  const addFiles = useCallback((files: File[]) => {
    const imgs = filterImageFiles(files);
    if (!imgs.length) return;
    setPending((prev) => {
      const next = [...prev];
      for (const file of imgs) {
        next.push({ key: crypto.randomUUID(), file, url: URL.createObjectURL(file) });
      }
      return next;
    });
  }, []);

  const remove = useCallback((key: string) => {
    setPending((prev) => {
      const hit = prev.find((x) => x.key === key);
      if (hit) URL.revokeObjectURL(hit.url);
      return prev.filter((x) => x.key !== key);
    });
  }, []);

  const clear = useCallback(() => {
    setPending((prev) => {
      prev.forEach((p) => URL.revokeObjectURL(p.url));
      return [];
    });
  }, []);

  return { pending, addFiles, remove, clear };
}
