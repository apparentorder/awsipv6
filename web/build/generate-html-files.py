#!/usr/bin/env python3

page_list = [
    "egress",
    "ingress",
    "faq",
    "intro",
    "resources",
    "sdk-programming",
]

for page in page_list:
    html_out  = open("web/build/html-start", "r").read()
    html_out += open(f"web/build/{page}.html", "r").read()
    html_out += open("web/build/html-end", "r").read()

    open(f"output/{page}.html", 'w').write(html_out)
