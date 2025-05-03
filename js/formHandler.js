import { generatePersonForm } from './formTemplates.js';

// State management
allSelectedFeatures: {};
submittedData: {};


// Main initialization
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById("generate-forms").addEventListener("click", function() {
    const peopleCount = parseInt(document.getElementById("people-count").value);
    generateForms(peopleCount);
  });
});

// Core functions
function generateForms(peopleCount) {
  const formsContainer = document.getElementById("forms-container");
  formsContainer.innerHTML = "";
  allSelectedFeatures = {};
  submittedData = {};

  for (let i = 1; i <= peopleCount; i++) {
    allSelectedFeatures[`person-${i}`] = [];
    formsContainer.insertAdjacentHTML("beforeend", generatePersonForm(i));
    initDualRangeSlider(i);
  }

  setupEventListeners();
}

// Set up all event listeners
async function setupEventListeners() {
  // Load data
  const cities = await loadCities();

  document.querySelectorAll('[id^="destination-"], [id^="starting-point-"]').forEach(select => {
  console.log("Initializing dropdown:", select.id);
  // Initialize both dropdowns with the same cities data
  initializeSelect2(select, cities);
  });

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
  const destination = document.getElementById(`destination-${personNum}`).value;
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

// Make core functions available globally if needed
window.FormManager = {
  generateForms,
  submitPersonForm
};