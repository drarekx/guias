// Índice de búsqueda cross-game
import { pagePlainText, type GuidePage } from "./guide";
import { GAMES } from "./games";
import { loadGame } from "./guide";

export interface SearchDoc {
  slug: string;
  game: string;
  title: string;
  disc: string;
  text: string;
  headings: { level: 2 | 3 | 4; text: string; idx: number }[];
}

function buildIndexFor(gameSlug: string): SearchDoc[] {
  try {
    const { pages } = loadGame(gameSlug);
    return pages.map((p: GuidePage) => ({
      slug: p.slug,
      game: gameSlug,
      title: p.title,
      disc: p.disc,
      text: pagePlainText(p),
      headings: p.content.blocks
        .map((b, idx) => {
          if (b.type === "h2") return { level: 2 as const, text: b.text, idx };
          if (b.type === "h3") return { level: 3 as const, text: b.text, idx };
          if (b.type === "h4") return { level: 4 as const, text: b.text, idx };
          return null;
        })
        .filter((x): x is { level: 2 | 3 | 4; text: string; idx: number } => x !== null),
    }));
  } catch {
    return [];
  }
}

export const SEARCH_INDEX: SearchDoc[] = GAMES.flatMap(g => buildIndexFor(g.slug));

export interface SearchHit {
  slug: string;
  game: string;
  title: string;
  disc: string;
  score: number;
  snippet: string;
  highlight: [number, number][];
}

export function search(query: string, max = 30): SearchHit[] {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];
  const tokens = q.split(/\s+/).filter(Boolean);
  const hits: SearchHit[] = [];
  for (const doc of SEARCH_INDEX) {
    const text = doc.text;
    let score = 0;
    const ranges: [number, number][] = [];
    for (const t of tokens) {
      if (!t) continue;
      const re = new RegExp(escapeRe(t), "gi");
      let m: RegExpExecArray | null;
      while ((m = re.exec(text)) !== null) {
        score += m[0].length;
        ranges.push([m.index, m.index + m[0].length]);
        if (ranges.length > 12) break;
      }
      if (ranges.length > 12) break;
    }
    if (score === 0) continue;
    if (doc.title.toLowerCase().includes(q)) score += 50;
    if (doc.headings.some((h) => h.text.toLowerCase().includes(q))) score += 20;

    const snippet = buildSnippet(text, ranges, 140);
    const hl = mergeRanges(ranges);
    hits.push({ slug: doc.slug, game: doc.game, title: doc.title, disc: doc.disc, score, snippet, highlight: hl });
  }
  hits.sort((a, b) => b.score - a.score);
  return hits.slice(0, max);
}

function escapeRe(s: string) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

function mergeRanges(rs: [number, number][]): [number, number][] {
  if (!rs.length) return [];
  const s = [...rs].sort((a, b) => a[0] - b[0]);
  const out: [number, number][] = [s[0]];
  for (let i = 1; i < s.length; i++) {
    const last = out[out.length - 1];
    if (s[i][0] <= last[1] + 1) last[1] = Math.max(last[1], s[i][1]);
    else out.push(s[i]);
  }
  return out;
}

function buildSnippet(text: string, ranges: [number, number][], len: number): string {
  if (!ranges.length) return text.slice(0, len);
  const [start] = ranges[0];
  const a = Math.max(0, start - Math.floor(len / 3));
  const b = Math.min(text.length, a + len);
  let s = text.slice(a, b);
  if (a > 0) s = "…" + s;
  if (b < text.length) s = s + "…";
  return s;
}
