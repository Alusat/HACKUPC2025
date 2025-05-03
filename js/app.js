// js/app.js

const { h, render, Component, createRef } = preact;

class FlightResultsApp extends Component {
    constructor() {
        super();
        this.state = {
            results: [],
            isLoading: true,
            error: null,
            sortBy: 'final_rank',
            sortOrder: 'asc'
        };
        this.mapInstance = null;
        this.markerGroup = null;
        this.mapContainerRef = createRef();
    }

    componentDidMount() {
        fetch('data/final_scored.json')
            .then(res => {
                if (!res.ok) throw new Error(res.statusText);
                return res.json();
            })
            .then(data => {
                if (!Array.isArray(data)) throw new Error('Data is not an array');
                this.setState({ results: data, isLoading: false });
            })
            .catch(err => {
                this.setState({ error: err.message, isLoading: false });
            });
    }

    componentDidUpdate(prevProps, prevState) {
        if (!this.state.isLoading && prevState.isLoading && !this.state.error) {
            this.initOrUpdateMap();
        }
    }

    componentWillUnmount() {
        if (this.mapInstance) {
            this.mapInstance.remove();
            this.mapInstance = null;
            this.markerGroup = null;
        }
    }

    initOrUpdateMap = () => {
        if (typeof L === 'undefined' || !this.mapContainerRef.current) return;
        const coords = this.state.results
            .filter(r => typeof r.lat === 'number' && typeof r.long === 'number')
            .map(r => [r.lat, r.long]);

        if (this.mapInstance) {
            this.markerGroup.clearLayers();
        } else {
            this.mapInstance = coords.length
                ? L.map(this.mapContainerRef.current).fitBounds(L.latLngBounds(coords), { padding: [30, 30] })
                : L.map(this.mapContainerRef.current).setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© OpenStreetMap'
            }).addTo(this.mapInstance);
            this.markerGroup = L.layerGroup().addTo(this.mapInstance);
        }

        if (coords.length) {
            this.state.results.forEach(r => {
                if (typeof r.lat === 'number') {
                    const marker = L.marker([r.lat, r.long])
                        .bindPopup(`<b>${r.city}</b><br>${r.iata}`);
                    r._marker = marker;
                    this.markerGroup.addLayer(marker);
                }
            });
            this.mapInstance.flyToBounds(L.latLngBounds(coords), { padding: [30, 30], duration: 0.5 });
        }
    }

    handleSort = col => {
        this.setState(prev => ({
            sortBy: col,
            sortOrder: prev.sortBy === col && prev.sortOrder === 'asc' ? 'desc' : 'asc'
        }));
    }

    handleRowClick = r => {
        if (this.mapInstance && r._marker) {
            this.mapInstance.flyTo([r.lat, r.long], 14, { duration: 0.8 });
            this.mapContainerRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
            setTimeout(() => r._marker.openPopup(), 300);
        }
    }

    render() {
        const { results, isLoading, error, sortBy, sortOrder } = this.state;
        if (isLoading) return h('div', {}, 'Cargando resultados...');
        if (error) return h('div', {}, `Error: ${error}`);

        const sorted = [...results].sort((a, b) => {
            const aVal = a[sortBy]; const bVal = b[sortBy];
            if (typeof aVal === 'number') return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
            return sortOrder === 'asc'
                ? String(aVal).localeCompare(bVal)
                : String(bVal).localeCompare(aVal);
        });

        const fmt = num => typeof num === 'number' ? num.toFixed(2) : '-';

        return h('div', { class: 'flight-results' },
            h('h1', {}, 'Resultados de Vuelos'),
            h('div', { class: 'results-table' },
                h('div', { class: 'table-header' },
                    ['final_rank','city','price_eur','vibe_fit','distance_fit','destination_fit'].map(col =>
                        h('div', {
                            class: `header-cell ${sortBy===col?'active':''}`,
                            onClick: () => this.handleSort(col)
                        }, col.replace(/_/g,' '))
                    )
                ),
                sorted.map(r => h('div', {
                    class: 'table-row', key: r.city, onClick: () => this.handleRowClick(r)
                }, [
                    r.final_rank, r.city, fmt(r.price_eur), r.vibe_fit, r.distance_fit, r.destination_fit
                ].map(val => h('div', { class: 'row-cell' }, val))))
            ),
            h('div', { id: 'mapid', ref: this.mapContainerRef })
        );
    }
}

render(h(FlightResultsApp), document.getElementById('app'));
