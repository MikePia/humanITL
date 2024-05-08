let downloadCount = 0;
const DOWNLOAD_THRESHOLD = 10; // Trigger after every 10 downloads

// #######################################################
// #################### Heartbeat ########################
// #######################################################
function checkFlaskAppStatus() {
    return fetch('http://localhost:5000/heartbeat')
        .then(response => response.ok)
        .catch(() => false);  // Just return false, no error logging or throwing
}

// #######################################################
// ###################### Downloads ######################
// #######################################################

chrome.downloads.onCreated.addListener(downloadItem => {
    console.log('Download started:', downloadItem.url);
    if (downloadItem.filename.endsWith('.pdf')) {
        console.log('PDF download initiated:', downloadItem.filename);
    }
});

chrome.downloads.onChanged.addListener(changeInfo => {
    if (changeInfo.state && changeInfo.state.current === 'complete') {
        console.log('Download state changed to complete for ID:', changeInfo.id);
        chrome.downloads.search({ id: changeInfo.id }, function (results) {
            if (results && results.length > 0) {
                const downloadItem = results[0];
                console.log('Download completed:', downloadItem.url, downloadItem.filename);
                postDownloadDetails(downloadItem);
            }
        });
        downloadCount++;
        if (downloadCount >= DOWNLOAD_THRESHOLD) {
            retryFailedAndCancelledDownloads();
            downloadCount = 0; // Reset the counter
        }

    }
});
function postDownloadDetails(downloadItem) {
    checkFlaskAppStatus()
        .then(isAppRunning => {
            if (isAppRunning) {
                console.log("Flask app is running.");
                const apiEndpoint = 'http://localhost:5000/process-row';
                return fetch(apiEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: downloadItem.url,
                        filename: downloadItem.filename
                    })
                });
            } else {
                console.log("Flask app is not running, skipping operations.");
                return Promise.reject(new Error("Flask app is not running"));  // Silently handle this error
            }
        })
        .then(response => {
            if (!response.ok) {
                // Throw an error with status text to understand what went wrong
                throw new Error(`HTTP error! status: ${response.status}, ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            if (data.success) {
                chrome.downloads.removeFile(downloadItem.id, () => {
                    console.log(`Removed download file with ID: ${downloadItem.id}`);
                });
            } else {
                console.log('No action taken:', data.message);
            }
        })
        .catch(error => {
            if (error.message !== "Flask app is not running") {
                console.error('Error:', error.message);
            }
        });
}

function retryFailedAndCancelledDownloads() {
    checkFlaskAppStatus()
        .then(isAppRunning => {
            if (isAppRunning) {
                console.log("Flask app is running, proceed with download retries.");
                chrome.downloads.search({state: "interrupted"}, function(downloads) {
                    if (downloads.length > 0) {
                        fetch('http://localhost:5000/download-decision', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({downloads: downloads})
                        })
                        .then(response => response.json())
                        .then(data => {
                            downloads.forEach(download => {
                                let action = data[download.id].action;
                                if (action === "download") {
                                    chrome.downloads.download({url: download.url}, newDownloadId => {
                                        console.log("Retried download with ID:", newDownloadId);
                                    });
                                } else if (action === "delete") {
                                    chrome.downloads.erase({id: download.id});
                                    console.log("Deleted download with ID:", download.id);
                                }
                            });
                        })
                        .catch(error => {
                            console.error('Error in processing download decisions:', error.message);
                        });
                    }
                });
            } else {
                console.log("Flask app is not running, skipping download retries.");
            }
        })
        .catch(error => {
            console.error('Error checking Flask app status:', error.message);
        });
}



// #######################################################
// ######################## Tabs #########################
// #######################################################

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'loading') {
        // Here we might short circuit loading the file and then remove the tab
        console.log(`Tab ${tabId} is loading.`);
    }
    if (changeInfo.status === 'complete' && tab.url) {

        console.log(`File opened in tab: ${tab.url}`);
        notifyAPI(tab.url);
    }
});

async function notifyAPI(url) {
    // Don't do anything if the URL is from our own Flask app
    if (url.startsWith('http://localhost:5000') || url.startsWith('http://127.0.0.1:5000')) {
        return; // Early exit if the URL is for the local Flask app
    }
    
    const isAppRunning = await checkFlaskAppStatus();
    if (!isAppRunning) {
        return; // Early return if the Flask app is not running, silently ignore
    }

    // If the app is running, proceed with the API call
    console.log("Flask app is running.");  // Log that the Flask app is available for operations
    const apiEndpoint = 'http://localhost:5000/tab-opened';
    try {
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        
        if (!response.ok) {
            return; // Handle HTTP errors silently
        }
        
        const data = await response.json();  // Process JSON response from server
        console.log('Success:', data.message);  // Log success message from server

    } catch (error) {
        return; // Handle any other errors silently
    }
}



// #######################################################
// ####################### Messaging #####################
// #######################################################

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case "openTabInBackground":
            chrome.tabs.create({ url: request.url, active: false });
            sendResponse({status: "success"});
            break;
        case "checkPageType":
            chrome.tabs.get(sender.tab.id, function(tab) {
                sendResponse({type: tab.url.startsWith('http://') || tab.url.startsWith('https://') ? 'processHTML' : 'ignore'});
            });
            return true; // indicates that the response is asynchronous
    }
});

chrome.webNavigation.onCompleted.addListener(function(details) {
    if (details.frameId === 0) {
        console.log('Main HTML page loaded:', details.url);
    }
});
