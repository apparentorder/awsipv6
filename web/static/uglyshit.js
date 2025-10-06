
function filterRegions() {
    const filter = document.getElementById('region-search').value.toLowerCase();
    const checkboxLabels = document.getElementById('region-checkboxes').getElementsByTagName('label');
    for (const cl of checkboxLabels) {
        cl.style.display = cl.textContent.toLowerCase().includes(filter) ? '' : 'none';
    }
}

function removeEndpointClassFilter() {
    // ... but only if it was set by default and not by the user.
    const defaultInput = document.querySelector('input[name="filter-class"][checked="default"]');

    if (defaultInput) {
        // The "checked" *attribute* can be false (not checked) but the *attribute value*
        // could still be "default" after the user has selected another filter class option.
        if (defaultInput.checked) {
            document.getElementById('class-all').checked = true;
        }

        defaultInput.removeAttribute('checked');
    }
}

function filterData() {
    console.log("filterData");
    return;

    const regionCheckboxes = document.getElementsByName('regions');
    const selectedRegions = [];
    for (const rc of regionCheckboxes) {
        if (rc.checked) {
            selectedRegions.push(rc.value);
        }
    }

    const filterClass = document.querySelector('input[name="filter-class"]:checked').value;
    const filterText = document.getElementById('endpoint-search').value.toLowerCase();

    const table = document.getElementById('endpoints-table');
    const rows = table.getElementsByTagName('tr');
    for (let i = 1; i < rows.length; i++) { // skip header row
        const cells = rows[i].getElementsByTagName('td');
        const region = cells[1].textContent;
        const serviceName = cells[0].textContent.toLowerCase();
        const hostnameDefault = cells[3].textContent.toLowerCase();
        const hostnameDualstack = cells[7].textContent.toLowerCase();
        const hasIPv4Default = cells[4].textContent === 'yes';
        const hasIPv6Default = cells[5].textContent === 'yes';
        const hasIPv4Dualstack = cells[8].textContent === 'yes';
        const hasIPv6Dualstack = cells[9].textContent === 'yes';

        let matchesRegion = selectedRegions.length === 0 || selectedRegions.includes(region);
        let matchesClass = false;
        if (filterClass === 'all') {
            matchesClass = true;
        } else if (filterClass === 'ipv4-only') {
            matchesClass = (hasIPv4Default && !hasIPv6Default) || (hasIPv4Dualstack && !hasIPv6Dualstack);
        } else if (filterClass === 'ipv6-only') {
            matchesClass = (hasIPv6Default && !hasIPv4Default) || (hasIPv6Dualstack && !hasIPv4Dualstack);
        } else if (filterClass === 'dualstack') {
            matchesClass = hasIPv4Dualstack && hasIPv6Dualstack;
        } else if (filterClass === 'ipv6') {
            matchesClass = hasIPv6Default || hasIPv6Dualstack;
        }
    }
}

function setAllRegionsChecked(isChecked) {
    for (const i of document.getElementsByName('regions')) {
        i.checked = isChecked;
        i.dispatchEvent(new Event('change'));
    }
}
