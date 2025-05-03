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
        dateRange: {},
        travelers: []
    };
    
    const startDateInput = document.querySelector('.start-date');
    const endDateInput = document.querySelector('.end-date');
    if (startDateInput && endDateInput) {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        if (startDate && endDate) {
            allAnswers.dateRange = {
                startDate: startDate,
                endDate: endDate
            };
        } else {
            console.warn('Date range is incomplete. Skipping date range data.');
        }
    }

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
    
    // window.location.href = 'loading-screen.html?destination=output.html';
    
}


function isDateRangeLocked() {
    const startDateInput = document.querySelector('.start-date');
    const endDateInput = document.querySelector('.end-date');
    return startDateInput && endDateInput && 
           startDateInput.disabled && endDateInput.disabled;
}

// Function to show or hide the save button based on submission status
function updateSaveButtonVisibility(peopleCount, submittedData) {
    const saveButton = document.getElementById('save-answers');
    const dateLocked = isDateRangeLocked();
    const allSubmitted = allTravelersSubmitted(peopleCount, submittedData);
    // Only show the save button if all travelers have submitted and the date range is decided
    if (allSubmitted) {
        if (!saveButton) {
            // Create the save button if it doesn't exist
            const newSaveButton = document.createElement('button');
            newSaveButton.id = 'save-answers';
            newSaveButton.textContent = 'Find the perfect reunion!';
            newSaveButton.style.marginTop = '20px';
            newSaveButton.style.backgroundColor = '#9c27b0';
            newSaveButton.addEventListener('click', () => saveAnswersToJson(peopleCount, submittedData));
            
            // Add the button after the forms container
            const formsContainer = document.getElementById('forms-container');
            formsContainer.insertAdjacentElement('afterend', newSaveButton);
        }
    } else {
        // Remove the save button if not all conditions are met
        if (saveButton) {
            saveButton.remove();
        }
    }
}

// Function to lock the date range inputs and show an "Edit" button
// Update this function in saveAnswers.js
function lockDateRange() {
    const startDateInput = document.querySelector('.start-date');
    const endDateInput = document.querySelector('.end-date');
    const saveButton = document.querySelector('.save-date-range');

    if (startDateInput && endDateInput && saveButton) {
        startDateInput.disabled = true;
        endDateInput.disabled = true;
        saveButton.style.display = 'none';

        let editButton = document.querySelector('.edit-date-range');
        if (!editButton) {
            editButton = document.createElement('button');
            editButton.className = 'edit-date-range';
            editButton.textContent = 'Edit Date Range';
            editButton.style.marginLeft = '10px';
            saveButton.insertAdjacentElement('afterend', editButton);
            editButton.addEventListener('click', unlockDateRange);
        }
        
        // Trigger save button visibility check
        const peopleCount = parseInt(document.getElementById('people-count').value);
        updateSaveButtonVisibility(peopleCount, window.submittedData || {});
    }
}

// Function to unlock the date range inputs and show the "Save" button
function unlockDateRange() {
    const startDateInput = document.querySelector('.start-date');
    const endDateInput = document.querySelector('.end-date');
    const saveButton = document.querySelector('.save-date-range');
    const editButton = document.querySelector('.edit-date-range');

    if (startDateInput && endDateInput && saveButton && editButton) {
        startDateInput.disabled = false;
        endDateInput.disabled = false;
        saveButton.style.display = 'inline-block';
        editButton.remove();
        
        // Hide the JSON save button if it exists
        const jsonSaveButton = document.getElementById('save-answers');
        if (jsonSaveButton) {
            jsonSaveButton.remove();
        }
    }
}

// Modify the save date range functionality to lock the inputs after saving
document.addEventListener('DOMContentLoaded', () => {
    const saveButton = document.querySelector('.save-date-range');
    if (saveButton) {
        saveButton.addEventListener('click', () => {
            const startDateInput = document.querySelector('.start-date');
            const endDateInput = document.querySelector('.end-date');

            if (startDateInput && endDateInput) {
                const startDate = startDateInput.value;
                const endDate = endDateInput.value;

                if (!startDate || !endDate) {
                    alert('Please select both start and end dates.');
                    return;
                }

                if (new Date(startDate) > new Date(endDate)) {
                    alert('Start date cannot be after end date.');
                    return;
                }

                // Lock the date range inputs after saving
                lockDateRange();
                //alert('Date range saved successfully!');
            }
        });
    }
});

// Export functions to be used in the main script
window.saveAnswers = {
    updateSaveButtonVisibility: updateSaveButtonVisibility
    
};