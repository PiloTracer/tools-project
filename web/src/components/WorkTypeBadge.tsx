export type WorkTypeMark = {
  id: string;
  key: string;
  name: string;
};

type MarkShape = "square" | "circle" | "bar" | "diamond";

/** Starter keys. Hues stay fixed so a type does not change color between releases. */
const STARTERS: readonly { key: string; hue: number; shape: MarkShape }[] = [
  { key: "programming", hue: 199, shape: "square" },
  { key: "administrative", hue: 36, shape: "circle" },
  { key: "documentation", hue: 152, shape: "bar" },
  { key: "legal", hue: 64, shape: "square" },
  { key: "miscellaneous", hue: 86, shape: "circle" },
  { key: "research", hue: 108, shape: "bar" },
  { key: "design", hue: 130, shape: "diamond" },
  { key: "testing", hue: 174, shape: "square" },
  { key: "defect", hue: 221, shape: "circle" },
  { key: "support", hue: 243, shape: "bar" },
  { key: "operations", hue: 265, shape: "diamond" },
  { key: "planning", hue: 287, shape: "square" },
  { key: "security", hue: 309, shape: "circle" },
  { key: "data", hue: 331, shape: "bar" },
  { key: "finance", hue: 353, shape: "diamond" },
];

function hueDistance(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return Math.min(d, 360 - d);
}

/** Stable hue. Starter types keep fixed colors; a custom type avoids sitting on one. */
export function workTypeHue(key: string): number {
  const known = STARTERS.find((row) => row.key === key);
  if (known) return known.hue;
  let n = 0;
  for (let i = 0; i < key.length; i += 1) n = (n * 33 + key.charCodeAt(i)) >>> 0;
  let hue = n % 360;
  if (STARTERS.some((row) => hueDistance(hue, row.hue) < 12)) hue = (hue + 9) % 360;
  return hue;
}

function markShape(key: string): MarkShape {
  return STARTERS.find((row) => row.key === key)?.shape ?? "diamond";
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
