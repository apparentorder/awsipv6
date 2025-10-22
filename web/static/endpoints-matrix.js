async function initSqliteFile() {
    if (this.endpointsSqliteDatabase) return; // already loaded

    document.getElementById('matrix-table-caption').textContent = 'Fetching EPDB ...';

    const [fetchResponse, SQL] = await Promise.all([
        fetch('endpoints.sqlite--but.cloudfront.does.not.want.to.compress.binary.data.so.lets.just.call.it.xml'),
        initSqlJs({ locateFile: file => `sql.js/${file}` }),
    ]);

    if (!fetchResponse.ok) {
        document.getElementById('matrix-table-caption').textContent = 'Could not load SQLite file.';
        return;
    }

    const dbFileContents = new Uint8Array(await fetchResponse.arrayBuffer());
    this.endpointsSqliteDatabase = new SQL.Database(dbFileContents);

    initRegions();
}

function setSelectedRegions(regionList) {
    try {
        if (!Array.isArray(regionList)) {
            regionList = JSON.parse(regionList);
        }
    } catch(_) {
        regionList = undefined
    }

    if (!regionList || !Array.isArray(regionList) || regionList.length === 0) {
        regionList = [
            'us-east-1', 'us-west-1',
            'ca-central-1',
            'eu-central-1',
            'cn-north-1',
            'us-gov-west-1',
            'eusc-de-east-1',
        ];
    }

    this.selectedRegions = [... new Set(regionList)];
    window.localStorage.setItem('regionSelection', JSON.stringify(this.selectedRegions));
}

function initRegions() {
    try {
        setSelectedRegions(JSON.parse(window.localStorage.getItem('regionSelection')));
    } catch(_) {
        setSelectedRegions(undefined);
    }

    const res = this.endpointsSqliteDatabase.exec(`
        SELECT region_name, partition_name, description
        FROM region
        ORDER BY region_name
    `);

    this.allRegions = {};
    for (const row of res[0].values) {
        const [regionName, partitionName, description] = row;
        const geoMatch = description.match(/\((.*)\)\s*$/);
        const shortDescription = geoMatch ? geoMatch[1] : description;
        this.allRegions[regionName] = { regionName, partitionName, description, shortDescription };
    }
}

function loadEndpointsTable() {
    document.getElementById('matrix-table-caption').textContent = 'Loading EPDB ...';

    const regionNamesOrdered = this.selectedRegions.toSorted();

    const serviceNamesOrdered = this.endpointsSqliteDatabase.exec(`
        SELECT DISTINCT service_name
        FROM endpoint
        ORDER BY service_name
    `)[0].values.map(r => r[0]);

    const stmt = this.endpointsSqliteDatabase.prepare(`
        SELECT
            service_name,
            region_name,
            endpoint_default_hostname,
            endpoint_default_has_ipv6,
            endpoint_default_has_ipv4,
            endpoint_dualstack_hostname,
            endpoint_dualstack_has_ipv6,
            endpoint_dualstack_has_ipv4
        FROM endpoint e
        WHERE e.service_name = ?
        AND e.region_name = ?
    `);

    // -----

    const headTr = document.createElement('tr');
    headTr.appendChild(document.createElement('th')).textContent = "Service";

    for (const regionName of regionNamesOrdered) {
        const region = this.allRegions[regionName];

        const th = headTr.appendChild(document.createElement('th'));
        const regionDiv = th.appendChild(document.createElement('div'));
        const descrDiv = th.appendChild(document.createElement('div'));
        regionDiv.textContent = region.regionName;
        descrDiv.textContent = region.shortDescription;
        descrDiv.classList.add("text-xs", "text-gray-500", "font-light");
    }

    const fragment = document.createDocumentFragment();
    for (const serviceName of serviceNamesOrdered) {
        const tr = fragment.appendChild(document.createElement('tr'));

        tr.appendChild(document.createElement('th')).textContent = serviceName;

        for (const regionName of regionNamesOrdered) {
            const row = stmt.getAsObject([serviceName, regionName]);
            const td = tr.insertCell(-1);
            const endpointClassDiv = td.appendChild(document.createElement('div'));
            const endpointClassSpan = endpointClassDiv.appendChild(document.createElement('span'));

            if (row.endpoint_default_has_ipv6) {
                td.classList.add('endpoint-ipv6');
                endpointClassSpan.textContent = 'IPv6';
            } else if (row.endpoint_dualstack_has_ipv6) {
                td.classList.add('endpoint-ipv6-dualstack');
                endpointClassSpan.textContent = 'opt-in';
            } else if (row.endpoint_default_has_ipv4 || row.endpoint_dualstack_has_ipv4) {
                td.classList.add('endpoint-ipv4');
                endpointClassSpan.textContent = 'IPv4';
            } else {
                td.classList.add('endpoint-nx');
                endpointClassSpan.textContent = '-';
            }

            // Those tooltips blow up and slow down the DOM massively.
            // Alternative: Have just one <div> for the tooltip, then position and fill it dynamically
            // on mouseover -- but then the fighting with JS starts again, instead of having nice clean
            // CSS for the tooltip.

            td.classList.add('tooltip-container');
            td.appendChild(createTooltipDivForRow(row));
        }
    }

    stmt.free();

    document.getElementById('matrix-table-head').replaceChildren(headTr);
    document.getElementById('matrix-table-body').replaceChildren(fragment);
    document.getElementById('matrix-table-caption').textContent = 'AWS Service APIs Public Endpoints';

    return;
}

function createTooltipDivForRow(row) {
    const tooltipDiv = document.createElement('div');
    tooltipDiv.classList.add('tooltip');

    const table = tooltipDiv.appendChild(document.createElement('table'));

    const caption = table.appendChild(document.createElement('caption'));
    caption.textContent = `${row.service_name} @ ${row.region_name}`;
    caption.classList.add("matrix-tooltip-head");

    const tbody = table.appendChild(document.createElement('tbody'));
    tbody.classList.add("matrix-tooltip-endpoints");

    // -----

    const trDefault = tbody.appendChild(document.createElement('tr'));

    const tdDefault = trDefault.appendChild(document.createElement('td'));
    tdDefault.textContent = "default";

    const tdDefaultHostname = trDefault.appendChild(document.createElement('td'));
    const codeDefaultHostname = tdDefaultHostname.appendChild(document.createElement('code'));
    codeDefaultHostname.textContent = row.endpoint_default_hostname;

    const tdDefaultExtra = trDefault.appendChild(document.createElement('td'));

    if (row.endpoint_default_has_ipv6 && row.endpoint_default_has_ipv4) {
        tdDefaultExtra.textContent = "IPv4, IPv6"
        codeDefaultHostname.classList.add("endpoint-ipv6");
    } else if (row.endpoint_default_has_ipv6) {
        tdDefaultExtra.textContent = "IPv6 ONLY"
        codeDefaultHostname.classList.add("endpoint-ipv6");
    } else if (row.endpoint_default_has_ipv4) {
        tdDefaultExtra.textContent = "IPv4"
        codeDefaultHostname.classList.add("endpoint-ipv4");
    } else {
        tdDefaultExtra.textContent = "-"
        codeDefaultHostname.classList.add("endpoint-nx");
    }

    // -----

    const trDualstack = tbody.appendChild(document.createElement('tr'));

    const tdDualstack = trDualstack.appendChild(document.createElement('td'));
    tdDualstack.textContent = "dualstack (opt-in)";

    const tdDualstackHostname = trDualstack.appendChild(document.createElement('td'));
    const codeDualstackHostname = tdDualstackHostname.appendChild(document.createElement('code'));
    codeDualstackHostname.textContent = row.endpoint_dualstack_hostname;

    const tdDualstackExtra = trDualstack.appendChild(document.createElement('td'));

    if (row.endpoint_dualstack_has_ipv6 && row.endpoint_dualstack_has_ipv4) {
        tdDualstackExtra.textContent = "IPv4, IPv6"
        codeDualstackHostname.classList.add("endpoint-ipv6-dualstack");
    } else if (row.endpoint_dualstack_has_ipv6) {
        tdDualstackExtra.textContent = "IPv6 ONLY"
        codeDualstackHostname.classList.add("endpoint-ipv6-dualstack");
    } else if (row.endpoint_dualstack_has_ipv4) {
        tdDualstackExtra.textContent = "IPv4 ONLY"
        codeDualstackHostname.classList.add("endpoint-ipv4");
    } else {
        tdDualstackExtra.textContent = "-"
        codeDualstackHostname.classList.add("endpoint-nx");
    }

    return tooltipDiv;
}

function populateRegionDropdown() {
    const dropdown = document.getElementById('region-dropdown');
    dropdown.innerHTML = '';

    for (const regionName in this.allRegions) {
        const region = this.allRegions[regionName];
        const label = document.createElement('label');
        label.className = 'block px-2 py-0 hover:bg-gray-100 cursor-pointer flex items-center text-sm whitespace-nowrap';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = regionName;
        console.log("XXX");
        console.log(regionName);
        console.log(JSON.stringify(this.selectedRegions, null, 4));
        checkbox.checked = this.selectedRegions.includes(regionName);
        checkbox.onchange = () => handleRegionChange();

        const span = document.createElement('span');
        span.textContent = `${region.regionName} (${region.shortDescription})`;
        span.className = 'px-1';

        label.appendChild(checkbox);
        label.appendChild(span);
        dropdown.appendChild(label);
    }

    // Add Select All / Clear All buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-between px-2 py-2 border-t sticky bottom-0 bg-white';

    const selectAllBtn = document.createElement('button');
    selectAllBtn.textContent = 'Select All (Bad Idea)';
    selectAllBtn.className = 'text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600';
    selectAllBtn.onclick = () => {
        const visibleLabels = dropdown.querySelectorAll('label:not([style*="display: none"])');
        visibleLabels.forEach(label => {
            const checkbox = label.querySelector('input[type="checkbox"]');
            if (checkbox) checkbox.checked = true;
        });
        handleRegionChange();
    };

    const resetBtn = document.createElement('button');
    resetBtn.textContent = 'Reset';
    resetBtn.className = 'text-xs bg-gray-500 text-white px-2 py-1 rounded hover:bg-gray-600';
    resetBtn.onclick = () => {
        // Reset to default region selection
        setSelectedRegions(null);
        loadEndpointsTable();
        populateRegionDropdown(); // Refresh checkboxes to show correct state
    };

    buttonContainer.appendChild(selectAllBtn);
    buttonContainer.appendChild(resetBtn);
    dropdown.appendChild(buttonContainer);
}

// Dropdown toggle now handled by HTMX inline event

function filterRegions() {
    const input = document.getElementById('region-search');
    const filter = input.value.toLowerCase();
    const labels = document.querySelectorAll('#region-dropdown label');

    // Show dropdown when typing
    document.getElementById('region-dropdown').classList.remove('hidden');

    labels.forEach(label => {
        const text = label.textContent.toLowerCase();
        label.style.display = text.includes(filter) ? '' : 'none';
    });
}

function handleRegionChange() {
    const checkboxes = document.querySelectorAll('#region-dropdown input[type="checkbox"]');
    const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
    setSelectedRegions(selected);
    loadEndpointsTable(); // Reload the table with new selection
    const input = document.getElementById('region-search');
    input.focus();
    input.select();
}

function filterServices(input) {
    const val = input.value.toLowerCase();
    const tbody = document.getElementById('matrix-table-body');

    for (const row of tbody.rows) {
        const matches = row.cells[0].textContent.toLowerCase().includes(val);
        row.style.display = matches ? '' : 'none';
    }
}

// Close dropdown when clicking outside or pressing Escape
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('region-dropdown');
    const input = document.getElementById('region-search');

    if (!input) return;

    if (!input.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
        input.value = '';
        document.querySelectorAll('#region-dropdown label').forEach(label => {
            label.style.display = '';
        });
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const activeElement = document.activeElement;
        const regionSearch = document.getElementById('region-search');

        // Only handle escape for the region search input
        if (activeElement === regionSearch) {
            document.getElementById('region-dropdown').classList.add('hidden');
            regionSearch.value = '';
        }
    }
});

initSqliteFile().then(() => {
    loadEndpointsTable();
    populateRegionDropdown();
});
