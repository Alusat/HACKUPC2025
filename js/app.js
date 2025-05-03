// js/app.js

// Using Preact (as included in your HTML)
// ***** IMPORT createRef *****
const { h, render, Component, createRef } = preact;

class FlightResultsApp extends Component {
    constructor() {
        super();
        this.state = {
            results: [],
            isLoading: true,
            error: null,
            sortBy: 'rank',
            sortOrder: 'asc'
        };
        // ***** ADD Refs for map *****
        this.mapInstance = null;
        this.markerGroup = null;
        this.mapContainerRef = createRef(); // Use createRef from Preact
    }

    componentDidMount() {
        // --- Your existing fetch logic ---
        fetch('http://localhost:3000/data/prologoutput.json') // Adjust if your JSON name or path changed
            .then(response => {
                if (!response.ok) {
                    console.warn('Server fetch failed, trying local file:', response.statusText);
                    // ***** ENSURE THIS PATH IS CORRECT RELATIVE TO YOUR HTML/SERVER *****
                    return fetch('data/ranked_cities_top100.json');
                }
                // If first fetch is ok, clone the response so it can be read twice
                // if the next .then needs to re-read it (though here it shouldn't)
                return response.clone().json().catch(() => response.json()); // Handle potential non-JSON from server ok response
            })
            .then(responseOrData => {
                // Check if it's a Response object (from fallback) or already parsed data
                if (responseOrData instanceof Response) {
                     if (!responseOrData.ok) { // Check if the fallback fetch failed
                         throw new Error(`Failed to load data from server and local file.`);
                     }
                     return responseOrData.json(); // Parse JSON from fallback
                }
                return responseOrData; // Already parsed data from primary fetch
            })
            .then(data => {
                 // ***** Add data validation *****
                 if (!Array.isArray(data)) {
                    throw new Error("Loaded data is not a valid array.");
                 }
                 if (data.length > 0 && (data[0].lat === undefined || data[0].long === undefined)) {
                     console.warn("Data loaded but might be missing lat/long fields.");
                     // Decide if this is an error or just a warning
                     // throw new Error('Data loaded but is missing required lat/long fields.');
                 }
                this.setState({
                    results: data,
                    isLoading: false,
                    error: null // Clear any previous error on success
                });
            })
            .catch(error => {
                this.setState({
                    error: `Error loading data: ${error.message}`,
                    isLoading: false,
                    results: [] // Clear results on error
                });
                console.error('Data loading error:', error);
            });
    }

    // ***** ADD componentDidUpdate for map initialization *****
    componentDidUpdate(prevProps, prevState) {
        // Check if data just finished loading successfully
        const dataJustLoaded = !this.state.isLoading && prevState.isLoading;
        const resultsAvailable = this.state.results.length > 0;
        const noError = !this.state.error;

        if (dataJustLoaded && noError) {
            // Data is loaded, attempt to initialize or update the map
            // It's okay if resultsAvailable is false, initMap will handle it
            this.initOrUpdateMap();
        }
        // Optional: Add logic here if you need the map to update
        // when the *filter* changes (not just sort)
    }

    // ***** ADD componentWillUnmount for cleanup *****
    componentWillUnmount() {
        if (this.mapInstance) {
            this.mapInstance.remove();
            this.mapInstance = null;
            this.markerGroup = null;
        }
    }

    // ***** ADD initOrUpdateMap Method *****
    initOrUpdateMap = () => {
        if (typeof L === 'undefined') {
            console.error("Leaflet library (L) not found.");
            return; // Or maybe set an error state?
        }
        if (!this.mapContainerRef.current) {
            console.error("Map container DOM element not found yet.");
             // Could retry, but indicates a timing issue in render/update
            return;
        }

        const { results } = this.state;
        const validCoords = results
            .filter(r => typeof r.lat === 'number' && typeof r.long === 'number')
            .map(r => [r.lat, r.long]);

        // --- Map Initialization or Update ---
        if (this.mapInstance) {
            // Map exists: Update markers and view
            if (this.markerGroup) {
                this.markerGroup.clearLayers();
            } else {
                this.markerGroup = L.layerGroup().addTo(this.mapInstance);
            }

            if (validCoords.length > 0) {
                results.forEach(result => {
                    if (typeof result.lat === 'number' && typeof result.long === 'number') {
                        const marker = L.marker([result.lat, result.long]);
                        marker.bindPopup(`<b>${result.city || 'N/A'}</b><br>${result.IATA || 'N/A'}`);
                        this.markerGroup.addLayer(marker);
                    }
                });
                const bounds = L.latLngBounds(validCoords);
                this.mapInstance.flyToBounds(bounds, { padding: [30, 30], duration: 0.5 });
            } else {
                 // No valid coords on update, maybe zoom out
                this.mapInstance.flyTo([20, 0], 2, { duration: 0.5 });
            }

        } else {
            // Map doesn't exist: Initialize
            if (validCoords.length > 0) {
                 const bounds = L.latLngBounds(validCoords);
                 this.mapInstance = L.map(this.mapContainerRef.current).fitBounds(bounds, { padding: [30, 30] });
            } else {
                 console.warn("No valid coordinates found in initial results. Setting default map view.");
                 this.mapInstance = L.map(this.mapContainerRef.current).setView([20, 0], 2); // Default world view
            }

             // Add tile layer (only once)
             L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(this.mapInstance);

            // Create marker group and add markers (only once on init)
            this.markerGroup = L.layerGroup().addTo(this.mapInstance);
            if (validCoords.length > 0) {
                 results.forEach(result => {
                    if (typeof result.lat === 'number' && typeof result.long === 'number') {
                        const marker = L.marker([result.lat, result.long]);
                        marker.bindPopup(`<b>${result.city || 'N/A'}</b><br>${result.IATA || 'N/A'}`);
                        this.markerGroup.addLayer(marker);
                    }
                });
            }
        }
    }


    handleSort = (column) => {
        this.setState(prev => ({
            sortBy: column,
            sortOrder: prev.sortBy === column ?
                     (prev.sortOrder === 'asc' ? 'desc' : 'asc') : 'asc'
        }));
        // Sorting does not require map update unless you filter data
    }

    render() {
        const { results, isLoading, error, sortBy, sortOrder } = this.state;

        // --- Status Message Rendering (early return) ---
        if (isLoading) {
            return h('div', { class: 'flight-results' }, // Wrap in main container for consistent styling
                 h('h1', {}, 'Resultados de Vuelos'),
                 h('div', { class: 'status-message loading' }, 'Cargando resultados...')
            );
        }
        if (error) {
             return h('div', { class: 'flight-results' },
                 h('h1', {}, 'Resultados de Vuelos'),
                 h('div', { class: 'status-message error' }, `Error: ${error}`) // error state contains message
            );
        }
        // No early return for no results, show empty table/map area


        // --- Sorting Logic (only if results exist) ---
        const sortedResults = results.length > 0 ? [...results].sort((a, b) => {
            const valA = a[sortBy];
            const valB = b[sortBy];

             // Handle numeric sorts
             if (['rank', 'score', 'lat', 'long'].includes(sortBy)) { // Added lat/long sort check
                const numA = Number(valA) || 0;
                const numB = Number(valB) || 0;
                return sortOrder === 'asc' ? numA - numB : numB - numA;
             }
            // Handle string sorts
            const strA = String(valA ?? '');
            const strB = String(valB ?? '');
            return sortOrder === 'asc'
                ? strA.localeCompare(strB)
                : strB.localeCompare(strA);
        }) : []; // Empty array if no results


        // --- Helper Function (can be outside render or inside) ---
        const formatCoordinate = (coord) => {
            if (typeof coord === 'number') {
                return coord.toFixed(6);
            }
            return '-';
        };

        // --- Main Render Structure ---
        return h('div', { class: 'flight-results' },
            h('h1', {}, 'Resultados de Vuelos'),

            // Show "No results" message if applicable, otherwise render table
            results.length === 0 && !isLoading && !error
                ? h('div', { class: 'status-message no-results' }, 'No hay resultados')
                : h('div', { class: 'results-table' },
                    h('div', { class: 'table-header' },
                        h('div', { class: `header-cell ${sortBy === 'rank' ? 'active' : ''}`, onClick: () => this.handleSort('rank') }, 'Posición'),
                        h('div', { class: `header-cell ${sortBy === 'IATA' ? 'active' : ''}`, onClick: () => this.handleSort('IATA') }, 'IATA'),
                        h('div', { class: `header-cell ${sortBy === 'city' ? 'active' : ''}`, onClick: () => this.handleSort('city') }, 'Ciudad'),
                        h('div', { class: `header-cell ${sortBy === 'destination_fit' ? 'active' : ''}`, onClick: () => this.handleSort('destination_fit') }, 'Destino'),
                        h('div', { class: `header-cell ${sortBy === 'distance_fit' ? 'active' : ''}`, onClick: () => this.handleSort('distance_fit') }, 'Distancia'),
                        h('div', { class: `header-cell ${sortBy === 'vibe_fit' ? 'active' : ''}`, onClick: () => this.handleSort('vibe_fit') }, 'Ambiente'),
                         // Added optional sorting handlers/active states for lat/long
                        h('div', { class: `header-cell ${sortBy === 'lat' ? 'active' : ''}`, onClick: () => this.handleSort('lat') }, 'Latitud'),
                        h('div', { class: `header-cell ${sortBy === 'long' ? 'active' : ''}`, onClick: () => this.handleSort('long') }, 'Longitud')
                    ),
                    // Map over sorted results
                    sortedResults.map(result =>
                        h('div', { class: 'table-row', key: result.IATA || result.rank }, // Use rank as fallback key
                            h('div', { class: 'row-cell' }, result.rank ?? '-'), // Use nullish coalescing for defaults
                            h('div', { class: 'row-cell' }, result.IATA ?? '-'),
                            h('div', { class: 'row-cell' }, result.city ?? '-'),
                            h('div', { class: 'row-cell' }, result.destination_fit ?? '-'),
                            h('div', { class: 'row-cell' }, result.distance_fit ?? '-'),
                            h('div', { class: 'row-cell' }, result.vibe_fit ?? '-'),
                            h('div', { class: 'row-cell' }, formatCoordinate(result.lat)),
                            h('div', { class: 'row-cell' }, formatCoordinate(result.long))
                        )
                    )
                  ), // End of results-table div

            // ***** ADD Map Container Div *****
            // Render the div always, map init logic will handle population
            h('div', { id: 'mapid', ref: this.mapContainerRef })

        ); // End of flight-results div
    }
}

// Ensure the target element exists in your HTML: <div id="app"></div>
render(h(FlightResultsApp), document.getElementById('app'));