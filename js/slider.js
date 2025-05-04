// Initialize dual range slider functionality
function initDualRangeSlider(personNum) {
    const slider = document.getElementById(`range-slider-${personNum}`);
    const range = document.getElementById(`slider-range-${personNum}`);
    const minThumb = document.getElementById(`min-thumb-${personNum}`);
    const maxThumb = document.getElementById(`max-thumb-${personNum}`);
    const minValue = document.getElementById(`min-value-${personNum}`);
    const maxValue = document.getElementById(`max-value-${personNum}`);
    const minInput = document.getElementById(`min-budget-${personNum}`);
    const maxInput = document.getElementById(`max-budget-${personNum}`);
    const rangeInput = document.getElementById(`budget-range-${personNum}`);
  
    const min = 0;
    const max = 1000;
    let minVal = 0;
    let maxVal = 1000;
  
    // Update slider positions and values
    function updateSlider() {
      const minPercent = ((minVal - min) / (max - min)) * 100;
      const maxPercent = ((maxVal - min) / (max - min)) * 100;
  
      minThumb.style.left = `${minPercent}%`;
      maxThumb.style.left = `${maxPercent}%`;
      range.style.left = `${minPercent}%`;
      range.style.width = `${maxPercent - minPercent}%`;
  
      // Ensure values are natural numbers (no decimals)
      minVal = Math.round(minVal);
      maxVal = Math.round(maxVal);
  
      minValue.textContent = `${minVal}€`;
      maxValue.textContent = `${maxVal}€`;
      minInput.value = minVal;
      maxInput.value = maxVal;
      rangeInput.value = `${minVal}-${maxVal}`;
    }
  
    // Handle thumb dragging
    function setupThumb(thumb, isMin) {
      thumb.addEventListener("mousedown", function (e) {
        e.preventDefault();
        const startX = e.clientX;
        const startLeft = parseFloat(
          thumb.style.left || (isMin ? "0" : "100")
        );
  
        function moveThumb(e) {
          const sliderRect = slider.getBoundingClientRect();
          const newLeft =
            startLeft + ((e.clientX - startX) / sliderRect.width) * 100;
          // Round to nearest integer immediately
          const newVal = Math.round(min + (newLeft / 100) * (max - min));
  
          if (isMin) {
            minVal = Math.min(Math.max(newVal, min), maxVal - 50);
          } else {
            maxVal = Math.max(Math.min(newVal, max), minVal + 50);
          }
  
          updateSlider();
        }
  
        function stopDragging() {
          document.removeEventListener("mousemove", moveThumb);
          document.removeEventListener("mouseup", stopDragging);
        }
  
        document.addEventListener("mousemove", moveThumb);
        document.addEventListener("mouseup", stopDragging);
      });
    }
  
    // Initialize both thumbs
    setupThumb(minThumb, true);
    setupThumb(maxThumb, false);
  
    // Set initial values
    updateSlider();
  }