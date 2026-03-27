/**
 * Composable filter system (AND logic).
 */
const Filters = (() => {
    function apply(events, state) {
        let result = events;

        // Type filter
        if (state.type) {
            result = result.filter(e => e.type === state.type);
        }

        // Faction filter
        if (state.faction) {
            const ns = DataManager.getNamespaces();
            result = result.filter(e => {
                const nsMeta = ns[e.ns];
                return nsMeta && nsMeta.faction === state.faction;
            });
        }

        // Category filter
        if (state.category) {
            const ns = DataManager.getNamespaces();
            result = result.filter(e => {
                const nsMeta = ns[e.ns];
                return nsMeta && nsMeta.category === state.category;
            });
        }

        // Namespace filter
        if (state.namespace) {
            result = result.filter(e => e.ns === state.namespace);
        }

        // Hidden events
        if (!state.showHidden) {
            result = result.filter(e => !e.hide);
        }

        // Search
        if (state.search) {
            result = SearchEngine.search(state.search, result);
        }

        return result;
    }

    function populateDropdowns(events) {
        const ns = DataManager.getNamespaces();
        const factions = new Set();
        const categories = new Set();
        const namespaces = new Set();

        for (const nsMeta of Object.values(ns || {})) {
            factions.add(nsMeta.faction);
            categories.add(nsMeta.category);
            namespaces.add(nsMeta.name);
        }

        fillSelect('filter-faction', sorted(factions), 'All Factions');
        fillSelect('filter-category', sorted(categories), 'All Categories');
        fillSelect('filter-namespace', sorted(namespaces), 'All Namespaces');
    }

    function fillSelect(id, values, defaultLabel) {
        const el = document.getElementById(id);
        if (!el) return;
        const current = el.value;
        el.innerHTML = `<option value="">${defaultLabel}</option>`;
        for (const val of values) {
            const opt = document.createElement('option');
            opt.value = val;
            opt.textContent = val;
            el.appendChild(opt);
        }
        el.value = current;
    }

    function sorted(set) {
        return [...set].sort();
    }

    return { apply, populateDropdowns };
})();
