// Using Preact instead of "Recreate"
const { h, render, Component } = preact;

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
    }

    componentDidMount() {
        // Option 1: If you've moved prologoutput.json to your server's static files
        fetch('http://localhost:3000/data/prologoutput.json') // Adjust if your JSON name or path changed
            .then(response => {
                if (!response.ok) {
                    // Try local file first if server fetch has CORS or other issues during development
                    console.warn('Server fetch failed, trying local file:', response.statusText);
                    return fetch('data/ranked_cities_top100.json'); // Assuming this is the correct local path/name
                }
                return response.json();
            })
            .then(response => { // Handle potential second fetch
                if (!response.ok && this.state.isLoading) { // Check if this is the fallback response and it also failed
                    throw new Error(`Failed to load data from server and local file.`);
                }
                return response.json();
            })
            .then(data => {
                this.setState({
                    results: data,
                    isLoading: false
                });
            })
            .catch(error => {
                 // If the primary fetch failed AND the fallback failed, this catch handles it.
                 // If only the primary failed but fallback succeeded, the previous .then handles the data.
                this.setState({
                    error: `Error loading data: ${error.message}`,
                    isLoading: false
                });
                console.error('Data loading error:', error);
            });
    }


    handleSort = (column) => {
        this.setState(prev => ({
            sortBy: column,
            sortOrder: prev.sortBy === column ?
                     (prev.sortOrder === 'asc' ? 'desc' : 'asc') : 'asc'
        }));
    }

    render() {
        const { results, isLoading, error, sortBy, sortOrder } = this.state;

        if (isLoading) {
            return h('div', { class: 'status-message loading' }, 'Cargando resultados...');
        }

        if (error) {
            return h('div', { class: 'status-message error' },
                `Error: ${error}` // Display the simplified error state
            );
        }

        if (results.length === 0) {
            return h('div', { class: 'status-message no-results' }, 'No hay resultados');
        }

        // Ordenar resultados
        const sortedResults = [...results].sort((a, b) => {
            const valA = a[sortBy];
            const valB = b[sortBy];

            // Handle numeric sorts (rank, score, potentially lat/long in the future)
            if (typeof valA === 'number' && typeof valB === 'number') {
                 return sortOrder === 'asc' ? valA - valB : valB - valA;
            }
             // Handle potential null/undefined values robustly during string sort
            const strA = String(valA ?? ''); // Use empty string for null/undefined
            const strB = String(valB ?? '');

            // Handle string sorts
            return sortOrder === 'asc'
                ? strA.localeCompare(strB)
                : strB.localeCompare(strA);
        });


        // Function to safely format numbers, handles non-numeric types
        const formatCoordinate = (coord) => {
            if (typeof coord === 'number') {
                return coord.toFixed(6); // Adjust decimal places as needed
            }
            return '-'; // Placeholder for missing or invalid data
        };

        return h('div', { class: 'flight-results' },
            h('h1', {}, 'Resultados de Vuelos'),
            h('div', { class: 'results-table' },
                h('div', { class: 'table-header' },
                    // Existing Headers with sorting
                    h('div', {
                        class: `header-cell ${sortBy === 'rank' ? 'active' : ''}`,
                        onClick: () => this.handleSort('rank')
                    }, 'Posición'),
                    h('div', {
                        class: `header-cell ${sortBy === 'IATA' ? 'active' : ''}`,
                        onClick: () => this.handleSort('IATA')
                    }, 'IATA'),
                    h('div', { // City sorting added
                        class: `header-cell ${sortBy === 'city' ? 'active' : ''}`,
                        onClick: () => this.handleSort('city')
                     }, 'Ciudad'),
                    h('div', {
                        class: `header-cell ${sortBy === 'destination_fit' ? 'active' : ''}`,
                        onClick: () => this.handleSort('destination_fit')
                    }, 'Destino'),
                    h('div', {
                        class: `header-cell ${sortBy === 'distance_fit' ? 'active' : ''}`,
                        onClick: () => this.handleSort('distance_fit')
                    }, 'Distancia'),
                    h('div', {
                        class: `header-cell ${sortBy === 'vibe_fit' ? 'active' : ''}`,
                        onClick: () => this.handleSort('vibe_fit')
                    }, 'Ambiente'),
                    // New Headers (no sorting added for these yet)
                    h('div', { class: 'header-cell' }, 'Latitud'),
                    h('div', { class: 'header-cell' }, 'Longitud')
                ),
                // Map over sorted results to create rows
                sortedResults.map(result =>
                    h('div', { class: 'table-row', key: result.IATA }, // Ensure IATA is unique
                        h('div', { class: 'row-cell' }, result.rank),
                        h('div', { class: 'row-cell' }, result.IATA),
                        h('div', { class: 'row-cell' }, result.city),
                        h('div', { class: 'row-cell' }, result.destination_fit),
                        h('div', { class: 'row-cell' }, result.distance_fit),
                        h('div', { class: 'row-cell' }, result.vibe_fit),
                        // New Cells for Lat/Long
                        h('div', { class: 'row-cell' }, formatCoordinate(result.lat)),
                        h('div', { class: 'row-cell' }, formatCoordinate(result.long))
                    )
                )
            )
        );
    }
}

// Ensure the target element exists in your HTML: <div id="app"></div>
render(h(FlightResultsApp), document.getElementById('app'));