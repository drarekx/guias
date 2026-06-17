// Screenshots de páginas nuevas para verificar escalado
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const OUT = "/tmp/ff9-shots-full";
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

  // Home (índice completo con 74 páginas)
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "01-home-full");

  // CD3 completa - una página larga
  await page.goto(`${URL}/guia/ff9-p34/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "02-templo-tierra");

  // CD4 - boss final
  await page.goto(`${URL}/guia/ff9-p39/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "03-lugar-recuerdos");

  // Extras: chocografías
  await page.goto(`${URL}/guia/ff9-chocografias/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1200);
  await shoot(page, "04-chocografias");

  // Extras: Hades
  await page.goto(`${URL}/guia/ff9-hades/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1200);
  await shoot(page, "05-hades");

  // Extras: curiosidades
  await page.goto(`${URL}/guia/ff9-curiosidades/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1200);
  await shoot(page, "06-curiosidades");

  // Búsqueda con un término raro
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(800);
  await page.keyboard.press("Control+k");
  await page.waitForTimeout(500);
  await page.fill("#search-input", "excalibur");
  await page.waitForTimeout(500);
  await shoot(page, "07-search-excalibur", false);

  await page.fill("#search-input", "hades");
  await page.waitForTimeout(500);
  await shoot(page, "08-search-hades", false);

  // Marcar varios como completados para ver progreso
  await page.evaluate(() => {
    const slugs = ["ff9-p1","ff9-p2","ff9-p5","ff9-p9","ff9-chocobos","ff9-invocaciones"];
    localStorage.setItem("ff9-progress", JSON.stringify(slugs));
  });
  await page.goto(URL, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "09-home-with-progress");

  // Página con marca activa
  await page.goto(`${URL}/guia/ff9-p11/`, { waitUntil: "load", timeout: 60000 });
  await page.waitForTimeout(1500);
  await shoot(page, "10-page-marked");

  await browser.close();
  console.log("\nListo → /tmp/ff9-shots-full/");
}

main().catch((e) => { console.error(e); process.exit(1); });
