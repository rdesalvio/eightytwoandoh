// Confirm: useless skips hide per theme, and Salary Cap free-play works/completes.
import fs from 'fs';
import os from 'os';
import puppeteer from 'puppeteer-core';
const BASE = process.argv[2] || 'http://localhost:5179';
const execPath = ['/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/chromium'].find((p) => fs.existsSync(p));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await puppeteer.launch({
	executablePath: execPath, headless: 'new',
	args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
	userDataDir: fs.mkdtempSync(os.tmpdir() + '/cr-')
});
const page = await browser.newPage();
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });

const cases = [
	['decade', '/play?info=classic&theme=decade&value=1980s', 'expect: New era HIDDEN'],
	['franchise', '/play?info=classic&theme=franchise&value=MTL', 'expect: New franchise HIDDEN'],
	['salary-cap', '/play?info=classic&theme=salary-cap', 'expect: both skips shown, completes']
];
for (const [name, url, note] of cases) {
	await page.goto(BASE + url, { waitUntil: 'networkidle0' });
	await page.waitForSelector('.pick', { timeout: 6000 });
	const skips = await page.$$eval('.skips .btn', (b) => b.map((x) => x.textContent.trim().replace(/\s+/g, ' ')));
	await page.screenshot({ path: `/tmp/e82o/theme-${name}.png` });
	// for salary-cap, play through to confirm it completes
	let done = '';
	if (name === 'salary-cap') {
		for (let i = 0; i < 6; i++) { await page.waitForSelector('.pick', { timeout: 6000 }); await page.$$eval('.pick', (b) => b[0].click()); await sleep(700); }
		done = (await page.waitForSelector('.resultcard', { timeout: 5000 }).then(() => 'completed').catch(() => 'STUCK'));
	}
	console.log(`${name.padEnd(11)} skips=[${skips.join(' | ')}] ${done} — ${note}`);
}
await browser.close();
