// Screenshots de la versión multi-juego
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const OUT = "/tmp/ff9-mg";
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
  await ctx.addInitScript(() => {
    localStorage.setItem("ff9-theme", "dark");
  });
  const page = await ctx.newPage();

  // Games index (home nueva)
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(2000);
  await shoot(page, "01-games-index");

  // FF9 home (con sidebar)
  await page.goto(`${URL}/ff9/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "02-ff9-home");

  // FF9 página
  await page.goto(`${URL}/ff9/guia/ff9-p11/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "03-ff9-page");

  // Buscar con resultados cross-game
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(500);
  await page.fill("#search-input", "crystal");
  await page.waitForTimeout(500);
  await shoot(page, "04-search", false);

  // 404
  await page.goto(`${URL}/ff9/guia/does-not-exist/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "05-404");

  await browser.close();
  console.log(`\nListo → ${OUT}/`);
}

main().catch((e) => { console.error(e); process.exit(1); });
