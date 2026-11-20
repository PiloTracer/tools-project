export type WorkTypeMark = {
  id: string;
  key: string;
  name: string;
};

const RESERVED = [
  { key: "programming", hue: 199 },
  { key: "administrative", hue: 36 },
  { key: "documentation", hue: 152 },
] as const;

function hueDistance(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
}

/** Stable hue. The three starter types keep fixed colors; added types avoid those hues. */
export function workTypeHue(key: string): number {
  const known = RESERVED.find((row) => row.key === key);
  if (known) return known.hue;
  let n = 0;
  for (let i = 0; i < key.length; i += 1) n = (n * 33 + key.charCodeAt(i)) >>> 0;
  let hue = n % 360;
  if (RESERVED.some((row) => hueDistance(hue, row.hue) < 28)) hue = (hue + 70) % 360;
  return hue;
}

function markShape(key: string): "square" | "circle" | "bar" | "diamond" {
  if (key === "programming") return "square";
  if (key === "administrative") return "circle";
  if (key === "documentation") return "bar";
  return "diamond";
}

export function findWorkType(
  types: WorkTypeMark[],
  id: string | null | undefined,
): WorkTypeMark | null {
  if (!id) return null;
  return types.find((row) => row.id === id) ?? null;
}

export function WorkTypeBadge({ workType }: { workType: WorkTypeMark }) {
  const hue = workTypeHue(workType.key);
  return (
    <span
      className={`work-type work-type--${markShape(workType.key)}`}
      style={{ ["--wt-h" as string]: String(hue) }}
      title={workType.name}
    >
      <span className="work-type__mark" aria-hidden="true" />
      {workType.name}
    </span>
  );
}
