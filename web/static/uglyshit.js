
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

let tooltipElement = null;
let currentTooltipUrl = null;

function initTooltip() {
    tooltipElement = document.getElementById('tooltip');
}

function showTooltip(progressTableRow, serviceName) {
    if (!tooltipElement) initTooltip();

    const url = `endpoints-services-tooltip-${serviceName}.html`;
    if (currentTooltipUrl === url) {
        tooltipElement.classList.remove('hidden');
        positionTooltip(progressTableRow);
        return;
    }
    fetch(url)
        .then(response => response.text())
        .then(html => {
            tooltipElement.innerHTML = html;
            currentTooltipUrl = url;
            tooltipElement.classList.remove('hidden');
            positionTooltip(progressTableRow);
        })
        .catch(err => console.error('Failed to load tooltip:', err));
}

function hideTooltip() {
    if (tooltipElement) {
        tooltipElement.classList.add('hidden');
    }
}

function positionTooltip(target) {
    const rect = target.getBoundingClientRect();
    tooltipElement.style.left = `${rect.left + window.scrollX}px`;
    tooltipElement.style.top = `${rect.bottom + window.scrollY + 5}px`;
}

// Event listeners for tooltips
document.addEventListener('mouseenter', function(e) {
    if (e.target.classList.contains('progress-table-row')) {
        if (!window.location.pathname.includes('services')) return;
        const tr = e.target.closest('tr');
        const serviceName = tr.querySelector('td').textContent.trim();
        showTooltip(e.target, serviceName);
    }
}, true);

document.addEventListener('mouseleave', function(e) {
    if (e.target.classList.contains('progress-table-row')) {
        hideTooltip();
    }
}, true);

document.addEventListener('touchstart', function(e) {
    if (e.target.classList.contains('progress-table-row')) {
        if (!window.location.pathname.includes('services')) return;
        const tr = e.target.closest('tr');
        const serviceName = tr.querySelector('td').textContent.trim();
        showTooltip(e.target, serviceName);
        // Hide after 3 seconds or on next touch
        setTimeout(hideTooltip, 3000);
    }
}, true);

// Hide tooltip on any touch outside
document.addEventListener('touchstart', function(e) {
    if (!e.target.closest('.progress-table-row') && !e.target.closest('#tooltip')) {
        hideTooltip();
    }
});

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
