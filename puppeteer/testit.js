const puppeteer = require('puppeteer');

async function testWaitForTimeout() {
    // Display the version of Puppeteer
    console.log(`Puppeteer version: ${require('puppeteer/package.json').version}`);
    // Display the version of Node.js
    console.log(`Node.js version: ${process.version}`);

    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    try {
        await page.goto('https://example.com', { waitUntil: 'networkidle2' });
        console.log('Page loaded successfully.');

        // Wait for 5000 milliseconds
        console.log('Waiting for 5 seconds...');
        await page.waitForTimeout(5000);
        console.log('Wait complete.');

    } catch (error) {
        console.error('Error occurred:', error);
    } finally {
        await browser.close();
        console.log('Browser closed.');
    }
}

testWaitForTimeout();
