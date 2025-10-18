# Yes, this file could have been a static HTML file.

import os

html = f'''
    <!-- file: {os.path.basename(__file__)} -->

    <div id="everything" class="border-t">

        <div id="filters" class="p-2 bg-gray-100 border-b-2">
            <div class="flex flex-wrap gap-4">
                <div id="filter-services">
                    <label class="block text-sm font-medium text-gray-700">
                        <input
                            id="filter"
                            type="search"
                            autofocus
                            pattern="[a-z0-9]*"
                            placeholder="Filter services..."
                            oninput="filterServices(this)"
                            class="mt-1 px-2 py-1 max-w-xs border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        >
                    </label>
                </div>

                <div id="region-selection-items">
                    <label class="block text-sm font-medium text-gray-700">
                        <div class="relative mt-1">
                            <input type="text" id="region-search" placeholder="Select regions..." class="w-80 px-2 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" hx-on:click="document.getElementById('region-dropdown').classList.remove('hidden')" oninput="filterRegions()">
                            <div id="region-dropdown" class="absolute top-full left-0 w-full bg-white border rounded shadow-md max-h-[70vh] overflow-y-auto hidden z-10">
                                <!-- Region checkboxes will be populated by JavaScript -->
                            </div>
                        </div>
                    </label>
                </div>
            </div>
        </div>

        <div id="main-content" class="p-4">
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
