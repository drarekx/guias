// Registry de juegos: fuente de verdad = data/games.json
import gamesData from "../../data/games.json";
import { isGameAvailable as isGameAvailableImpl } from "./guide";

export interface GameTheme {
  primary: { name: string; hex: string; ink: string };
  accent:  { name: string; hex: string; ink: string };
  rose: string; azure: string; emerald: string;
  ember: string; crimson: string; void: string; bg: string;
}

export interface GameSection {
  disc: string;
  items: { slug: string; title: string; href: string }[];
}

export interface Game {
  slug: string;
  title: string;
  shortTitle: string;
  year: number;
  developer: string;
  platforms: string[];
  tagline: string;
  baseUrl: string;
  indexHref: string;
  filePrefix: string;
  theme: GameTheme;
  sections: GameSection[];
}

const games = (gamesData as { games: (Game & { order?: number })[] }).games;
// Orden por `order` (cronología del número romano), luego por nombre.
const sortedGames = [...games].sort((a, b) => {
  const oa = a.order ?? 999;
  const ob = b.order ?? 999;
  return oa - ob || a.slug.localeCompare(b.slug);
});
export const GAMES: Game[] = sortedGames;
export const BY_SLUG: Record<string, Game> = Object.fromEntries(sortedGames.map(g => [g.slug, g]));

export function getGame(slug: string): Game | undefined {
  return BY_SLUG[slug];
}

export function totalPages(g: Game): number {
  return g.sections.reduce((acc, s) => acc + s.items.length, 0);
}

// Re-exportar para que la UI no tenga que importar de guide.ts solo para esto
export function isGameAvailable(slug: string): boolean {
  return isGameAvailableImpl(slug);
}

// Convierte una paleta a CSS custom properties para usar en :root o [data-game="..."]
export function themeVars(theme: GameTheme, mode: "dark" | "light" = "dark"): Record<string, string> {
  // Por ahora solo soportamos dark mode real (FF9 tenía light parchment);
  // cada juego podría tener su propia variante light más adelante.
  return {
    "--color-crystal":       theme.primary.hex,
    "--color-crystal-2":     lighten(theme.primary.hex, 0.15),
    "--color-crystal-ink":   theme.primary.ink,
    "--color-gold":          theme.accent.hex,
    "--color-gold-2":        lighten(theme.accent.hex, 0.15),
    "--color-gold-ink":      theme.accent.ink,
    "--color-rose":          theme.rose,
    "--color-azure":         theme.azure,
    "--color-emerald":       theme.emerald,
    "--color-ember":         theme.ember,
    "--color-crimson":       theme.crimson,
    "--color-void":          theme.void,
    "--color-bg":            theme.bg,
  };
}

function lighten(hex: string, amount: number): string {
  const m = hex.match(/^#([0-9a-f]{6})$/i);
  if (!m) return hex;
  const n = parseInt(m[1], 16);
  let r = (n >> 16) & 0xff, g = (n >> 8) & 0xff, b = n & 0xff;
  r = Math.round(r + (255 - r) * amount);
  g = Math.round(g + (255 - g) * amount);
  b = Math.round(b + (255 - b) * amount);
  return "#" + [r, g, b].map(v => v.toString(16).padStart(2, "0")).join("");
}
