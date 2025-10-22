- allow filtering on the Services page, too
  * a bit of effort to make the existing filter re-usable

- replace punk templating with e.g. `from string import Template`

- clean up: inconsistent use of stylesheet-defined classes vs.
  inline use of Tailwind classes

- accessibility: keyboard navigation, focus:ring, ARIA labels etc.

- data attributes as styling hooks, instead of adding classes
  directly in matrix JS

- event handling dropdowns etc: replace some JS with hx-*?

- matrix: virtual scrolling?
