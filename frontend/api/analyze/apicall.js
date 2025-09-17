// This script demonstrates how a frontend application can interact with your API.

// This is the URL of your running Flask API.
// If your Flask app is running locally, this will be the address.
const API_URL = 'http://127.0.0.1:5000/api/analyze';

// Function to call the API with user-provided coordinates and radius.
async function analyzeLocation(latitude, longitude, radius) {
    try {
        // Prepare the data to be sent to the API.
        // The API expects a JSON object with 'latitude', 'longitude', and 'radius_km'.
        const payload = {
            latitude: parseFloat(latitude),
            longitude: parseFloat(longitude),
            radius_km: parseFloat(radius)
        };

        // Make the POST request to your API endpoint.
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // Check if the request was successful.
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Parse the JSON response from the API.
        const analysisData = await response.json();
        
        // Log the received data to the console for inspection.
        console.log('API Response:', analysisData);
        
        // You would then update your website's UI with this data.
        // For example: display the total score, recommendations, etc.
        displayResults(analysisData);

    } catch (error) {
        // Log any errors that occur during the fetch operation.
        console.error('There was a problem with the fetch operation:', error);
    }
}

// Example function to display the results in the UI.
function displayResults(data) {
    // This is a placeholder for your UI logic.
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <h2>Analysis Results</h2>
            <p>Overall Suitability: ${data.fra_analysis.overall_suitability}</p>
            <p>Total Score: ${data.fra_analysis.total_score}</p>
            <h3>Recommendations</h3>
            <ul>
                ${data.recommendations.immediate_actions.map(action => `<li>${action}</li>`).join('')}
            </ul>
        `;
    }
}

// Example of how to call the function when a button is clicked.
document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyze-button');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', () => {
            // Get values from your input fields (e.g., using document.getElementById)
            const lat = '23.3441';  // Replace with actual input value
            const lng = '85.3096';  // Replace with actual input value
            const rad = '2.0';     // Replace with actual input value

            // Call the analysis function
            analyzeLocation(lat, lng, rad);
        });
    }
});
