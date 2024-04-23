let currentIndex = 0;

function downloadBatch() {
    // Define the Flask API endpoint
    const apiEndpoint = 'http://localhost:5000/click-downloads';
    const batch_size = parseInt(document.getElementById('batchSize').value);

    // Use fetch API to make a POST request
    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ batch_size: batch_size })
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

function handleDocumentAction(button, docLink) {
    // Directly initiate an action or download without checking the content type
    window.location.href = docLink;

    // Change the button color when clicked to indicate an attempt was made to handle the file
    button.style.backgroundColor = '#FFCC00'; // Ruddy yellow color
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
                fileList.append(`<tr>
                    <td><a href="${docLink}" target="_blank">${docLink}</a></td>
                    <td><button id="downloadBtn-${index + 1}" class="btn btn-sm btn-secondary" onclick="handleDocumentAction(this, '${docLink}')">Download</button></td>
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


let currentCount = 1;
const batchSize = parseInt(document.getElementById('batchSize').value, 10);

function processNext() {
    if (currentCount <= batchSize) {
        downloadNext(currentCount);
        document.getElementById('currentCount').innerText = currentCount;
        currentCount++;
    } else {
        alert("All items in the batch have been processed. Loading new batch...");
        loadDocuments();  // Load new documents when the batch is exhausted
        currentCount = 1;  // Reset count after reaching batch size
        document.getElementById('currentCount').innerText = currentCount;  // Update the display to reflect the reset
    }
}

function downloadNext(count) {
    // Log the item number that is being handled
    console.log('Downloading item number: ' + count);

    // Construct the ID of the button based on the count
    var buttonId = 'downloadBtn-' + count;

    // Get the button element by its ID
    var button = document.getElementById(buttonId);

    // Check if the button exists
    if (button) {
        // Trigger a click event on the button
        button.click();
    } else {
        // Log an error or handle the absence of the button
        console.log('Button with id ' + buttonId + ' does not exist.');
    }
}
