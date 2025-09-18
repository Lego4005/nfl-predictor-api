import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

console.log('🔍 Testing Dashboard Access...\n');

// Test 1: Main page
await page.goto('http://localhost:5173');
await page.waitForTimeout(2000);
await page.screenshot({ path: 'test-main.png' });

// Get current mode
const modeButtons = await page.$$eval('button', buttons =>
  buttons.map(b => b.textContent).filter(t => t)
);
console.log('📱 Available buttons on main page:', modeButtons);

// Test 2: Try admin URL
console.log('\n🧠 Testing Admin URL...');
await page.goto('http://localhost:5173/?admin=true');
await page.waitForTimeout(2000);
await page.screenshot({ path: 'test-admin.png' });

// Check what's rendered
const title = await page.textContent('h1');
console.log('Title shown:', title);

// Look for Expert Observatory
const hasExpertObservatory = await page.$$eval('*', elements =>
  elements.some(el => el.textContent?.includes('Expert Observatory'))
);
console.log('Has Expert Observatory:', hasExpertObservatory);

// Check for admin button
const hasAdminButton = await page.$$eval('button', buttons =>
  buttons.some(b => b.textContent?.includes('🧠') || b.textContent?.includes('Expert') || b.textContent?.includes('Admin'))
);
console.log('Has Admin Button:', hasAdminButton);

// Test 3: Click Live if available
const liveButton = await page.$('button:has-text("Live")');
if (liveButton) {
  console.log('\n📊 Clicking Live button...');
  await liveButton.click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'test-live.png' });

  const liveButtons = await page.$$eval('button', buttons =>
    buttons.map(b => b.textContent).filter(t => t && (t.includes('🧠') || t.includes('Expert')))
  );
  console.log('Expert buttons on Live dashboard:', liveButtons);
}

// Test 4: Check API
console.log('\n🔌 Testing Expert API...');
const apiResponse = await page.evaluate(async () => {
  try {
    const res = await fetch('http://localhost:8003/api/experts');
    const data = await res.json();
    return { success: true, count: data.length };
  } catch (err) {
    return { success: false, error: err.message };
  }
});
console.log('API Response:', apiResponse);

// Final check - get all text content
const allText = await page.evaluate(() => document.body.innerText);
if (allText.includes('Expert Observatory')) {
  console.log('\n✅ Expert Observatory FOUND in page!');
} else {
  console.log('\n❌ Expert Observatory NOT found');
  console.log('Page contains:', allText.substring(0, 200) + '...');
}

await browser.close();
console.log('\n📸 Screenshots saved: test-main.png, test-admin.png, test-live.png');