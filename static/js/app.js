let currentIndex = 0;

function downloadBatch() {
    // Collect all the document IDs to download
    const ids = Array.from(document.querySelectorAll('.document-button')).map(button => button.dataset.id);

    // Define the Flask API endpoint
    const apiEndpoint = 'http://localhost:5000/click-downloads';

    // Use fetch API to make a POST request
    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: ids })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) 
            alert('Error downloading batch: ' + data.message);
        else
            console.log('Batch download initiated:', data);
    })
    .catch(error => {
        console.error('Error initiating batch download:', error);
    });
}

function handleDocumentAction(docLink) {
    // Just navigate to the URL, allowing the browser and extension to handle the specifics
    window.location.href = docLink;
}


// This function can be used if you choose to call it directly instead of using custom events
function openLinkInBackgroundTab(url) {
    chrome.runtime.sendMessage({
        action: "openTabInBackground",
        url: url
    }, function(response) {
        console.log(response.status);
    });
}


function loadDocuments() {
    const batch_size = parseInt(document.getElementById('batchSize').value);
    $.ajax({
        url: '/start-batch',
        method: 'POST',
        data: { batch_size: batch_size },
        success: function(documents) {

            const fileList = $('#fileList');
            fileList.empty();  // Clear existing entries
            documents.forEach((doc, index) => {
                const docLink = doc.pdf_link || '#';
                const linkText = doc.pdf_link;

                fileList.append(`<tr>
                    <td><a href="${docLink}" target="_blank">${linkText}</a></td>
                    <td><button id="downloadBtn-${index + 1}" class="btn btn-sm btn-secondary" onclick="handleDocumentAction('${docLink}')">Download</button></td>
                </tr>`);
            });

        },
        error: function() {
            alert('Failed to load documents');
        }
    });
}

$(document).ready(function() {
    loadDocuments();  // Load documents when the page loads
});
