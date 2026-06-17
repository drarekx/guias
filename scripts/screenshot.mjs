// Quick visual check: captura home, página de guía, lightbox, búsqueda, modo claro
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const OUT = "/tmp/ff9-shots";
mkdirSync(OUT, { recursive: true });

const URL = "http://127.0.0.1:4321";

async function shoot(page, name, fullPage = true) {
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage });
  console.log(`✓ ${name}.png`);
}

async function main() {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    colorScheme: "dark",
    deviceScaleFactor: 1.5,
  });
  // Quitar toolbar de astro
  await ctx.addInitScript(() => {
    localStorage.setItem("astro:dev-toolbar", "false");
    const style = document.createElement("style");
    style.textContent = "astro-dev-toolbar, astro-dev-overlay { display: none !important; }";
    document.documentElement.appendChild(style);
  });
  const page = await ctx.newPage();

  // 1) Home dark
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await shoot(page, "01-home-dark");

  // 2) Página de guía
  await page.goto(`${URL}/guia/ff9-p11/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await shoot(page, "02-page-burmecia");

  // 3) Página con muchas imágenes
  await page.goto(`${URL}/guia/ff9-p2/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await shoot(page, "03-page-alexandria");

  // 4) Extras (cartas)
  await page.goto(`${URL}/guia/ff9-cartas/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(600);
  await shoot(page, "04-extras-cartas");

  // 5) Extras (invocaciones)
  await page.goto(`${URL}/guia/ff9-invocaciones/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(600);
  await shoot(page, "05-extras-invocaciones");

  // 6) Search modal
  await page.goto(`${URL}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(400);
  await page.fill("#search-input", "burmecia");
  await page.waitForTimeout(500);
  await shoot(page, "06-search-burmecia", false);

  // 7) Lightbox
  await page.goto(`${URL}/guia/ff9-p11/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  const firstImg = page.locator(".prose-guide img").first();
  await firstImg.scrollIntoViewIfNeeded();
  await firstImg.click();
  await page.waitForTimeout(500);
  await shoot(page, "07-lightbox", false);

  // 8) Modo claro - home
  await page.evaluate(() => localStorage.setItem("ff9-theme", "light"));
  await page.goto(`${URL}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await shoot(page, "08-home-light");

  // 9) Modo claro - página
  await page.goto(`${URL}/guia/ff9-p11/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await shoot(page, "09-page-light");

  // 10) Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => localStorage.setItem("ff9-theme", "dark"));
  await page.goto(`${URL}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await shoot(page, "10-mobile-home");

  await page.goto(`${URL}/guia/ff9-p11/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await shoot(page, "11-mobile-page");

  // 12) Mobile TOC drawer
  await page.click("#mobile-toc");
  await page.waitForTimeout(500);
  await shoot(page, "12-mobile-toc", false);

  await browser.close();
  console.log("\nListo → /tmp/ff9-shots/");
}

main().catch((e) => { console.error(e); process.exit(1); });
