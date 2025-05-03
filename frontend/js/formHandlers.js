document.addEventListener('DOMContentLoaded', function() {
    // Store all selected features for all people
    let allSelectedFeatures = {};
    // Store submitted data for all people
    let submittedData = {};

    // Generate forms for each person
    function generateForms(peopleCount) {
        const formsContainer = document.getElementById("forms-container");
    
        // Clear previous forms
        formsContainer.innerHTML = "";
        allSelectedFeatures = {}; // Reset stored features
        submittedData = {}; // Reset submitted data
    
        // Generate forms for each person
        for (let i = 1; i <= peopleCount; i++) {
        allSelectedFeatures[`person-${i}`] = []; // Initialize features array for this person
    
        const formHTML = `
            <div class="person-form" id="person-${i}">
            <h2>Traveler ${i}</h2>
            <form class="questionnaire" data-person="${i}">
                <!-- Budget range slider question -->
                <div class="question">
                <label>1. What's your budget range?</label>
                <div class="dual-range-slider" id="range-slider-${i}">
                    <div class="slider-track"></div>
                    <div class="slider-range" id="slider-range-${i}"></div>
                    <div class="slider-thumb min" id="min-thumb-${i}"></div>
                    <div class="slider-thumb max" id="max-thumb-${i}"></div>
                </div>
                <div class="range-values">
                    <div class="range-value" id="min-value-${i}">0€</div>
                    <span>to</span>
                    <div class="range-value" id="max-value-${i}">5000€</div>
                </div>
                <input type="hidden" id="min-budget-${i}" name="min-budget-${i}" value="0">
                <input type="hidden" id="max-budget-${i}" name="max-budget-${i}" value="5000">
                <input type="hidden" id="budget-range-${i}" name="budget-range-${i}" value="0-5000">
                </div>
    
                <!-- Multiple selection question -->
                <div class="question">
                <label>2. Select your desired vibes (add multiple):</label>
                <div class="multi-select-container">
                    <select id="product-features-${i}">
                    <option value="">-- Select a vibe --</option>
                    <option value="nightlife_and_entertainment">Nightlife and entertainment</option>
                    <option value="underrated_destinations">Underrated destinations</option>
                    <option value="beach">Beach</option>
                    <option value="art_and_culture">Art and culture</option>
                    <option value="great_food">Great food</option>
                    <option value="outdoor_adventures">Outdoor adventures</option>
                    </select>
                    <button type="button" class="add-feature secondary" data-person="${i}">Add</button>
                </div>
                <ul id="selected-items-${i}"></ul>
                <input type="hidden" id="selected-features-${i}" name="selected-features-${i}">
                </div>
    
                <!-- Dropdown menu question -->
                <div class="question">
                <label for="color-${i}">3. What is your preferred destination?</label>
                <select id="color-${i}" name="color-${i}">
                    <option value="">-- Select a destination --</option>
                    <option value="europe">Europe</option>
                    <option value="asia">Asia</option>
                    <option value="america">America</option>
                    <option value="africa">Africa</option>
                    <option value="oceania">Oceania</option>
                </select>
                </div>
    
                <!-- New dropdown question for starting point -->
                <div class="question">
                <label for="starting-point-${i}">4. What's your starting point?</label>
                <select id="starting-point-${i}" name="starting-point-${i}">
                    <option value="">-- Select a starting point --</option>
                    <option value="europe">Europe</option>
                    <option value="asia">Asia</option>
                    <option value="america">America</option>
                    <option value="africa">Africa</option>
                    <option value="oceania">Oceania</option>
                </select>
                </div>
    
                <button type="button" class="submit-person" data-person="${i}">Submit Traveler ${i}</button>
            </form>
            </div>
            <div class="person-summary" id="summary-${i}">
            <h3>Traveler ${i} - Submitted Answers</h3>
            <div id="summary-content-${i}"></div>
            <button type="button" class="modify-person tertiary" data-person="${i}">Modify Answers</button>
            </div>
        `;
    
        formsContainer.insertAdjacentHTML("beforeend", formHTML);
    
        // Initialize slider functionality for this person
        initDualRangeSlider(i);
        }
    
        setupEventListeners();
    }
  
    // Set up all event listeners
    function setupEventListeners() {
      // Add event listeners to all add-feature buttons
      document.querySelectorAll(".add-feature").forEach((button) => {
        button.addEventListener("click", function() {
          const personNum = this.getAttribute("data-person");
          const featureSelect = document.getElementById(
            `product-features-${personNum}`
          );
          const selectedValue = featureSelect.value;
          const selectedText =
            featureSelect.options[featureSelect.selectedIndex].text;
  
          if (
            selectedValue &&
            !allSelectedFeatures[`person-${personNum}`].includes(
              selectedValue
            )
          ) {
            allSelectedFeatures[`person-${personNum}`].push(selectedValue);
            updateSelectedFeaturesList(personNum);
            featureSelect.value = "";
          }
        });
      });
  
      // Add event listeners to all submit buttons
      document.querySelectorAll(".submit-person").forEach((button) => {
        button.addEventListener("click", function() {
          const personNum = this.getAttribute("data-person");
          submitPersonForm(personNum);
        });
      });
  
      // Add event listeners to all modify buttons
      document.querySelectorAll(".modify-person").forEach((button) => {
        button.addEventListener("click", function() {
          const personNum = this.getAttribute("data-person");
          const personForm = document.getElementById(`person-${personNum}`);
          const personSummary = document.getElementById(
            `summary-${personNum}`
          );
  
          // Remove this traveler's data from submittedData
          delete submittedData[`person-${personNum}`];
  
          // Show form and hide summary
          personForm.classList.remove("hidden");
          personSummary.style.display = "none";
  
          // Update save button visibility
          const peopleCount = parseInt(
            document.getElementById("people-count").value
          );
          if (window.saveAnswers && window.saveAnswers.updateSaveButtonVisibility) {
            window.saveAnswers.updateSaveButtonVisibility(
              peopleCount,
              submittedData
            );
          }
        });
      });
    }
  
    // Submit a person's form
    function submitPersonForm(personNum) {
        const personForm = document.getElementById(`person-${personNum}`);
        const personSummary = document.getElementById(`summary-${personNum}`);
    
        // Validate required fields
        const minBudget = document.getElementById(`min-budget-${personNum}`).value;
        const maxBudget = document.getElementById(`max-budget-${personNum}`).value;
        const destination = document.getElementById(`color-${personNum}`).value;
        const startingPoint = document.getElementById(`starting-point-${personNum}`).value;
        const features = allSelectedFeatures[`person-${personNum}`];
    
        if (parseInt(minBudget) >= parseInt(maxBudget)) {
        alert(`Traveler ${personNum}: Maximum budget must be greater than minimum budget.`);
        return;
        }
    
        if (!destination) {
        alert(`Traveler ${personNum}: Please select a preferred destination.`);
        return;
        }
    
        if (!startingPoint) {
        alert(`Traveler ${personNum}: Please select a starting point.`);
        return;
        }
    
        // Prepare data object
        submittedData[`person-${personNum}`] = {
        person: personNum,
        minBudget: minBudget,
        maxBudget: maxBudget,
        features: features,
        destination: destination,
        startingPoint: startingPoint,
        };
    
        // Update summary
        updateSummary(personNum);
    
        // Hide form and show summary
        personForm.classList.add("hidden");
        personSummary.style.display = "block";
    
        console.log(`Traveler ${personNum} data:`, submittedData[`person-${personNum}`]);
    
        // Check if all travelers have submitted and show save button
        const peopleCount = parseInt(document.getElementById("people-count").value);
        if (window.saveAnswers && window.saveAnswers.updateSaveButtonVisibility) {
        window.saveAnswers.updateSaveButtonVisibility(peopleCount, submittedData);
        }
    }
  
    // Update the visible list and hidden input for a specific person
    function updateSelectedFeaturesList(personNum) {
        const selectedItemsList = document.getElementById(`selected-items-${personNum}`);
        const selectedFeaturesInput = document.getElementById(`selected-features-${personNum}`);
    
        selectedItemsList.innerHTML = "";
        allSelectedFeatures[`person-${personNum}`].forEach((value, index) => {
        const li = document.createElement("li");
        const optionText = document.querySelector(
            `#product-features-${personNum} option[value="${value}"]`
        ).text;
        li.innerHTML = `${index + 1}. ${optionText} <span class="remove-item" data-value="${value}" data-person="${personNum}">×</span>`;
        selectedItemsList.appendChild(li);
        });
    
        // Update hidden input with comma-separated values
        selectedFeaturesInput.value = allSelectedFeatures[`person-${personNum}`].join(",");
    
        // Add event listeners to remove buttons
        selectedItemsList.querySelectorAll(".remove-item").forEach((button) => {
        button.addEventListener("click", function() {
            const valueToRemove = this.getAttribute("data-value");
            const person = this.getAttribute("data-person");
            const index = allSelectedFeatures[`person-${person}`].indexOf(valueToRemove);
            if (index > -1) {
            allSelectedFeatures[`person-${person}`].splice(index, 1);
            updateSelectedFeaturesList(person);
            }
        });
        });
    }
  
    // Update the summary for a specific person
    function updateSummary(personNum) {
        const data = submittedData[`person-${personNum}`];
        const summaryContent = document.getElementById(`summary-content-${personNum}`);
    
        if (!data) return;
    
        let featuresList = "";
        data.features.forEach((feature, index) => {
        const optionText = document.querySelector(
            `#product-features-${personNum} option[value="${feature}"]`
        ).text;
        featuresList += `<li>${index + 1}. ${optionText}</li>`;
        });
    
        summaryContent.innerHTML = `
        <p><strong>Budget Range:</strong> ${data.minBudget}€ - ${data.maxBudget}€</p>
        <p><strong>Preferred Vibes:</strong></p>
        <ul>${featuresList}</ul>
        <p><strong>Preferred Destination:</strong> ${data.destination}</p>
        <p><strong>Starting Point:</strong> ${data.startingPoint}</p>
        `;
    }

      // Initialize the main button listener
  document.getElementById("generate-forms").addEventListener("click", function() {
    console.log("Generate forms button clicked");
    const peopleCount = parseInt(document.getElementById("people-count").value);
    generateForms(peopleCount);
  });
});