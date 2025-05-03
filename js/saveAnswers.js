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
function saveAnswersToJson(peopleCount, submittedData) {
    const answers = collectAllAnswers(peopleCount, submittedData);
    
    // Convert the answers object to a JSON string
    const jsonData = JSON.stringify(answers, null, 2);
    
    // Create a blob from the JSON string
    const blob = new Blob([jsonData], { type: 'application/json' });
    
    // Create a download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skyscanner_reunion_answers_${new Date().toISOString().slice(0, 10)}.json`;
    
    // Trigger the download
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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