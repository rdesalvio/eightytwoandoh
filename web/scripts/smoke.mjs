import fs from 'fs';
import os from 'os';
import puppeteer from 'puppeteer-core';
import lz from 'lz-string';

const BASE = 'http://localhost:5179';
const OUT = '/tmp/e82o';
fs.mkdirSync(OUT, { recursive: true });

const candidates = ['/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/chromium'];
const execPath = candidates.find((p) => fs.existsSync(p));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({
	executablePath: execPath,
	headless: 'new',
	args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
	userDataDir: fs.mkdtempSync(os.tmpdir() + '/cr-')
});
const page = await browser.newPage();
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
const errors = [];
page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message));
page.on('console', (m) => m.type() === 'error' && errors.push('CONSOLE: ' + m.text()));

async function shot(name) {
	await page.screenshot({ path: `${OUT}/${name}.png` });
	console.log('shot', name);
}

// 1. home
await page.goto(BASE + '/', { waitUntil: 'networkidle0' });
await shot('1-home');

// switch to Hockey-IQ + Original Six to exercise theme/info
await page.$$eval('.seg button', (b) => b[1].click()); // Hockey-IQ
await page.$$eval('.tchip', (b) => b[1].click()); // Original Six
await shot('2-home-config');

// 2. start draft
await page.click('.btn.primary.big');
await page.waitForFunction(() => location.pathname === '/play');
// 6 picks
for (let i = 0; i < 6; i++) {
	await page.waitForSelector('.pick', { timeout: 5000 });
	if (i === 2) await shot('3-draft-pick');
	await page.$$eval('.pick', (b) => b[0].click());
	await sleep(800); // spin + render next round
}
await page.waitForSelector('.resultcard', { timeout: 5000 });
await sleep(400);
await shot('4-result');

// verify "Draft again" actually restarts a draft (was a no-op bug)
await page.evaluate(() => {
	const b = [...document.querySelectorAll('button.btn')].find((x) => /Draft again/i.test(x.textContent));
	b && b.click();
});
await page.waitForSelector('.pick', { timeout: 8000 });
console.log('draft-again: new draft started ✓');

// 3. how-to-play
await page.goto(BASE + '/how-to-play', { waitUntil: 'networkidle0' });
await shot('5-howto');

// 4. shared link round-trip — build a code from the dataset and open /r/<code>
const ds = JSON.parse(fs.readFileSync('./src/lib/data/players.json'));
const pick = (g, n) => ds.pool.filter((p) => p.grp === g).sort((a, b) => b.overall - a.overall)[n];
const roster = [pick('F', 0), pick('F', 1), pick('F', 2), pick('D', 0), pick('D', 1), pick('G', 0)];
const code = lz.compressToEncodedURIComponent(
	JSON.stringify({ m: 0, r: roster.map((p) => [p.id, p.team, p.decade]) })
);
await page.goto(`${BASE}/r/${code}`, { waitUntil: 'networkidle0' });
await page.waitForSelector('.resultcard', { timeout: 5000 });
await shot('6-shared');
const sharedRecord = await page.$eval('.record', (e) => e.textContent);
console.log('shared decoded record:', sharedRecord);

console.log(errors.length ? '\nERRORS:\n' + errors.join('\n') : '\nNo page errors ✓');
await browser.close();
