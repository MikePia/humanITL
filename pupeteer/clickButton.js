const puppeteer = require('puppeteer');

async function clickButtonsByNumber(url, numButtons) {
    console.log("Just starting");
    const browser = await puppeteer.launch({ headless: false }); // Run in non-headless for testing
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text())); // Listen to page console logs

    console.log("before page.goto");
    await page.goto(url, { waitUntil: 'networkidle2' });
    console.log("after page.goto");

    await page.waitForSelector(`#downloadBtn-${numButtons}`, { visible: true }); // Ensure the last button is loaded

    for (let i = 1; i <= numButtons; i++) {
        const id = `downloadBtn-${i}`;
        const selector = `#${id}`;
        try {
            await page.click(selector);
            console.log(`Clicked on: ${selector}`);
            
        } catch (error) {
            console.error(`Failed to click on ${selector}:`, error.message);
        }
        await new Promise(resolve => setTimeout(resolve, 500)); // Delay for demonstration
    }

    await browser.close();
}

const url = process.argv[2];
const numButtons = parseInt(process.argv[3], 10);

clickButtonsByNumber(url, numButtons).catch(err => console.error('Error during button clicks:', err));
