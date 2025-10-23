# Yes, this file could have been a static HTML file.

import os

html = f'''
    <!-- file: {os.path.basename(__file__)} -->

    <div id="everything" class="border-t">
        <div id="filters-container" class="p-2 bg-gray-100 border-b-2">
            <div id="filters-row" class="flex flex-wrap gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">
                        <input
                            id="services-filter"
                            type="search"
                            autofocus
                            pattern="[a-z0-9]*"
                            placeholder="Filter services..."
                            hx-on:input="filterServices(this)"
                            class="px-2 py-1 max-w-xs border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        >
                    </label>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-700">
                        <!-- <div class="relative mt-1"> -->
                            <input
                                type="text"
                                id="region-search"
                                placeholder="Select regions..."
                                class="w-80 px-2 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                hx-on:click="document.getElementById('region-dropdown').classList.remove('hidden')"
                                hx-on:input="filterRegions()"
                            >
                            <div id="region-dropdown" class="absolute top-full left-0 w-full bg-white border rounded shadow-md max-h-[70vh] overflow-y-auto hidden z-10">
                                <!-- js -->
                            </div>
                        <!-- </div> -->
                    </label>
                </div>
            </div> <!-- filters-row -->
        </div> <!-- filters-container -->

        <div id="main-content" class="p-4">
            <noscript>This requires JavaScript. Sorry, pal.</noscript>

            <div id="matrix-table-container"></div>
                <table id="matrix-table" class="text-center text-xs w-full table-auto whitespace-nowrap">
                    <caption id="matrix-table-caption" class="text-lg font-semibold">
                        <!-- js -->
                    </caption>
                    <thead id="matrix-table-head" class="border-b text-sm">
                        <!-- js -->
                    </thead>

                    <tbody id="matrix-table-body" class="text-center font-light">
                        <!-- js -->
                    </tbody>
                </table>
            </div>
        </div> <!-- main-content -->
    </div> <!-- everything -->

    <script defer src="sql.js/sql-wasm.js"></script>
    <script defer src="endpoints-matrix.js"></script>
'''

open("output/endpoints-matrix-main.html", 'w').write(html)
