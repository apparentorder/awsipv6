function tooltipMouseOver(element, event) {
    console.log(JSON.stringify({element}, null, 4));
    console.log(JSON.stringify({event}, null, 4));
    console.log(`t: ${event.target}`);
}

function tooltipMouseOut(element, event) {
    // console.log(JSON.stringify(element, null, 4));
}
