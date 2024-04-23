// content_script.js
document.addEventListener('OpenLinkInBackground', function(e) {
    openLinkInBackgroundTab(e.detail.url);
});


function openLinkInBackgroundTab(url) {
    chrome.runtime.sendMessage({
        action: "openTabInBackground",
        url: url
    }, function(response) {
        console.log(response.status);
    });
}



// content_script.js
chrome.runtime.sendMessage({action: "checkPageType"}, (response) => {
    if (response.type === 'processHTML') {
        console.log('Processing HTML content of this page...');
        // Here you can analyze the HTML, manipulate it or send details back to the background script
    }
});
