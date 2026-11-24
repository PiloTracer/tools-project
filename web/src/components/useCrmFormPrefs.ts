"use client";

import { useCallback, useEffect, useState } from "react";

import {
  type CrmFormFieldKey,
  readCachedCrmFormFields,
  resolveCrmFormFields,
  writeCachedCrmFormFields,
} from "@/shared/crm-form-prefs";

export function useCrmFormPrefs() {
  const [fields, setFields] = useState<Record<CrmFormFieldKey, boolean>>(readCachedCrmFormFields);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const cached = readCachedCrmFormFields();
      if (!cancelled) setFields(cached);
      try {
        const r = await fetch("/api/auth/me");
        if (!r.ok) {
          if (!cancelled) setReady(true);
          return;
        }
        const data = (await r.json()) as {
          ui_preferences?: { crm_form_fields?: Partial<Record<CrmFormFieldKey, boolean>> };
        };
        const resolved = resolveCrmFormFields(data.ui_preferences?.crm_form_fields);
        writeCachedCrmFormFields(resolved);
        if (!cancelled) {
          setFields(resolved);
          setReady(true);
        }
      } catch {
        if (!cancelled) setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const setField = useCallback(async (key: CrmFormFieldKey, visible: boolean) => {
    setFields((prev) => {
      const next = { ...prev, [key]: visible };
      writeCachedCrmFormFields(next);
      void fetch("/api/auth/me/preferences", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ crm_form_fields: { [key]: visible } }),
      }).catch(() => {
        /* local cache already updated; server sync best-effort */
      });
      return next;
    });
  }, []);

  const isVisible = useCallback((key: CrmFormFieldKey) => fields[key] !== false, [fields]);

  return { fields, setField, isVisible, ready };
}
