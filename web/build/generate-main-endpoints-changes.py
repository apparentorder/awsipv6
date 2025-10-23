#!/usr/bin/env python3

import os
import re
import html

html_out = '''
    <h1>Recent changes in public API endpoints</h1>

    <div class="text-xs text-gray-500 font-light max-w-prose">
        This list is presented in <code>diff</code>-style output: Every
        endpoint beginning with a <code>+</code> was added, and every
        endpoint beginning with a <code>-</code> was removed &mdash; or
        changed, when paired with a <code>+</code> line.
    </div>

    <div>
'''

with open("output/changes") as f:
    data_tags_open = False
    date_count = 0
    for line in f.readlines():
        if re.match(r'^\d', line):
            if data_tags_open:
                html_out += '</ul>'
                data_tags_open = False

            # new date
            date_count += 1
            if date_count > 30:
                break

            html_out += f'<div id="changes-date-{line}" class="text-sm mt-3">{line}</div>'
            html_out += f'<ul id="changes-data-{line}" class="text-xs ml-3">'
            data_tags_open = True

        else:
            line = re.sub(r'^(.)', r'\1 ', line) # add space
            html_out += f'<li><code>{html.escape(line)}</code></li>'

html_out += '</ul>'
html_out += '</div>'


open("output/endpoints-changes-main.html", 'w').write(html_out)
