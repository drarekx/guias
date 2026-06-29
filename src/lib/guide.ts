// Tipos + data loaders por juego
import type { GameSection } from "./games";

// Importa automáticamente todas las guías y estructuras descargadas.
// `eager: true` + `import: "default"` devuelve directamente el JSON parseado.
const guideModules = import.meta.glob<GuidePage[]>("../../data/games/*/guide.json", {
  eager: true,
  import: "default",
});
const structModules = import.meta.glob<GameSection[]>("../../data/games/*/structure.json", {
  eager: true,
  import: "default",
});

export type CellLink = { text: string; href?: string };
export type TableCell = string | CellLink;

export type Block =
  | { type: "h2"; text: string }
  | { type: "h3"; text: string }
  | { type: "h4"; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "img"; src: string; alt: string; caption: string }
  | { type: "table"; rows: TableCell[][] };

export interface PageContent {
  title: string;
  intro: string;
  image?: string;
  blocks: Block[];
}

export interface GuidePage {
  slug: string;
  disc: string;
  title: string;
  href: string;
  content: PageContent;
}

export interface PageMeta {
  slug: string;
  title: string;
  disc: string;
  index: number;
  prev?: { slug: string; title: string };
  next?: { slug: string; title: string };
}

interface GameData {
  pages: GuidePage[];
  bySlug: Map<string, GuidePage>;
  structure: GameSection[];
  meta: PageMeta[];
  byMetaSlug: Map<string, PageMeta>;
}

const CACHE = new Map<string, GameData>();

function slugFromPath(p: string, suffix: string): string {
  const m = p.match(new RegExp(`/games/([^/]+)/${suffix}$`));
  return m ? m[1] : "";
}

function ensureLoaded(gameSlug: string): GameData {
  if (CACHE.has(gameSlug)) return CACHE.get(gameSlug)!;

  let pages: GuidePage[] | undefined;
  let structure: GameSection[] | undefined;
  for (const [p, mod] of Object.entries(guideModules)) {
    if (slugFromPath(p, "guide.json") === gameSlug) { pages = mod; break; }
  }
  for (const [p, mod] of Object.entries(structModules)) {
    if (slugFromPath(p, "structure.json") === gameSlug) { structure = mod; break; }
  }
  if (!pages || !structure) {
    throw new Error(`Datos no encontrados para juego '${gameSlug}'`);
  }

  const bySlug = new Map(pages.map(p => [p.slug, p]));
  const meta: PageMeta[] = [];
  let idx = 0;
  for (const d of structure) {
    for (const it of d.items) {
      meta.push({ slug: it.slug, title: it.title, disc: d.disc, index: idx });
      idx++;
    }
  }
  for (let k = 0; k < meta.length; k++) {
    if (k > 0) meta[k].prev = { slug: meta[k - 1].slug, title: meta[k - 1].title };
    if (k < meta.length - 1) meta[k].next = { slug: meta[k + 1].slug, title: meta[k + 1].title };
  }
  const byMetaSlug = new Map(meta.map(m => [m.slug, m]));
  const data: GameData = { pages, bySlug, structure, meta, byMetaSlug };
  CACHE.set(gameSlug, data);
  return data;
}

export function loadGame(gameSlug: string) {
  return ensureLoaded(gameSlug);
}

export function getPage(gameSlug: string, slug: string): GuidePage | undefined {
  try { return ensureLoaded(gameSlug).bySlug.get(slug); }
  catch { return undefined; }
}

export function getMeta(gameSlug: string, slug: string): PageMeta | undefined {
  try { return ensureLoaded(gameSlug).byMetaSlug.get(slug); }
  catch { return undefined; }
}

export function getStructure(gameSlug: string): GameSection[] {
  return ensureLoaded(gameSlug).structure;
}

export function totalPagesFor(gameSlug: string): number {
  try { return ensureLoaded(gameSlug).pages.length; }
  catch { return 0; }
}

export function isGameAvailable(gameSlug: string): boolean {
  try { ensureLoaded(gameSlug); return true; }
  catch { return false; }
}

// Texto plano para búsqueda
export function pagePlainText(p: GuidePage): string {
  const parts: string[] = [p.title, p.disc, p.content.intro];
  for (const b of p.content.blocks) {
    if (b.type === "p" || b.type.startsWith("h")) parts.push(b.text);
    else if (b.type === "ul" || b.type === "ol") parts.push(b.items.join(" "));
    else if (b.type === "img") parts.push(b.alt, b.caption);
    else if (b.type === "table") {
      const cells = b.rows.flat().map((c) => typeof c === "string" ? c : c.text);
      parts.push(cells.join(" "));
    }
  }
  return parts.join("\n").toLowerCase();
}
