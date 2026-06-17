// Screenshots de los 5 juegos para verificar paletas
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const OUT = "/tmp/ff9-themes";
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

  // Games index
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(2000);
  await shoot(page, "00-games-index");

  // Cada juego: home + primera página
  const games = ["ff9", "ff7", "ff8", "ff10", "ff6"];
  for (const g of games) {
    await page.goto(`${URL}/${g}/`, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(1500);
    await shoot(page, `${g}-home`);

    await page.goto(`${URL}/${g}/guia/${g}-p1/`, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(1500);
    await shoot(page, `${g}-page`);
  }

  // Búsqueda cross-game
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(500);
  await page.fill("#search-input", "chocobo");
  await page.waitForTimeout(800);
  await shoot(page, "search-chocobo", false);

  await browser.close();
  console.log(`\nListo → ${OUT}/`);
}

main().catch((e) => { console.error(e); process.exit(1); });
