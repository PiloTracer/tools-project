"use client";

import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";

export function DropdownMenu({
  trigger,
  children,
}: {
  trigger: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const focusItem = useCallback((dir: "first" | "last" | "next" | "prev") => {
    if (!menuRef.current) return;
    const items = menuRef.current.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not([disabled])');
    if (items.length === 0) return;
    const current = document.activeElement;
    let idx = Array.from(items).indexOf(current as HTMLButtonElement);
    if (dir === "first") idx = 0;
    else if (dir === "last") idx = items.length - 1;
    else if (dir === "next") idx = Math.min(idx + 1, items.length - 1);
    else if (dir === "prev") idx = Math.max(idx - 1, 0);
    items[idx]?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        return;
      }
      if (e.key === "ArrowDown") { e.preventDefault(); focusItem("next"); }
      if (e.key === "ArrowUp") { e.preventDefault(); focusItem("prev"); }
    };
    document.addEventListener("mousedown", handler);
    document.addEventListener("keydown", keyHandler);
    focusItem("first");
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("keydown", keyHandler);
    };
  }, [open, focusItem]);

  return (
    <div ref={ref} style={{ position: "relative", display: "inline-flex" }}>
      <div
        ref={triggerRef}
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen(!open); } }}
      >
        {trigger}
      </div>
      {open ? (
        <div
          ref={menuRef}
          role="menu"
          style={{
            position: "absolute",
            right: 0,
            top: "100%",
            marginTop: "0.25rem",
            zIndex: "var(--z-dropdown)",
            background: "var(--surface-overlay)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-md)",
            minWidth: "160px",
            padding: "0.25rem 0",
          }}
          onClick={(e) => { e.stopPropagation(); setOpen(false); triggerRef.current?.focus(); }}
        >
          {children}
        </div>
      ) : null}
    </div>
  );
}

export function DropdownItem({
  children,
  onClick,
  danger,
  disabled,
}: {
  children: ReactNode;
  onClick?: () => void;
  danger?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      onClick={onClick}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        padding: "0.45rem 0.85rem",
        fontSize: "0.88rem",
        background: "none",
        border: "none",
        cursor: disabled ? "default" : "pointer",
        color: danger ? "var(--danger)" : "var(--text)",
        opacity: disabled ? 0.4 : 1,
        fontFamily: "inherit",
      }}
      onMouseEnter={(e) => {
        if (!disabled) e.currentTarget.style.background = "var(--surface)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "none";
      }}
    >
      {children}
    </button>
  );
}
