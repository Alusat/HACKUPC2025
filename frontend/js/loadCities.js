async function loadCities() {
    try {
      const response = await fetch('data/locations.csv');
      const csvData = await response.text();
      const cities = csvData.split('\n').filter(city => city.trim() !== '');
      return cities;
    } catch (error) {
      console.error('Error loading cities:', error);
      return ['NULL']; // Fallback
    }
  }
  
  function populateDropdowns(cities) {
    document.querySelectorAll('[id^="starting-point-"], [id^="color-"]').forEach(dropdown => {
      // Clear existing options except first
      while (dropdown.options.length > 1) {
        dropdown.remove(1);
      }
      
      // Add new options
      cities.forEach(city => {
        const option = new Option(city.trim(), city.trim().toLowerCase());
        dropdown.add(option);
      });
    });
  }
  
  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', async () => {
    const cities = await loadCities();
    populateDropdowns(cities);
    
    // Update the generate forms function to use these cities
    window.dynamicCities = cities;
  });