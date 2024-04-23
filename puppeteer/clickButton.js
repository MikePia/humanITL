const puppeteer = require('puppeteer');
const path = require('path');
require('dotenv').config();

console.log(process.env.DOWNLOAD_DIRECTORY)
download_directory = process.env.DOWNLOAD_DIRECTORY
extension_path = process.env.EXTENSION_PATH

// assert that bot exist
if (!download_directory || !extension_path) {
    console.error('Missing environment variables. Exiting puppeteer');
    process.exit(1);
}

async function clickButtonsByNumber(url, numButtons) {
    console.log("Just starting");

    const extensionPath = path.resolve(__dirname, '../download_extension');
    const browser = await puppeteer.launch({
        headless: false,  // Extensions only work in head-full mode.
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            `--plugins.always_open_pdf_externally=true`,            // Automatically download PDFs.
            `--disable-dev-shm-usage`,
            '--disable-features=IsolateOrigins, site-per-process',
            `--disable-extensions-except=${extension_path}`,
            `--load-extension=${extension_path}`,
            `--download.default_directory=${download_directory}`
        ]
    });


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

    // await browser.close();yyy
}

const url = process.argv[2];
const numButtons = parseInt(process.argv[3], 10);

clickButtonsByNumber(url, numButtons).catch(err => console.error('Error during button clicks:', err));
