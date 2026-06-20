"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import type { MeResponse } from "@/shared/types/me";

export function ClientRedirect({ me }: { me: MeResponse | null }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (
      me &&
      me.client_contact_id &&
      !me.is_superuser &&
      !pathname.startsWith("/client/")
    ) {
      router.replace("/client/dashboard");
    }
  }, [me, pathname, router]);

  return null;
}
