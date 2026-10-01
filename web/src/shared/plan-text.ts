/**
 * Plan-import text presentation helpers.
 *
 * The plan-sync import writes a task's *title* as the plan's (technical) cell text and its
 * *description* as `## Acceptance` + a provenance line (`**Provenance:** plan_ref=…, files=…`).
 * That is the right source of truth but a poor reading experience, so this module derives a
 * short human label plus structured acceptance/technical parts.
 *
 * Tolerant by design: it accepts the current inline provenance format and a future
 * `## Technical details` block, and falls back to the raw text when nothing matches.
 */

export type TaskTech = {
  planRef?: string;
  planVersion?: string;
  source?: string;
  files: string[];
  frNfr: string[];
  complexity?: string;
  /** Recognised `key=value` / `key: value` pairs, in source order. */
  pairs: { key: string; value: string }[];
};

export type ParsedTaskText = {
  /** Short, human-readable label (first clause of the technical title). */
  label: string;
  /** The original title, always. */
  fullTitle: string;
  /** The technical remainder of the title after the first clause (markdown, may be ""). */
  remainder: string;
  /** Acceptance criteria, one item per entry (may be empty). */
  acceptance: string[];
  /** Provenance found in the description (may be empty). */
  tech: TaskTech;
  hasTech: boolean;
  /** Description body to fall back to verbatim when no markers were recognised. */
  plainFallback: string | null;
};

const DASH_SPLIT = /\s+[—–]\s+/;
const HEADING_RE = /^#{1,6}\s*(.+?)\s*$/;
const ACCEPTANCE_RE = /^(?:#{2,6}\s*|\*\*\s*)?acceptance(?:\s*criteria)?\s*(?:\*\*)?:?\s*$/i;
const TECH_HEADING_RE = /^(?:#{2,6}\s*|\*\*\s*)?(?:technical\s+details|provenance|source)\b/i;
const PROVENANCE_RE = /^\*\*\s*provenance\s*:?\s*\*\*\s*(.+)$/i;
const BULLET_RE = /^(?:[-*+]\s*|\d+[.)]\s*|\[[ xX]\]\s*)+/;

function stripMd(s: string): string {
  return s
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .replace(/`/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function splitItems(line: string): string[] {
  return line
    .split(";")
    .map((part) => stripMd(part.replace(BULLET_RE, "")))
    .map((part) => part.replace(/^[.,\s]+/, "").trim())
    .filter((part) => part.length > 0);
}

/** First clause of a technical title, with markdown markers removed. */
function labelFromTitle(title: string, max = 120): { label: string; remainder: string } {
  const clean = stripMd(title);
  const parts = clean.split(DASH_SPLIT);
  let head = (parts[0] ?? "").trim();
  let tail = parts.length > 1 ? parts.slice(1).join(" — ").trim() : "";
  if (!head) {
    head = clean;
    tail = "";
  }
  if (!tail) {
    // No em-dash: fall back to the first sentence when the title is long.
    const dot = head.indexOf(". ");
    if (dot > 40 && dot < head.length - 1) {
      tail = head.slice(dot + 2).trim();
      head = head.slice(0, dot + 1).trim();
    }
  }
  const label = head.length > max ? `${head.slice(0, max - 1).trimEnd()}…` : head;
  return { label, remainder: tail };
}

function pushPair(pairs: TaskTech["pairs"], rawKey: string, rawValue: string): void {
  const key = stripMd(rawKey).replace(/[:,]$/, "").toLowerCase();
  const value = rawValue.trim();
  if (key && value) pairs.push({ key, value });
}

/** Parse `key=value` items from the legacy `**Provenance:** a=1, b=2` line. */
function parseInlineProvenance(text: string): TaskTech {
  const tech: TaskTech = { files: [], frNfr: [], pairs: [] };
  const grab = (key: string): string | undefined => {
    const quoted = new RegExp(`${key}\\s*=\\s*([\\s\\S]*?)(?=,\\s*[a-z_]+\\s*=|$)`, "i");
    const m = text.match(quoted);
    return m ? m[1].trim() : undefined;
  };
  const planRef = grab("plan_ref");
  const planVersion = grab("plan_version");
  const source = grab("source");
  const files = grab("files");
  const frNfr = grab("fr_nfr");
  const complexity = grab("complexity");
  if (planRef) tech.planRef = stripMd(planRef);
  if (planVersion) tech.planVersion = stripMd(planVersion);
  if (source) tech.source = stripMd(source);
  if (complexity) tech.complexity = stripMd(complexity);
  if (files) tech.files = files.split(/,\s*(?=`|[A-Za-z0-9._*(])/).map(stripMd).filter(Boolean);
  if (frNfr) tech.frNfr = frNfr.split(/,\s*/).map(stripMd).filter(Boolean);
  if (planRef) pushPair(tech.pairs, "plan_ref", stripMd(planRef));
  if (planVersion) pushPair(tech.pairs, "plan_version", stripMd(planVersion));
  if (source) pushPair(tech.pairs, "source", stripMd(source));
  if (complexity) pushPair(tech.pairs, "complexity", stripMd(complexity));
  if (files) pushPair(tech.pairs, "files", tech.files.join(", "));
  if (frNfr) pushPair(tech.pairs, "fr_nfr", tech.frNfr.join(", "));
  return tech;
}

export function parseTaskText(title: string, description: string | null | undefined): ParsedTaskText {
  const fullTitle = title ?? "";
  const { label, remainder } = labelFromTitle(fullTitle);
  const body = (description ?? "").replace(/\r\n/g, "\n");
  const acceptance: string[] = [];
  const tech: TaskTech = { files: [], frNfr: [], pairs: [] };
  const leftovers: string[] = [];

  let section: "none" | "acceptance" | "tech" = "none";
  let sawMarker = false;

  for (const rawLine of body.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;
    if (/^-{3,}$/.test(line)) {
      sawMarker = true;
      continue;
    }
    const inline = line.match(PROVENANCE_RE);
    if (inline) {
      sawMarker = true;
      Object.assign(tech, mergeTech(tech, parseInlineProvenance(inline[1])));
      section = "tech";
      continue;
    }
    const heading = line.match(HEADING_RE);
    if (heading) {
      sawMarker = true;
      const text = heading[1];
      if (ACCEPTANCE_RE.test(text)) {
        section = "acceptance";
        continue;
      }
      if (TECH_HEADING_RE.test(text)) {
        section = "tech";
        continue;
      }
      section = "none";
      leftovers.push(line);
      continue;
    }
    const bullet = line.match(/^(?:[-*+]\s*|\d+[.)]\s*)(.+)$/);
    if (section === "tech" || (section === "none" && looksLikePairs(line))) {
      sawMarker = true;
      section = "tech";
      for (const item of line.replace(/^[-*+]\s*/, "").split(/\s*·\s*|\s*\|\s*/)) {
        const kv = item.match(/^\s*([A-Za-z_][A-Za-z0-9_ ]*)\s*[:=]\s*(.+)$/);
        if (kv) pushPair(tech.pairs, kv[1], kv[2]);
      }
      continue;
    }
    if (section === "acceptance") {
      sawMarker = true;
      acceptance.push(...splitItems(bullet ? bullet[1] : line));
      continue;
    }
    leftovers.push(line);
  }

  const hasTech = tech.pairs.length > 0 || Boolean(tech.planRef || tech.source || tech.planVersion);
  const plainFallback = sawMarker ? (leftovers.length ? leftovers.join("\n\n") : null) : body.trim() || null;

  return { label, fullTitle, remainder, acceptance, tech, hasTech, plainFallback };
}

function looksLikePairs(line: string): boolean {
  return /(?:^|[\s·|])(plan_ref|plan_version|source|files|fr_nfr|complexity)\s*[:=]/i.test(line);
}

function mergeTech(base: TaskTech, extra: TaskTech): TaskTech {
  return {
    planRef: base.planRef ?? extra.planRef,
    planVersion: base.planVersion ?? extra.planVersion,
    source: base.source ?? extra.source,
    files: base.files.length ? base.files : extra.files,
    frNfr: base.frNfr.length ? base.frNfr : extra.frNfr,
    complexity: base.complexity ?? extra.complexity,
    pairs: [...base.pairs, ...extra.pairs],
  };
}

/** Short label for list/board views — never throws, always returns something readable. */
export function taskLabel(title: string): string {
  return parseTaskText(title, null).label;
}

export type MilestoneProgress = { total: number; done: number; percent: number };

export function milestoneProgress(total: number, done: number): MilestoneProgress {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return { total, done, percent: pct };
}
