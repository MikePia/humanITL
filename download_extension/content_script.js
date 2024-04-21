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
