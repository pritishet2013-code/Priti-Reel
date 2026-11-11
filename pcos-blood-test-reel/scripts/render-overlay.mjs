// Renders composition/index.html to a transparent PNG sequence (30 fps).
// Usage: node render-overlay.mjs <outDir> [--times 1.2,3.4]   (times = stills only)
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); } catch { playwright = require('/opt/node22/lib/node_modules/playwright'); }

const here = path.dirname(fileURLToPath(import.meta.url));
const page_url = pathToFileURL(path.join(here, '..', 'composition', 'index.html')).href;
const outDir = path.resolve(process.argv[2] || 'frames');
const tIdx = process.argv.indexOf('--times');
const FPS = 30;
fs.mkdirSync(outDir, { recursive: true });

const browser = await playwright.chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(page_url);
await page.evaluate(() => window.__ready);
if (errors.length) { console.error('Composition errors:\n' + errors.join('\n')); process.exit(1); }

const duration = await page.evaluate(() => window.__DURATION);
const sfx = await page.evaluate(() => window.__SFX);
fs.writeFileSync(path.join(outDir, 'sfx.json'), JSON.stringify(sfx));

const times = tIdx > 0
  ? process.argv[tIdx + 1].split(',').map(Number)
  : Array.from({ length: Math.round(duration * FPS) }, (_, i) => i / FPS);

for (let i = 0; i < times.length; i++) {
  await page.evaluate(t => window.__seek(t), times[i]);
  const name = tIdx > 0 ? `still_${times[i].toFixed(2)}.png` : `f_${String(i).padStart(5, '0')}.png`;
  await page.screenshot({ path: path.join(outDir, name), omitBackground: true });
  if (i % 60 === 0) process.stdout.write(`\r${i}/${times.length}`);
}
console.log(`\nRendered ${times.length} frame(s) to ${outDir}`);
await browser.close();
