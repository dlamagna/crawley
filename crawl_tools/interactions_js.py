scroll_and_next = """
"use strict";
window.scrollTo(0, document.body.scrollHeight);
await new Promise(r => setTimeout(r, 1000));
const btn = document.querySelector("a.pagination-next");
if (btn) {
  btn.click();
  return true;
}
return false;
"""

wait_for_new_page = """js:() => {
  // Example: wait until new items are visible
  const items = document.querySelectorAll('.exhibitor-item');
  // Or check a data attribute that changes on new page
  return items.length > 0;
}"""