let currentCount = 1;

function downloadBatch() {
    const batchSize = parseInt(document.getElementById('batchSize').value);

    function clickButtonSequentially(index) {
        if (index > batchSize) {
            // document.getElementById('loadBtn').click(); // Click 'Load Documents' after last download button
            return;
        }

        const buttonId = `downloadBtn-${index}`;
        const button = document.getElementById(buttonId);
        if (button) {
            button.click(); // Click the download button if it exists
            setTimeout(() => clickButtonSequentially(index + 1), 4000); // Wait 1 second before the next click
        } else {
            console.log(`Button with ID ${buttonId} does not exist.`);
            setTimeout(() => clickButtonSequentially(index + 1), 4000); // Continue sequence even if button doesn't exist
        }
    }

    clickButtonSequentially(1); // Start clicking from the first button
}

function handleDocumentAction(button, docLink) {
    const pdfExtensions = ['pdf'];
    const htmlExtensions = ['html', 'htm'];
    const fileExtension = docLink.split('.').pop().toLowerCase();  // Get the extension and convert it to lowercase

    button.style.backgroundColor = '#FFCC00'; // Indicate processing
    button.disabled = true; // Disable the button to prevent multiple submissions

    if (pdfExtensions.includes(fileExtension)) {
        window.location.href = docLink; // This will cause the browser to navigate or download the PDF
        console.log("Downloading a PDF document.");
        button.innerText = "Processing PDF";
    } else if (htmlExtensions.includes(fileExtension)) {
        console.log("Setting html files as classify 2.");
        button.innerText = "HTML file-- a non presentation";
        const data = { docLink: docLink };
        const apiEndpoint = 'http://localhost:5000/handle-html';

        fetch(apiEndpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            button.disabled = false; // Re-enable the button once processing is complete
        })
        .catch((error) => {
            console.error('Error:', error);
            button.innerText = "Error in processing";
            button.disabled = false;
        });
    } else {
        console.log("Could be anything");
        button.innerText = "Checking document...";

        const data = { docLink: docLink };
        const apiEndpoint = 'http://localhost:5000/might-be-pdf';

        fetch(apiEndpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            button.innerText = "We are unsure";
            var newWindow = window.open(docLink, '_blank', 'noopener,noreferrer');
            if (newWindow) {
                newWindow.blur();
                window.focus();
            }
            button.disabled = false;
        })
        .catch((error) => {
            console.error('Error:', error);
            button.innerText = "Error in processing";
            button.disabled = false;
        });
    }
}

function loadDocuments() {
    const batch_size = parseInt(document.getElementById('batchSize').value);
    const apiEndpoint = 'http://localhost:5000/start-batch';
    currentCount = 1;

    fetch(apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',  // Set Content-Type to application/json
        },
        body: JSON.stringify({ batch_size: batch_size })  // Convert the JavaScript object to a JSON string
    })
    .then(response => {
        if (response.ok) {
            return response.json();  // Parse JSON from the response
        } else {
            throw new Error('Failed to load documents');
        }
    })
    .then(documents => {
        console.log("Clearing fileList");
        const fileList = $('#fileList');
        fileList.empty();  // Clear existing entries
        console.log("Adding new documents to an empty fileList", fileList);

        documents.forEach((doc, index) => {
            const docLink = doc.pdf_link || '#';
            fileList.append(`<tr>
                <td><a href="${docLink}" target="_blank">${docLink}</a></td>
                <td><button id="downloadBtn-${index + 1}" class="btn btn-sm btn-secondary" onclick="handleDocumentAction(this, '${docLink}')">Download</button></td>
            </tr>`);
        });

    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
}

$(document).ready(function() {
    // loadDocuments();  // Keep it under control of user to click and set the batch_size
});
    


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

            console.log('All documents and links have been cleared.');
        }
    })
    .catch(error => {
        console.error('Error initiating clear processing:', error);
    });
}


function processNext() {
    const batchSize = parseInt(document.getElementById('batchSize').value, 10);  // Ensure the batchSize is updated from the input field

    if (currentCount <= batchSize) {
        const buttonId = `downloadBtn-${currentCount}`;  // Construct the ID of the button to be clicked
        const button = document.getElementById(buttonId);  // Get the button element by its ID

        if (button) {
            button.click();  // Trigger a click event on the button
            document.getElementById('currentCount').innerText = currentCount;  // Update the displayed count
            currentCount++;  // Increment the count to the next document
        } else {
            console.log('Button with id ' + buttonId + ' does not exist.');  // Handle the absence of the button
        }
    } else {
        console.log("All items in the batch have been processed. Loading new batch...");
        loadDocuments();  // Load new documents when the batch is exhausted
        currentCount = 1;  // Reset count after reaching batch size
        document.getElementById('currentCount').innerText = currentCount;  // Update the display to reflect the reset
    }
}

// function downloadNext(count) {
//     // Log the item number that is being handled
//     console.log('Downloading item number: ' + count);

//     // Construct the ID of the button based on the count
//     var buttonId = 'downloadBtn-' + count;

//     // Get the button element by its ID
//     var button = document.getElementById(buttonId);

//     // Check if the button exists
//     if (button) {
//         // Trigger a click event on the button
//         button.click();
//     } else {
//         // Log an error or handle the absence of the button
//         console.log('Button with id ' + buttonId + ' does not exist.');
//     }
// }
