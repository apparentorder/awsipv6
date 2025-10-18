
// HTMX-based tooltip positioning and auto-hide
function positionTooltip(target) {
    const tooltip = document.getElementById('tooltip');
    if (!tooltip) return;

    const rect = target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;

    // Check if tooltip clips at bottom, if so position above
    const tooltipRect = tooltip.getBoundingClientRect();
    if (tooltipRect.bottom > window.innerHeight) {
        tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 5}px`;
    }
}

// Position tooltip after HTMX loads content
document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.target.id === 'tooltip') {
        // Find the currently hovered row
        const targetRow = document.querySelector('.progress-table-row:hover');
        if (targetRow) {
            positionTooltip(targetRow);
        }
        // Auto-hide after 10 seconds
        setTimeout(() => {
            document.getElementById('tooltip').classList.add('hidden');
        }, 10000);
    }
});

// Hide tooltip on mouse leave
document.addEventListener('mouseleave', function(e) {
    if (e.target.classList.contains('progress-table-row')) {
        document.getElementById('tooltip').classList.add('hidden');
    }
}, true);

// Hide tooltip on touch outside
document.addEventListener('touchstart', function(e) {
    if (!e.target.closest('.progress-table-row') && !e.target.closest('#tooltip')) {
        document.getElementById('tooltip').classList.add('hidden');
    }
});
