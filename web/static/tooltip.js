function tooltipMouseOver(element, event) {
    console.log(JSON.stringify({element}, null, 4));
    console.log(JSON.stringify({event}, null, 4));
    console.log(`t: ${event.target}`);
}

function tooltipMouseOut(element, event) {
    // console.log(JSON.stringify(element, null, 4));
}

function getTree(e) {
    let stack = [];

    while (e) {
        stack.push(e);
        e = e.parentElement;
    }

    return stack;
}

document.onmouseover = ((e) => {
    const td = e.target.closest('td');

    if (td) {
        console.log(`TDiH: ${td.innerHTML}`);
        if (td.innerHTML != "") {
            document.getElementById('tooltip').classList.remove("hidden");
            return;
        }
    }

    document.getElementById('tooltip').classList.add("hidden");
});
