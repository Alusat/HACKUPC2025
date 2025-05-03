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
        fetch('http://localhost:3000/data/prologoutput.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('No se pudo cargar los datos');
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
                // Fallback to local file if server request fails
                console.warn('Server fetch failed, trying local file:', error);
                
                // Try to load directly if using a proper local server like Python's http.server
                fetch('data/prologoutput.json')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('No se pudo cargar los datos locales');
                        }
                        return response.json();
                    })
                    .then(data => {
                        this.setState({
                            results: data,
                            isLoading: false
                        });
                    })
                    .catch(localError => {
                        this.setState({ 
                            error: `${error.message}. También falló localmente: ${localError.message}`,
                            isLoading: false 
                        });
                        console.error('Local fetch error:', localError);
                    });
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
                `Error: ${error}`
            );
        }

        if (results.length === 0) {
            return h('div', { class: 'status-message no-results' }, 'No hay resultados');
        }

        // Ordenar resultados
        const sortedResults = [...results].sort((a, b) => {
            if (sortBy === 'rank' || sortBy === 'score') {
                return sortOrder === 'asc' ? a[sortBy] - b[sortBy] : b[sortBy] - a[sortBy];
            }
            return sortOrder === 'asc' 
                ? String(a[sortBy]).localeCompare(String(b[sortBy]))
                : String(b[sortBy]).localeCompare(String(a[sortBy]));
        });

        return h('div', { class: 'flight-results' },
            h('h1', {}, 'Resultados de Vuelos'),
            h('div', { class: 'results-table' },
                h('div', { class: 'table-header' },
                    h('div', { 
                        class: `header-cell ${sortBy === 'rank' ? 'active' : ''}`,
                        onClick: () => this.handleSort('rank')
                    }, 'Posición'),
                    h('div', { 
                        class: `header-cell ${sortBy === 'IATA' ? 'active' : ''}`,
                        onClick: () => this.handleSort('IATA')
                    }, 'IATA'),
                    h('div', { class: 'header-cell' }, 'Ciudad'),
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
                    }, 'Ambiente')
                ),
                sortedResults.map(result => 
                    h('div', { class: 'table-row', key: result.IATA },
                        h('div', { class: 'row-cell' }, result.rank),
                        h('div', { class: 'row-cell' }, result.IATA),
                        h('div', { class: 'row-cell' }, result.city),
                        h('div', { class: 'row-cell' }, result.destination_fit),
                        h('div', { class: 'row-cell' }, result.distance_fit),
                        h('div', { class: 'row-cell' }, result.vibe_fit)
                    )
                )
            )
        );
    }
}

render(h(FlightResultsApp), document.getElementById('app'));