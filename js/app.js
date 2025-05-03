// js/app.js

const { h, render, Component, createRef } = preact;

class FlightResultsApp extends Component {
    constructor() {
        super();
        this.state = {
            results: [],
            isLoading: true,
            error: null,
            // Default sort key
            sortBy: 'rank',
            sortOrder: 'asc'
        };
        // Map related properties
        this.mapInstance = null;
        this.markerGroup = null;
        this.mapContainerRef = createRef(); // Ref for the map container div
    }

    // Fetch data when the component mounts
    componentDidMount() {
        fetch('http://localhost:3000/data/prologoutput.json') // Attempt server fetch first
            .then(response => {
                if (!response.ok) {
                    // If server fails, try local file
                    console.warn('Server fetch failed, trying local file:', response.statusText);
                    // Ensure this path is correct relative to your HTML/server
                    return fetch('data/ranked_cities_top100.json');
                }
                // Clone response if primary fetch is okay (good practice, though maybe not strictly needed here)
                return response.clone().json().catch(() => response.json());
            })
            .then(responseOrData => {
                // Handle whether we have a Response object (from fallback) or parsed data
                if (responseOrData instanceof Response) {
                     if (!responseOrData.ok) { // Check if fallback also failed
                         throw new Error(`Failed to load data from server and local file.`);
                     }
                     return responseOrData.json(); // Parse JSON from fallback
                }
                return responseOrData; // Already parsed data from primary
            })
            .then(data => {
                 // Basic data validation
                 if (!Array.isArray(data)) {
                    throw new Error("Loaded data is not a valid array.");
                 }
                 // Check if essential coordinate data might be missing (optional check)
                 if (data.length > 0 && (data[0].lat === undefined || data[0].long === undefined)) {
                     console.warn("Data loaded but might be missing lat/long fields in first item.");
                 }
                // Update state with successful data load
                this.setState({
                    results: data,
                    isLoading: false,
                    error: null // Clear any previous error
                });
            })
            .catch(error => {
                // Update state on error during fetch/parse
                this.setState({
                    error: `Error loading data: ${error.message}`,
                    isLoading: false,
                    results: [] // Clear results on error
                });
                console.error('Data loading error:', error);
            });
    }

    // Initialize or update the map after the component updates (e.g., after data loads)
    componentDidUpdate(prevProps, prevState) {
        const dataJustLoaded = !this.state.isLoading && prevState.isLoading;
        const noError = !this.state.error;

        // Initialize/update map only once after data has loaded successfully
        if (dataJustLoaded && noError) {
            this.initOrUpdateMap();
        }
    }

    // Clean up the map instance when the component is removed from the DOM
    componentWillUnmount() {
        if (this.mapInstance) {
            this.mapInstance.remove();
            this.mapInstance = null;
            this.markerGroup = null;
        }
    }

    // Function to initialize the Leaflet map or update markers
    initOrUpdateMap = () => {
        // Ensure Leaflet library is loaded
        if (typeof L === 'undefined') {
            console.error("Leaflet library (L) not found.");
            return;
        }
        // Ensure the map container div is available in the DOM
        if (!this.mapContainerRef.current) {
            console.error("Map container DOM element not found yet.");
            return;
        }

        const { results } = this.state;
        // Get coordinates only from results that have valid lat/long numbers
        const validCoords = results
            .filter(r => typeof r.lat === 'number' && typeof r.long === 'number')
            .map(r => [r.lat, r.long]);

        // --- Map Initialization or Update Logic ---
        if (this.mapInstance) {
            // Map already exists: Update markers and view

            // Clear existing markers from the group
            if (this.markerGroup) {
                this.markerGroup.clearLayers();
            } else {
                // Create group if it doesn't exist (shouldn't happen often here)
                this.markerGroup = L.layerGroup().addTo(this.mapInstance);
            }

            // Add new markers based on current results
            if (validCoords.length > 0) {
                results.forEach(result => {
                    if (typeof result.lat === 'number' && typeof result.long === 'number') {
                        const marker = L.marker([result.lat, result.long]);
                        // Use lowercase 'iata' key from JSON
                        const popupContent = `<b>${result.city || 'N/A'}</b><br>${result.iata || 'N/A'}`;
                        marker.bindPopup(popupContent);
                        // Store a reference to the marker on the result object for easy popup opening
                        result._marker = marker;
                        this.markerGroup.addLayer(marker);
                    }
                });
                // Adjust map view to fit all new markers
                const bounds = L.latLngBounds(validCoords);
                this.mapInstance.flyToBounds(bounds, { padding: [30, 30], duration: 0.5 });
            } else {
                // No valid coordinates in results, fly to a default view
                this.mapInstance.flyTo([20, 0], 2, { duration: 0.5 });
            }

        } else {
            // Map doesn't exist: Initialize it for the first time

            // Set initial view: fit valid coordinates or use default world view
            if (validCoords.length > 0) {
                 const bounds = L.latLngBounds(validCoords);
                 this.mapInstance = L.map(this.mapContainerRef.current).fitBounds(bounds, { padding: [30, 30] });
            } else {
                 console.warn("No valid coordinates found in initial results. Setting default map view.");
                 this.mapInstance = L.map(this.mapContainerRef.current).setView([20, 0], 2);
            }

             // Add the background tile layer (only needs to be done once)
             L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.mapInstance);

            // Create the marker group and add initial markers
            this.markerGroup = L.layerGroup().addTo(this.mapInstance);
            if (validCoords.length > 0) {
                 results.forEach(result => {
                    if (typeof result.lat === 'number' && typeof result.long === 'number') {
                        const marker = L.marker([result.lat, result.long]);
                         // Use lowercase 'iata' key from JSON
                        const popupContent = `<b>${result.city || 'N/A'}</b><br>${result.iata || 'N/A'}`;
                        marker.bindPopup(popupContent);
                        // Store marker reference
                        result._marker = marker;
                        this.markerGroup.addLayer(marker);
                    }
                });
            }
        }
    }

    // Handler for clicking table headers to sort
    handleSort = (column) => {
        this.setState(prev => ({
            sortBy: column, // The column key (e.g., 'rank', 'iata', 'city')
            // Toggle sort order or set to 'asc' if changing column
            sortOrder: prev.sortBy === column ?
                     (prev.sortOrder === 'asc' ? 'desc' : 'asc') : 'asc'
        }));
        // Note: Sorting the display order doesn't require updating the map markers themselves
    }

    // Handler for clicking a table row
    handleRowClick = (result) => {
        // Check if map is ready and the clicked result has valid coordinates
        if (this.mapInstance && typeof result.lat === 'number' && typeof result.long === 'number') {
            const targetLatLng = [result.lat, result.long];
            const targetZoom = 14; // Desired zoom level when flying to a point

            // Animate map view to the target location
            this.mapInstance.flyTo(targetLatLng, targetZoom, {
                duration: 0.8 // Animation duration in seconds
            });

            // Scroll the map container into the viewport
            if (this.mapContainerRef.current) {
                this.mapContainerRef.current.scrollIntoView({
                    behavior: 'smooth', // Use smooth scrolling animation
                    block: 'start'      // Align top of map with top of viewport
                });
            }

            // Attempt to open the popup for the corresponding marker
            if (result._marker) { // Check if marker reference exists
                 // Use a small delay to allow map panning/scrolling animation to start
                 setTimeout(() => {
                     result._marker.openPopup();
                 }, 300); // Adjust delay if needed (milliseconds)
            }

        } else {
             // Log a warning if map/coords aren't ready for the clicked row
             // Use lowercase 'iata' key from JSON
            console.warn("Map not ready or invalid coordinates for clicked row:", result.iata);
        }
    }

    // Render the component UI
    render() {
        const { results, isLoading, error, sortBy, sortOrder } = this.state;

        // --- Render loading state ---
        if (isLoading) {
            return h('div', { class: 'flight-results' },
                 h('h1', {}, 'Resultados de Vuelos'),
                 h('div', { class: 'status-message loading' }, 'Cargando resultados...')
            );
        }
        // --- Render error state ---
        if (error) {
             return h('div', { class: 'flight-results' },
                 h('h1', {}, 'Resultados de Vuelos'),
                 h('div', { class: 'status-message error' }, `Error: ${error}`) // Display error message from state
            );
        }

        // --- Sort results if data is available ---
        const sortedResults = results.length > 0 ? [...results].sort((a, b) => {
            const valA = a[sortBy]; // Get value based on current sort column
            const valB = b[sortBy];

             // Check if sorting numerically (add any other numeric columns if needed)
             if (['rank', 'score', 'lat', 'long'].includes(sortBy)) {
                const numA = Number(valA) || 0; // Treat non-numbers as 0 for comparison
                const numB = Number(valB) || 0;
                return sortOrder === 'asc' ? numA - numB : numB - numA; // Asc/Desc numeric sort
             }

            // Default to string sort for other columns (handles 'iata', 'city', etc.)
            const strA = String(valA ?? ''); // Convert null/undefined to empty string
            const strB = String(valB ?? '');
            return sortOrder === 'asc'
                ? strA.localeCompare(strB) // Ascending string sort
                : strB.localeCompare(strA); // Descending string sort
        }) : []; // Return empty array if no results to sort


        // Helper function to format coordinates for display
        const formatCoordinate = (coord) => {
            if (typeof coord === 'number') { return coord.toFixed(6); } // Format to 6 decimal places
            return '-'; // Placeholder for invalid/missing data
        };

        // --- Render main UI (table and map) ---
        return h('div', { class: 'flight-results' },
            h('h1', {}, 'Resultados de Vuelos'),

            // Conditionally render "No results" message or the results table
            results.length === 0 && !isLoading && !error
                ? h('div', { class: 'status-message no-results' }, 'No hay resultados')
                : h('div', { class: 'results-table' },
                    // Table Header Row
                    h('div', { class: 'table-header' },
                        // Header cells with onClick for sorting and 'active' class indication
                        h('div', { class: `header-cell ${sortBy === 'rank' ? 'active' : ''}`, onClick: () => this.handleSort('rank') }, 'Posición'),
                        // Use lowercase 'iata' for sort key and active check
                        h('div', { class: `header-cell ${sortBy === 'iata' ? 'active' : ''}`, onClick: () => this.handleSort('iata') }, 'IATA'),
                        h('div', { class: `header-cell ${sortBy === 'city' ? 'active' : ''}`, onClick: () => this.handleSort('city') }, 'Ciudad'),
                        h('div', { class: `header-cell ${sortBy === 'destination_fit' ? 'active' : ''}`, onClick: () => this.handleSort('destination_fit') }, 'Destino'),
                        h('div', { class: `header-cell ${sortBy === 'distance_fit' ? 'active' : ''}`, onClick: () => this.handleSort('distance_fit') }, 'Distancia'),
                        h('div', { class: `header-cell ${sortBy === 'vibe_fit' ? 'active' : ''}`, onClick: () => this.handleSort('vibe_fit') }, 'Ambiente'),
                        h('div', { class: `header-cell ${sortBy === 'lat' ? 'active' : ''}`, onClick: () => this.handleSort('lat') }, 'Latitud'),
                        h('div', { class: `header-cell ${sortBy === 'long' ? 'active' : ''}`, onClick: () => this.handleSort('long') }, 'Longitud')
                    ),
                    // Table Body Rows (map over sorted results)
                    sortedResults.map(result =>
                        // Each row div is clickable
                        h('div', {
                            class: 'table-row',
                            // Use lowercase 'iata' for key (or rank as fallback)
                            key: result.iata || result.rank,
                            // Call handleRowClick with the specific result data
                            onClick: () => this.handleRowClick(result)
                          },
                            // Row cells displaying data (use ?? '-' for default if data missing)
                            h('div', { class: 'row-cell' }, result.rank ?? '-'),
                            // Use lowercase 'iata' for display
                            h('div', { class: 'row-cell' }, result.iata ?? '-'),
                            h('div', { class: 'row-cell' }, result.city ?? '-'),
                            h('div', { class: 'row-cell' }, result.destination_fit ?? '-'),
                            h('div', { class: 'row-cell' }, result.distance_fit ?? '-'),
                            h('div', { class: 'row-cell' }, result.vibe_fit ?? '-'),
                            h('div', { class: 'row-cell' }, formatCoordinate(result.lat)),
                            h('div', { class: 'row-cell' }, formatCoordinate(result.long))
                        )
                    )
                  ), // End of results-table div

            // The map container div, linked via ref
            h('div', { id: 'mapid', ref: this.mapContainerRef })

        ); // End of flight-results div
    }
}

// Mount the Preact application to the '#app' element in the HTML
render(h(FlightResultsApp), document.getElementById('app'));