// Initialize date range slider functionality
function initDateRangeSlider(containerId) {
    const container = document.getElementById(containerId);
    const startDateInput = container.querySelector('.start-date');
    const endDateInput = container.querySelector('.end-date');
    const saveButton = container.querySelector('.save-date-range');
  
    saveButton.addEventListener('click', () => {
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
  
      // Save the date range (you can extend this to save to a server or local storage)
      const dateRange = { startDate, endDate };
      console.log('Date range selected:', dateRange);
  
      // Example: Save to localStorage
      localStorage.setItem('selectedDateRange', JSON.stringify(dateRange));
      //alert('Date range saved successfully!');
    });
  }
  
  // Example usage: Initialize the date range slider for a specific container
  document.addEventListener('DOMContentLoaded', () => {
    initDateRangeSlider('date-range-container');
  });