from datasette import hookimpl

JS = """
document.addEventListener('DOMContentLoaded', () => {
  // Only runs on .row or .table pages
  if (!document.body.classList.contains('row') && !document.body.classList.contains('table')) {
    return;
  }
  const isRowPage = document.body.classList.contains('row');
  const table = document.querySelector('table.rows-and-columns');
  if (!table) {
    return;
  }
  // Function to create and show the "Saved" message
  function showSavedMessage(cell) {
    let savedMessage = cell.querySelector('.saved-message');
    if (!savedMessage) {
      savedMessage = document.createElement('span');
      savedMessage.className = 'saved-message';
      savedMessage.textContent = 'updated';
      savedMessage.style.marginLeft = '5px';
      savedMessage.style.transition = 'opacity 0.5s ease-out';
      savedMessage.style.fontSize = '0.8em';
      cell.querySelector('label').appendChild(savedMessage);
    }
    savedMessage.style.display = 'inline';
    savedMessage.style.opacity = '1';

    setTimeout(() => {
      savedMessage.style.opacity = '0';
      setTimeout(() => {
        savedMessage.style.display = 'none';
      }, 500);
    }, 1000);
  }

  // Function to handle checkbox changes
  async function handleCheckboxChange(checkbox) {
    const cell = checkbox.closest('td');
    const isChecked = checkbox.checked ? 1 : 0;
    const row = cell.closest('tr');
    const pkCells = row.querySelectorAll('td.type-pk');
    const rowPks = Array.from(pkCells).map(pkCell => {
      let copy = pkCell.cloneNode(true)
      Array.from(copy.querySelectorAll('span')).forEach(
        span => span.parentNode.removeChild(span)
      );
      return copy.textContent;
    }).join(',');

    const currentPagePath = window.location.pathname
    const apiUrl = isRowPage ? `${currentPagePath}/-/update` : `${currentPagePath}/${rowPks}/-/update`;

    const toUpdate = {};
    // Figure out column name from associated <th> element
    const cellIndex = Array.from(cell.parentNode.children).indexOf(cell);
    const column = cell.closest('table').querySelectorAll('th')[cellIndex].dataset.column;
    toUpdate[column] = isChecked;

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          update: toUpdate
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      showSavedMessage(cell);
    } catch (error) {
      alert(`Error updating status: ${error.message}`);
    }
  }

  // Replace content of matching cells with checkboxes
  const prefixes = ["is_", "has_", "should_"];
  const types = ["type-int", "type-none"];
  const selector = prefixes.flatMap(prefix =>
    types.map(type => `td[class^="col-${prefix}"][class~="${type}"]`)
  ).join(',');
  const cells = table.querySelectorAll(selector);
  cells.forEach(cell => {
    if (cell.textContent === '0' || cell.textContent === '1' || cell.textContent.trim() === '') {
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = cell.textContent === '1';
      checkbox.className = 'status-checkbox';
      const label = document.createElement('label');
      label.style.display = 'block';
      label.style.width = '100%';
      label.style.height = '100%';
      label.style.cursor = 'pointer';
      cell.innerHTML = '';
      cell.appendChild(label);
      label.appendChild(checkbox);
    }
  });

  // Add a single event listener to the table
  table.addEventListener('change', (event) => {
    if (event.target.classList.contains('status-checkbox')) {
      handleCheckboxChange(event.target);
    }
  });
});
"""


@hookimpl
def extra_body_script(database, table, request, datasette):
    async def inner():
        # Does user have permission to update rows in this table?
        if table and await datasette.permission_allowed(
            request.actor, "update-row", resource=(database, table)
        ):
            return JS
        else:
            return ""

    return inner
