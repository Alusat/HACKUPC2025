// Export form generation functions
export function generatePersonForm(i) {
    return `
      <div class="person-form" id="person-${i}">
        <h2>Traveler ${i}</h2>
        <form class="questionnaire" data-person="${i}">
          ${generateBudgetQuestion(i)}
          ${generateVibesQuestion(i)}
          ${generateDestinationQuestion(i)}
          ${generateStartingPointQuestion(i)}
          <button type="button" class="submit-person" data-person="${i}">Submit Traveler ${i}</button>
        </form>
      </div>
      ${generateSummarySection(i)}
    `;
  }
  
  function generateBudgetQuestion(i) {
    return `
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
    `;
  }
  
  function generateVibesQuestion(i) {
    return `
      <div class="question">
        <label>2. Select your desired vibes (add multiple):</label>
        <div class="multi-select-container">
          <select id="product-features-${i}">
            <option value=""> </option>
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
    `;
  }
  
  function generateDestinationQuestion(i) {
    return `
      <div class="question">
        <label for="destination-${i}">3. What is your preferred destination?</label>
        <select id="destination-${i}" name="destination-${i}" data-placeholder=" ">
          <option value=""></option>
        </select>
      </div>
    `;
  }
  
  function generateStartingPointQuestion(i) {
    return `
      <div class="question">
        <label for="starting-point-${i}">4. What's your starting point?</label>
        <select id="starting-point-${i}" name="starting-point-${i}" data-placeholder=" ">
          <option value=""></option>
        </select>
      </div>
    `;
  }
  
  function generateSummarySection(i) {
    return `
      <div class="person-summary" id="summary-${i}">
        <h3>Traveler ${i} - Submitted Answers</h3>
        <div id="summary-content-${i}"></div>
        <button type="button" class="modify-person tertiary" data-person="${i}">Modify Answers</button>
      </div>
    `;
  }