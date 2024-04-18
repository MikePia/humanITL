const puppeteer = require('puppeteer');

async function clickButton() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('http://localhost:5000'); // your URL here
    await page.click('#buttonID'); // your button's selector
    await browser.close();
}

clickButton();
