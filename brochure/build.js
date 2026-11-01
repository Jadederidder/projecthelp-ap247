// Render brochure/index.html to a print-ready A4 PDF.
//
//   node brochure/build.js
//
// Writes brochure/auto-pedigree-247.pdf. The fonts are local (assets/fonts),
// so this produces the same bytes with or without a network connection — the
// point being that the brochure can be rebuilt by anyone, at any time,
// without a designer and without this conversation.

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const HERE = __dirname;
const SRC = 'file://' + path.join(HERE, 'index.html');
const OUT = path.join(HERE, 'auto-pedigree-247.pdf');

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();

  const problems = [];
  page.on('pageerror', (e) => problems.push('page error: ' + e.message));
  page.on('requestfailed', (r) => problems.push('failed to load: ' + r.url()));

  await page.goto(SRC, { waitUntil: 'networkidle' });
  // Webfonts decide the line breaks, so a PDF rendered before they land is a
  // different document. Wait for them rather than for a guess at a timeout.
  await page.evaluate(() => document.fonts.ready);

  await page.pdf({
    path: OUT,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
  });

  await browser.close();

  if (problems.length) {
    console.error('PROBLEMS:\n  ' + problems.join('\n  '));
    process.exitCode = 1;
  }
  const kb = (fs.statSync(OUT).size / 1024).toFixed(0);
  console.log(`wrote ${path.relative(process.cwd(), OUT)} (${kb} KB)`);
})();
