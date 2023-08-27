
function toggleV4Only(checkbox) {
    var ids = document.getElementsByClassName(`service-ipv4-only`);
    for (var i = 0; i < ids.length; i++) {
        ids[i].style.display = checkbox.checked ? "none" : "";
    }
}

function toggleRegion(checkbox, region) {
    var ids = document.getElementsByClassName(`data-region-${region}`);
    for (var i = 0; i < ids.length; i++) {
        ids[i].style.display = checkbox.checked ? "" : "none";
    }
}

function toggleRegionDropdown(div) {
      const dropdown = document.getElementById("region-selection-items");
      dropdown.style.display = dropdown.style.display == "none" ? "" : "none";
}

function updateSearch(textinput) {
    // using search will arbitrarily set/unset that rows are hidden, so we
    // effectively lose control over this setting. remove the filter.
    const cbox = document.getElementById("toggle-v4only")
    cbox.checked = false;
    
    for (const element of document.getElementsByClassName(`service-row`)) {
        const dt = Array.from(element.classList).find((e) => e.startsWith(`data-service-`));
        const service = dt.slice(`data-service-`.length);
        const should_display = textinput.value != "" ? service.includes(textinput.value) : true;

        element.style.display = should_display ? "" : "none";
    }
}

