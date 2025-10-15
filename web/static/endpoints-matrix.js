async function initSqliteFile() {
    if (this.endpointsSqliteDatabase) return; // already loaded

    document.getElementById('matrix-table-caption').innerHTML = 'Loading EPDB ...';

    const [fetchResponse, SQL] = await Promise.all([
        fetch('endpoints.sqlite--but.cloudfront.does.not.want.to.compress.binary.data.so.lets.just.call.it.xml'),
        initSqlJs({ locateFile: file => `sql.js/${file}` }),
    ]);

    if (!fetchResponse.ok) {
        document.getElementById('matrix-table-caption').innerHTML = 'Could not load SQLite file.';
        return;
    }

    const dbFileContents = new Uint8Array(await fetchResponse.arrayBuffer());
    this.endpointsSqliteDatabase = new SQL.Database(dbFileContents);

    this.endpointsSqliteDatabase.run(`
        ALTER TABLE region
        ADD COLUMN selected INTEGER DEFAULT 0
    `);

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

    this.endpointsSqliteDatabase.run("UPDATE region SET selected = 0");
    for (const regionName of regionList) {
        this.endpointsSqliteDatabase.run("UPDATE region SET selected = 1 WHERE region_name = ?", [regionName]);
    }
}

function initRegions() {

    try {
        setSelectedRegions(JSON.parse(window.localStorage.getItem('regionSelection')));
    } catch(_) {
        setSelectedRegions(defaultRegionSelection);
    }

    const res = this.endpointsSqliteDatabase.exec(`
        SELECT region_name, partition_name, description
        FROM region
        ORDER BY region_name
    `);

    this.allRegions = {};
    for (const row of res[0].values) {
        const [regionName, partitionName, description] = row;
        this.allRegions[regionName] = { regionName, partitionName, description };
    }

    populateRegionDropdown();
}

function loadEndpointsTable() {
    // Clear existing table content
    const headTr = document.getElementById('matrix-table-head-row');
    while (headTr.children.length > 1) { // Keep the first 'Service' th
        headTr.removeChild(headTr.lastChild);
    }
    document.getElementById('matrix-table-body').innerHTML = '';

    const regionNamesOrdered = this.endpointsSqliteDatabase.exec(`
        SELECT region_name
        FROM region
        WHERE selected = 1
        ORDER BY region_name
    `)[0].values.map(r => r[0]);

    const serviceNamesOrdered = this.endpointsSqliteDatabase.exec(`
        SELECT DISTINCT service_name
        FROM endpoint
        ORDER BY service_name
    `)[0].values.map(r => r[0]);

    for (const regionName of regionNamesOrdered) {
        const th = headTr.appendChild(document.createElement('th'));
        th.innerHTML = regionName;
        th.classList.add('px-1');
    }

    // -----

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

    const fragment = document.createDocumentFragment();
    for (const serviceName of serviceNamesOrdered) {
        const tr = fragment.appendChild(document.createElement('tr'));
        const th = tr.appendChild(document.createElement('th'));
        th.innerHTML = serviceName;

        for (const regionName of regionNamesOrdered) {
            const row = stmt.getAsObject([serviceName, regionName]);
            const td = tr.insertCell(-1);

            if (row.endpoint_default_has_ipv6) {
                td.classList.add('endpoint-ipv6');
                td.innerHTML = 'IPv6';
            } else if (row.endpoint_dualstack_has_ipv6) {
                td.classList.add('endpoint-ipv6-dualstack');
                td.innerHTML = 'opt-in';
            } else if (row.endpoint_default_has_ipv4 || row.endpoint_dualstack_has_ipv4) {
                td.classList.add('endpoint-ipv4');
                td.innerHTML = 'IPv4';
            } else {
                td.classList.add('endpoint-nx');
                td.innerHTML = '-';
            }
        }
    }

    stmt.free();

    document.getElementById('matrix-table-body').appendChild(fragment);
    document.getElementById('matrix-table-caption').innerHTML = 'AWS Service APIs Public Endpoints';

    return;
}

function populateRegionDropdown() {
    const dropdown = document.getElementById('region-dropdown');
    dropdown.innerHTML = '';

    for (const regionName in this.allRegions) {
        const region = this.allRegions[regionName];
        const label = document.createElement('label');
        label.className = 'block px-2 py-0 hover:bg-gray-100 cursor-pointer flex items-center text-sm';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = regionName;
        checkbox.checked = this.selectedRegions.includes(regionName);
        checkbox.onchange = () => handleRegionChange();

        const span = document.createElement('span');
        const geoMatch = region.description.match(/\(.*\)\s*$/);
        span.textContent = geoMatch ? `${regionName} (${geoMatch[1]})` : regionName;
        span.className = 'px-1';

        label.appendChild(checkbox);
        label.appendChild(span);
        dropdown.appendChild(label);
    }

    // Add Select All / Clear All buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-between px-2 py-2 border-t sticky bottom-0 bg-white';

    const selectAllBtn = document.createElement('button');
    selectAllBtn.textContent = 'Select All';
    selectAllBtn.className = 'text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600';
    selectAllBtn.onclick = () => {
        const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = true);
        handleRegionChange();
    };

    const clearAllBtn = document.createElement('button');
    clearAllBtn.textContent = 'Clear / reset';
    clearAllBtn.className = 'text-xs bg-gray-500 text-white px-2 py-1 rounded hover:bg-gray-600';
    clearAllBtn.onclick = () => {
        const checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        handleRegionChange();
    };

    buttonContainer.appendChild(selectAllBtn);
    buttonContainer.appendChild(clearAllBtn);
    dropdown.appendChild(buttonContainer);
}

function toggleDropdown() {
    const dropdown = document.getElementById('region-dropdown');
    dropdown.classList.toggle('hidden');
}

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
    if (!input.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.getElementById('region-dropdown').classList.add('hidden');
        document.getElementById('region-search').value = '';
        filterRegions(); // Reset filter to show all regions
    }
});

initSqliteFile().then(() => {
    loadEndpointsTable();
});
