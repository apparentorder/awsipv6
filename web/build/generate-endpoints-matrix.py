# Yes, this file could have been a static HTML file.

import os

html = f'''
    <!-- file: {os.path.basename(__file__)} -->

    <div id="everything" class="border-t dark:border-gray-600">
        <div id="filters-container" class="p-2 bg-gray-100 dark:bg-gray-800 border-b-2 dark:border-gray-600">
            <div id="filters-row" class="flex flex-wrap gap-4">
                <div class="relative">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        <input
                            id="services-filter"
                            type="search"
                            autofocus
                            pattern="[a-z0-9]*"
                            placeholder="Filter services..."
                            hx-on:input="filterServices(this)"
                            class="input-field dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
                        >
                    </label>
                </div>

                <div class="relative">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        <input
                            type="text"
                            id="region-search"
                            placeholder="Select regions..."
                            class="input-field dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
                            hx-on:input="filterRegions()"
                            hx-on:click="document.getElementById('region-dropdown').classList.remove('hidden')"
                        >
                    </label>
                    <div id="region-dropdown" class="absolute top-full left-0 w-full bg-white dark:bg-gray-800 border dark:border-gray-600 rounded shadow-md max-h-[70vh] overflow-y-auto hidden z-10">
                        <!-- js -->
                    </div>
                </div>
            </div> <!-- filters-row -->
        </div> <!-- filters-container -->

        <div id="main-content" class="p-4">
            <noscript>This requires JavaScript. Sorry, pal.</noscript>

            <div id="matrix-table-container"></div>
                <table id="matrix-table" class="data-table">
                    <caption id="matrix-table-caption" class="text-lg font-semibold">
                        <!-- js -->
                    </caption>
                    <thead id="matrix-table-head" class="border-b text-sm dark:border-gray-600">
                        <!-- js -->
                    </thead>

                    <tbody id="matrix-table-body" class="text-center font-light">
                        <!-- js -->
                    </tbody>
                </table>
            </div>
        </div> <!-- main-content -->
    </div> <!-- everything -->

    <script defer src="assets/sql.js/sql-wasm.js"></script>
    <script defer src="assets/endpoints-matrix.js"></script>
'''

open("web/zola/generated/endpoints-matrix.html", 'w').write(html)
