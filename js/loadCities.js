console.log("Script is loading"); // This should appear immediately
// Cache for all cities
let cachedCities = null;

async function loadCities() {
  // Return cached data if available
  if (cachedCities) return cachedCities;
  
  try {
    const response = await fetch('data/locations.csv');
    const csvData = await response.text();
    cachedCities = csvData.split('\n')
      .filter(city => city.trim() !== '')
      .map(city => ({
        id: city.trim(),//.toLowerCase(),
        text: city.trim()
      }));
    return cachedCities;
  } catch (error) {
    console.error('Error loading cities:', error);
    return [{ id: 'null', text: 'NULL' }]; // Fallback in Select2 format
  }
    // In loadCities(), add debug logging:
    console.log("First 5 cities:", cachedCities.slice(0, 5));
    console.log("Total cities:", cachedCities.length);
}

function initializeSelect2(selectElement, cities) {
  $(selectElement).select2({
    placeholder: '-- Placeholder --',
    allowClear: true,
    data: cities,
    minimumInputLength: 1, // Require typing before showing options
    dropdownAutoWidth: true,
    width: '100%',
    closeOnSelect: true,
    language: {
      noResults: function() {
        return "No results found";
      },
      searching: function() {
        return "Searching...";
      }
    }
  });
}

// Main initialization
document.addEventListener('DOMContentLoaded', async () => {
  // Load cities data
  const cities = await loadCities();
  
  // Initialize existing select elements
  document.querySelectorAll('[id^="starting-point-"], [id^="color-"]').forEach(select => {
    initializeSelect2(select, cities);
  });
  
  // Store for dynamic forms (if needed)
  window.dynamicCities = cities;
});

// For dynamically added forms (if you're adding dropdowns after page load)
function addNewDropdown(container, index) {
  const selectId = `starting-point-${index}`;
  
  // Create the select element
  const selectHTML = `
    <select id="${selectId}" name="${selectId}">
      <option value=""></option>
    </select>
  `;
  
  // Add to container
  container.insertAdjacentHTML('beforeend', selectHTML);
  
  // Initialize Select2
  initializeSelect2(document.getElementById(selectId), window.dynamicCities);
}