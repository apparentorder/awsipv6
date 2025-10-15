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
    if (!regionList) {
        throw new Error('regionList is null or undefined');
    }

    this.selectedRegions = [... new Set(regionList)];
    window.localStorage.setItem('regionSelection', JSON.stringify(this.selectedRegions));

    this.endpointsSqliteDatabase.run("UPDATE region SET selected = 0");
    for (const regionName of regionList) {
        this.endpointsSqliteDatabase.run("UPDATE region SET selected = 1 WHERE region_name = ?", [regionName]);
    }
}

function initRegions() {
    const defaultRegionSelection = [
        'us-east-1', 'us-west-1',
        'ca-central-1',
        'eu-central-1',
        'cn-north-1',
        'us-gov-west-1',
        'eusc-de-east-1',
    ];

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
}

function loadEndpointsTable() {
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

    const headTr = document.getElementById('matrix-table-head-row');
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

function filterServices(input) {
    const val = input.value.toLowerCase();
    const tbody = document.getElementById('matrix-table-body');

    for (const row of tbody.rows) {
        const matches = row.cells[0].textContent.toLowerCase().includes(val);
        row.style.display = matches ? '' : 'none';
    }
}

// document.getElementById('filter').addEventListener('input', function() {
//     const val = this.value.toLowerCase();
//     const tbody = document.getElementById('matrix-table-body');

//     for (const row of tbody.rows) {
//         const matches = row.cells[0].textContent.toLowerCase().includes(val);
//         row.style.display = matches ? '' : 'none';
//     }
// });

initSqliteFile().then(() => {
    loadEndpointsTable();
});
