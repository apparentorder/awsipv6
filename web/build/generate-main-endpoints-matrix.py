# Yes, this file could have been a static HTML file.

import os

html = f'''
    <!-- file: {os.path.basename(__file__)} -->

    <div id="everything" class="border-t flex">

        <div id="settings" class="text-sm p-2 w-64 flex-initial space-y-4 bg-gray-100 border-r-2">
            <strong>Filter services:</strong>
            <div id="filter-services">
                <input type="search" autofocus class="box-border w-full border-2 rounded" id="filter" pattern="[a-z0-9]*" oninput="updateSearch(this)">
            </div>

            <div id="region-selection-items">
                <strong>Select regions:</strong>
            </div>
        </div>

        <div id="main-content" class="p-2 flex-auto">
            <noscript>This requires JavaScript. Sorry, pal.</noscript>

            <div id="matrix-table-container"></div>
                <table id="matrix-table" class="text-center w-full table-auto">
                    <caption id="matrix-table-caption" class="font-semibold"></caption>
                    <thead id="matrix-table-head" class="border-b">
                        <tr>
                            <th>Service</th>
                        </tr>
                    </thead>

                    <tbody id="matrix-table-body" class="text-xs text-left font-light">
                    </tbody>
                </table>
            </div>
        </div> <!-- main-content -->
    </div> <!-- everything -->

    <script src="sql.js/sql-wasm.js"></script>
    <script src="endpoints-matrix.js"></script>
'''

open("output/endpoints-matrix-main.html", 'w').write(html)
