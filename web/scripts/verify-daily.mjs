// Verify the daily across many "days" (seeds, incl. themed ones): every run
// completes (no dead-ends) and everyone sees the SAME draws regardless of picks.
import fs from 'fs';
import os from 'os';
import puppeteer from 'puppeteer-core';

const BASE = process.argv[2] || 'http://localhost:5179';
const SEEDS = ['', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'];
const execPath = ['/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/chromium'].find((p) =>
	fs.existsSync(p)
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({
	executablePath: execPath,
	headless: 'new',
	args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
	userDataDir: fs.mkdtempSync(os.tmpdir() + '/cr-')
});

async function playOnce(seed) {
	const ctx = await browser.createBrowserContext();
	const page = await ctx.newPage();
	await page.setViewport({ width: 390, height: 844 });
	const errs = [];
	page.on('pageerror', (e) => errs.push(e.message));
	const url = BASE + '/play?daily=1' + (seed ? '&seed=' + seed : '');
	await page.goto(url, { waitUntil: 'networkidle0' });
	const seq = [];
	let theme = '';
	for (let i = 0; i < 6; i++) {
		try {
			await page.waitForSelector('.pick', { timeout: 6000 });
		} catch {
			await ctx.close();
			return { ok: false, why: 'stuck', seq, theme };
		}
		if (!theme) theme = await page.$eval('.eyebrow', (e) => e.textContent.trim()).catch(() => '');
		const td = await page.evaluate(
			() => `${document.querySelector('.lower3 .decade')?.textContent?.trim()} ${document.querySelector('.lower3 .team')?.textContent?.trim()}`
		);
		seq.push(td);
		const n = await page.$$eval('.pick', (els) => els.length);
		await page.$$eval('.pick', (els, idx) => els[idx].click(), Math.floor(Math.random() * n));
		await sleep(650);
	}
	const done = await page
		.waitForSelector('.resultcard', { timeout: 4000 })
		.then(() => true)
		.catch(() => false);
	await ctx.close();
	return { ok: done && !errs.length, why: errs[0], seq: seq.join(' | '), theme };
}

let pass = true;
for (const seed of SEEDS) {
	const a = await playOnce(seed);
	const b = await playOnce(seed); // different random picks, same seed
	const same = a.seq === b.seq;
	const ok = a.ok && b.ok && same;
	pass &&= ok;
	console.log(`seed "${seed || 'today'}" [${a.theme}] ${ok ? 'OK' : 'FAIL ' + (a.why || b.why || (!same && 'draws differ'))}`);
}
console.log('\n' + (pass ? 'ALL SEEDS PASS ✓ (complete + deterministic)' : 'FAIL ✗'));
await browser.close();
