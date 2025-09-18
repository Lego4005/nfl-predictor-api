import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:5173');
await page.waitForTimeout(2000);

// Find the Narrow Mode button
const narrowButton = await page.$('button:has-text("Narrow Mode")');
if (narrowButton) {
  const box = await narrowButton.boundingBox();
  console.log('Narrow Mode button position:', box);
} else {
  console.log('Narrow Mode button not found');
}

// Find all buttons and their positions
const buttons = await page.$$eval('button', buttons =>
  buttons.map(b => ({
    text: b.textContent?.trim().substring(0, 20),
    position: {
      top: b.getBoundingClientRect().top,
      right: window.innerWidth - b.getBoundingClientRect().right,
      left: b.getBoundingClientRect().left
    }
  })).filter(b => b.position.top < 100) // Only buttons near top
);

console.log('\nTop buttons:', buttons);

await browser.close();