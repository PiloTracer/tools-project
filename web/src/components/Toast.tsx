"use client";

import { useEffect, useState } from "react";

import { errorTextFromBody } from "@/shared/client/api";

type ToastKind = "success" | "error";

let toastQueue: Array<{ id: number; message: string; kind: ToastKind }> = [];
let toastId = 0;
let listeners: Array<() => void> = [];

function notify() {
  listeners.forEach((l) => l());
}

export function toast(message: unknown, kind: ToastKind = "success") {
  // Callers often pass a parsed API error body. A FastAPI validation error is an
  // array of objects; handing that to React as a child crashes the page
  // (React error #31), so normalize anything that is not a plain string.
  const text = typeof message === "string" ? message : errorTextFromBody(message);
  const id = ++toastId;
  toastQueue = [...toastQueue, { id, message: text, kind }];
  notify();
  setTimeout(() => {
    toastQueue = toastQueue.filter((t) => t.id !== id);
    notify();
  }, 3500);
}

export function ToastContainer() {
  const [items, setItems] = useState<typeof toastQueue>([]);

  useEffect(() => {
    const listener = () => setItems([...toastQueue]);
    listeners.push(listener);
    return () => {
      listeners = listeners.filter((l) => l !== listener);
    };
  }, []);

  if (items.length === 0) return null;

  return (
    <div
      aria-live="polite"
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        zIndex: "var(--z-toast)",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        maxWidth: "380px",
      }}
    >
      {items.map((t) => (
        <div
          key={t.id}
          style={{
            padding: "0.65rem 1rem",
            borderRadius: "var(--radius-md)",
            background: t.kind === "success" ? "rgb(74 222 128 / 15%)" : "rgb(251 113 133 / 15%)",
            border: `1px solid ${t.kind === "success" ? "rgb(74 222 128 / 35%)" : "rgb(251 113 133 / 35%)"}`,
            color: t.kind === "success" ? "var(--success)" : "var(--danger)",
            fontSize: "0.9rem",
            fontWeight: 500,
            boxShadow: "var(--shadow-md)",
          }}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
