
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

function setAllRegionsChecked(isChecked) {
    for (const i of document.getElementsByName('regions')) {
        i.checked = isChecked;
        i.dispatchEvent(new Event('change'));
    }
}
