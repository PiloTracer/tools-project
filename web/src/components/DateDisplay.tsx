"use client";

import { useEffect, useMemo, useState } from "react";

function relativeTime(date: Date, now: Date): string {
  const diffMs = now.getTime() - date.getTime();
  const absDiff = Math.abs(diffMs);
  const seconds = Math.floor(absDiff / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

function absoluteDate(date: Date): string {
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  });
}

export function DateDisplay({ date: dateStr }: { date: string }) {
  const date = useMemo(() => new Date(dateStr), [dateStr]);
  const [label, setLabel] = useState(() => relativeTime(date, new Date()));

  useEffect(() => {
    const interval = setInterval(() => {
      setLabel(relativeTime(date, new Date()));
    }, 30_000);
    return () => clearInterval(interval);
  }, [date]);

  return (
    <span title={absoluteDate(date)}>
      {label}
    </span>
  );
}
