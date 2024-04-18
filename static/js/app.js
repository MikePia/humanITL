let currentIndex = 0;


function downloadBatch() {
    console.log("downloadBatch called");
    const batchSize = parseInt(document.getElementById('batchSize').value);
    const rows = document.querySelectorAll('#fileList tr');
    for (let i = currentIndex; i < Math.min(currentIndex + batchSize, rows.length); i++) {
        // $(rows[i]).find('button').click();
        rows[i].querySelector('button').click();

    }
    currentIndex += batchSize; // Update the current index
    if (currentIndex >= rows.length) { // Reset if all files are processed
        currentIndex = 0;
        alert('All batches have been initiated for download.');
    }
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
                // Using the index to number the documents for better user tracking
                const linkText = doc.pdf_link; 

                // Append a new row with the document link displayed as a clickable hyperlink
                fileList.append(`<tr>
                    <td><a href="${docLink}" target="_blank">${linkText}</a></td>
                    <td><button class="btn btn-sm btn-secondary" onclick="window.open('${docLink}', '_blank')">Download</button></td>
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