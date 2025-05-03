// Function to check if all travelers have submitted their answers
function allTravelersSubmitted(peopleCount, submittedData) {
    for (let i = 1; i <= peopleCount; i++) {
        if (!submittedData[`person-${i}`]) {
            return false;
        }
    }
    return true;
}

// Function to collect all answers from the form
function collectAllAnswers(peopleCount, submittedData) {
    const allAnswers = {
        timestamp: new Date().toISOString(),
        travelers: []
    };

    for (let i = 1; i <= peopleCount; i++) {
        const travelerData = submittedData[`person-${i}`];
        if (travelerData) {
            allAnswers.travelers.push({
                travelerNumber: i,
                budgetRange: {
                    min: travelerData.minBudget,
                    max: travelerData.maxBudget
                },
                preferredVibes: travelerData.features,
                preferredDestination: travelerData.destination,
                startingPoint: travelerData.startingPoint
            });
        }
    }

    return allAnswers;
}

// Function to save answers to a JSON file
// Modified saveAnswersToJson function
function saveAnswersToJson(peopleCount, submittedData) {
    const answers = collectAllAnswers(peopleCount, submittedData);
    
    // Send data to Node.js server
    fetch('http://localhost:3000/save-json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(answers),
    })
    .then(response => response.text())
    .then(message => console.log(message))
    .catch(error => console.error('Error:', error));
}

// Function to show or hide the save button based on submission status
function updateSaveButtonVisibility(peopleCount, submittedData) {
    const saveButton = document.getElementById('save-answers');
    const allSubmitted = allTravelersSubmitted(peopleCount, submittedData);
    
    if (allSubmitted) {
        if (!saveButton) {
            // Create the save button if it doesn't exist
            const newSaveButton = document.createElement('button');
            newSaveButton.id = 'save-answers';
            newSaveButton.textContent = 'Save All Answers to JSON';
            newSaveButton.style.marginTop = '20px';
            newSaveButton.style.backgroundColor = '#9c27b0';
            newSaveButton.addEventListener('click', () => saveAnswersToJson(peopleCount, submittedData));
            
            // Add the button after the forms container
            const formsContainer = document.getElementById('forms-container');
            formsContainer.insertAdjacentElement('afterend', newSaveButton);
        }
    } else {
        // Remove the save button if not all travelers have submitted
        if (saveButton) {
            saveButton.remove();
        }
    }
}

// Export functions to be used in the main script
window.saveAnswers = {
    updateSaveButtonVisibility: updateSaveButtonVisibility
};