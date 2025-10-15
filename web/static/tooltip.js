
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

    // Check if tooltip clips at bottom, if so position above
    const tooltipRect = tooltipElement.getBoundingClientRect();
    if (tooltipRect.bottom > window.innerHeight) {
        tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 5}px`;
    }
}

// Event listeners for tooltips
document.addEventListener('mouseenter', function(e) {
    const tr = e.target.closest('.progress-table-row');
    if (!tr || !window.location.pathname.includes('services')) return;
    const isFirstCell = e.target.tagName === 'TD' && e.target === tr.querySelector('td:first-child');
    const isProgressBar = e.target.classList.contains('progress-bar') || e.target.closest('.progress-bar');
    if (isFirstCell || isProgressBar) {
        const serviceName = tr.querySelector('td').textContent.trim();
        showTooltip(tr, serviceName);

        if (this.serviceToolTipTimer) clearTimeout(this.serviceToolTipTimer);
        this.serviceToolTipTimer = setTimeout(hideTooltip, 10_000);
    }
}, true);

document.addEventListener('mouseleave', function(e) {
    if (e.target.classList.contains('progress-table-row')) {
        hideTooltip();
    }
}, true);

document.addEventListener('touchstart', function(e) {
    const tr = e.target.closest('.progress-table-row');
    if (!tr || !window.location.pathname.includes('services')) return;
    const isFirstCell = e.target.tagName === 'TD' && e.target === tr.querySelector('td:first-child');
    const isProgressBar = e.target.classList.contains('progress-bar') || e.target.closest('.progress-bar');
    if (isFirstCell || isProgressBar) {
        const serviceName = tr.querySelector('td').textContent.trim();
        showTooltip(tr, serviceName);

        if (this.serviceToolTipTimer) clearTimeout(this.serviceToolTipTimer);
        this.serviceToolTipTimer = setTimeout(hideTooltip, 10_000);
    }
}, true);

// Hide tooltip on any touch outside
document.addEventListener('touchstart', function(e) {
    if (!e.target.closest('.progress-table-row') && !e.target.closest('#tooltip')) {
        hideTooltip();
    }
});
