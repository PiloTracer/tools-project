"use client";

import { useCallback, useState } from "react";

export type PendingAttachment = { key: string; file: File; url?: string };

export function filterImageFiles(files: Iterable<File>): File[] {
  return Array.from(files).filter((f) => f.type.startsWith("image/"));
}

/** Pass-through — server `file_sniff` does real MIME validation via magic bytes. */
export function filterUploadableFiles(files: Iterable<File>): File[] {
  return Array.from(files).filter((f) => f.name.length > 0);
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

export function clipboardUploadableFiles(ev: ClipboardEvent): File[] {
  const items = ev.clipboardData?.items;
  if (!items) return [];
  const raw: File[] = [];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    if (it.kind !== "file") continue;
    const f = it.getAsFile();
    if (f) raw.push(f);
  }
  return filterUploadableFiles(raw);
}

export function usePendingImages() {
  const [pending, setPending] = useState<PendingAttachment[]>([]);

  const addFiles = useCallback((files: File[]) => {
    const usable = filterUploadableFiles(files);
    if (!usable.length) return;
    setPending((prev) => {
      const next = [...prev];
      for (const file of usable) {
        const url = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
        next.push({ key: crypto.randomUUID(), file, url });
      }
      return next;
    });
  }, []);

  const remove = useCallback((key: string) => {
    setPending((prev) => {
      const hit = prev.find((x) => x.key === key);
      if (hit?.url) URL.revokeObjectURL(hit.url);
      return prev.filter((x) => x.key !== key);
    });
  }, []);

  const clear = useCallback(() => {
    setPending((prev) => {
      prev.forEach((p) => {
        if (p.url) URL.revokeObjectURL(p.url);
      });
      return [];
    });
  }, []);

  return { pending, addFiles, remove, clear };
}
