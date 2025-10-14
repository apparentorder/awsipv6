async function initSqliteFile() {
    console.log('Loading EPDB...');
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

    let headHtml = `
        <tr>
            <th>Service</th>
    `;
    regionNamesOrdered.forEach(regionName => headHtml += `<th>${regionName}</th>`);
    headHtml += `
        </tr>
    `;
    document.getElementById('matrix-table-head').innerHTML = headHtml;

    // -----

    const stmt = this.endpointsSqliteDatabase.prepare(`
        SELECT
            e.service_name,
            r.region_name,
            e.endpoint_default_hostname,
            e.endpoint_default_has_ipv4,
            e.endpoint_default_has_ipv4,
            e.endpoint_dualstack_hostname,
            e.endpoint_dualstack_has_ipv4,
            e.endpoint_dualstack_has_ipv4
        FROM region r
        LEFT JOIN endpoint e ON e.region_name = r.region_name
        WHERE r.selected = 1
        ORDER BY e.service_name, r.region_name
    `);

    let stepIsTrue = stmt.step();
    while (stepIsTrue) {
        const tr = document.getElementById('matrix-table-body').insertRow(-1);
        const row = stmt.getAsObject();
        tr.insertCell(-1).innerHTML = row.service_name;
        console.log(row.service_name);

        for (let i = 0; i < regionNamesOrdered.length; i++) {
            const row = stmt.getAsObject();
            stepIsTrue = stmt.step();

            tr.insertCell(-1).innerHTML = row.endpoint_default_hostname;
        }
    }
}

document.getElementById('filter').addEventListener('input', function() {
    const val = this.value.toLowerCase();
    const filtered = tableData.filter(row =>
        row.some(cell => String(cell).toLowerCase().includes(val))
    );
    renderTable(filtered);
});

if (!this.endpointsSqliteDatabase) {
    initSqliteFile().then(() => {
        initRegions();
        loadEndpointsTable();
    });
}
