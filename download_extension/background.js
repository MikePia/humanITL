
// Listen for download events
chrome.downloads.onCreated.addListener(downloadItem => {
    console.log('Download started:', downloadItem.url);

    if (downloadItem.filename.endsWith('.pdf')) {
        console.log('PDF download initiated:', downloadItem.filename);
    }

});


chrome.downloads.onChanged.addListener(changeInfo => {
    if (changeInfo.state && changeInfo.state.current === 'complete') {
        console.log('Download state changed to complete for ID:', changeInfo.id);

        // Retrieve the download item details using the ID
        chrome.downloads.search({ id: changeInfo.id }, function (results) {
            if (results && results.length > 0) {
                const downloadItem = results[0];
                console.log('Download completed:', downloadItem.url, downloadItem.filename);
                // Prepare the data to be sent
                const data = {
                    url: downloadItem.url,
                    filename: downloadItem.filename
                };

                // Define the URL of your Flask API endpoint
                const apiEndpoint = 'http://localhost:5000/process-row';

                // Use fetch API to make a POST request
                fetch(apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Success:', data);
                    })
                    .catch((error) => {
                        console.error('Error:', error);
                    });

            }
        });
    }
});



chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "openTabInBackground") {
        chrome.tabs.create({ url: request.url, active: false });
        sendResponse({status: "success"});
    }
});
