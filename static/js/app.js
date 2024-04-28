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
    const pdfExtensions = ['pdf'];
    const htmlExtensions = ['html', 'htm'];
    const fileExtension = docLink.split('.').pop().toLowerCase();  // Get the extension and convert it to lowercase

    // Change the button color when clicked to indicate an attempt was made to handle the file
    button.style.backgroundColor = '#FFCC00'; // Ruddy yellow color

    // Check and handle based on the file extension
    if (pdfExtensions.includes(fileExtension)) {
        // Handle PDF files
        window.location.href = docLink;
        console.log("Downloading a PDF document.");
        button.innerText = "Processing PDF";
    } else if (htmlExtensions.includes(fileExtension)) {
        // Handle HTML files
        console.log("Ignoring html file.");
        button.innerText = "ignoring  HTML file";
    } else {
        // File type is not supported
        console.log("Could be anything");
        button.innerText = "In new tab";
        var newWindow = window.open(docLink, '_blank', 'noopener,noreferrer');
        if (newWindow) {
            newWindow.blur();
            window.focus();
        }
    }
}


function loadDocuments() {
    const batch_size = parseInt(document.getElementById('batchSize').value);
    $.ajax({
        url: '/start-batch',
        method: 'POST',
        data: { batch_size: batch_size },
        success: function(documents) {
            console.log("Clearing fileList")
            const fileList = $('#fileList');
            fileList.empty();  // Clear existing entries
            console.log("Adding new documents to an empty fileList", fileList)

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
    // loadDocuments();  // Keep it under control of user to click and set the batch_size
});
    

let currentCount = 1;
const batchSize = parseInt(document.getElementById('batchSize').value, 10);

function clearAll() {
    // Define the Flask API endpoint
    const apiEndpoint = 'http://localhost:5000/clear-all';

    // Use fetch API to make a POST request
    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) {
            alert('Error clearing db: ' + data.message);
        } else {
            console.log('Clearing processing initiated:', data);

            // Clear document links and download buttons from the page
            const fileList = $('#fileList');
            fileList.empty();  // Clear existing entries

            alert('All documents and links have been cleared.');
        }
    })
    .catch(error => {
        console.error('Error initiating clear processing:', error);
    });
}



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
