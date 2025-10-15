# Yes, this file could have been a static HTML file.

import os

html = f'''
    <!-- file: {os.path.basename(__file__)} -->

    <div id="everything" class="border-t flex">

        <div id="settings" class="text-sm p-2 w-64 flex-initial space-y-4 bg-gray-100 border-r-2">
            <div id="filter-services">
                <label>
                    <strong>Filter services:</strong>
                    <input
                        id="filter"
                        type="search"
                        autofocus
                        placeholder="Filter services..."
                        pattern="[a-z0-9]*"
                        oninput="filterServices(this)"
                        class="px-1 w-full box-border border-2 rounded"
                    >
                </label>
            </div>

            <div id="region-selection-items">
                <strong>Select regions:</strong>
                <div class="relative mt-2">
                    <input type="text" id="region-search" placeholder="Select regions..." class="w-full px-2 py-1 border rounded" onclick="toggleDropdown()" oninput="filterRegions()">
                    <div id="region-dropdown" class="absolute top-full left-0 w-full bg-white border rounded shadow-md max-h-96 overflow-y-auto hidden z-10">
                        <!-- Region checkboxes will be populated by JavaScript -->
                    </div>
                </div>
            </div>
        </div>

        <div id="main-content" class="p-2 flex-auto">
            <noscript>This requires JavaScript. Sorry, pal.</noscript>

            <div id="matrix-table-container"></div>
                <table id="matrix-table" class="text-center text-xs w-full table-auto whitespace-nowrap">
                    <caption id="matrix-table-caption" class="text-lg font-semibold"></caption>
                    <thead id="matrix-table-head" class="border-b text-sm">
                        <tr id="matrix-table-head-row">
                            <th>Service</th>
                        </tr>
                    </thead>

                    <tbody id="matrix-table-body" class="text-center font-light">
                    </tbody>
                </table>
            </div>
        </div> <!-- main-content -->
    </div> <!-- everything -->

    <script defer src="sql.js/sql-wasm.js"></script>
    <script defer src="endpoints-matrix.js"></script>
'''

open("output/endpoints-matrix-main.html", 'w').write(html)
