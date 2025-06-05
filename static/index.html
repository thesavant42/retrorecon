<!-- File: templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>WABAX - Wayback Archive Explorer</title>
    <link rel="stylesheet" href="/static/wabax.css">

    <!-- Inline styles for your existing search/import UI -->
    <style>
        .search-bar input[type="text"] {
            width: 400px;
            font-size: 1.1em;
            padding: 0.3em;
        }
        .btn-wayback {
            display: inline-block;
            padding: 4px 8px;
            background-color: #f3f3f3;
            border: 1px solid #ccc;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
            font-size: 0.9em;
            width: fit-content;
        }
        .btn-wayback:hover {
            background-color: #e0e0e0;
            border-color: #999;
        }
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 1em;
        }
        .url-list li {
            display: flex;
            justify-content: space-between;
            padding: 0.5em 0;
            border-bottom: 1px solid #ddd;
        }
        .url-info {
            display: flex;
            flex-direction: column;
            gap: 5px;
            flex-grow: 1;
        }
        .url-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .url-actions {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }
        .import-container {
            position: relative;
            margin-left: auto;
        }
        .import-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            transform: translateX(-350px);
            z-index: 10;
            background: #fff;
            border: 1px solid #ccc;
            padding: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
            display: none;
            white-space: nowrap;
        }

        /* NEW: “Tools” dropdown styling */
        .dropdown {
            position: relative;
            display: inline-block;
        }
        .dropbtn {
            background-color: #f3f3f3;
            color: #333;
            padding: 4px 8px;
            font-size: 0.9em;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        }
        .dropbtn:hover {
            background-color: #e0e0e0;
        }
        .dropdown-content {
            display: none;
            position: absolute;
            background-color: #fff;
            min-width: 180px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
            z-index: 20;
        }
        .dropdown-content a {
            color: #333;
            padding: 8px 12px;
            text-decoration: none;
            display: block;
            font-size: 0.9em;
        }
        .dropdown-content a:hover {
            background-color: #e0e0e0;
        }
        .dropdown:hover .dropdown-content {
            display: block;
        }
    </style>

    <!-- NEW: Tiny JS function to toggle the hidden Exploder form -->
    <script>
        function toggleImportDropdown() {
            const dropdown = document.getElementById('import-dropdown');
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        }

        function toggleSelectAllMatching(checkbox) {
            document.querySelector('input[name="select_all_matching"]').value = checkbox.checked ? "true" : "false";
        }

        // NEW: This will be overridden by the inline script at the bottom to handle “Webpack Exploder”
        window.addEventListener('DOMContentLoaded', function() {
            // no-op here; real toggling is defined at bottom of body
        });
    </script>
</head>
<body>
<h1>🔎⏳📁 WABAX: Wayback Archive eXplorer 📁⏳🔎</h1>

<!-- ======= CONTROLS ROW ======= -->
<div class="controls">
    <!-- Search bar -->
    <div class="search-bar">
        <form method="GET" action="/">
            <input type="text" name="q" placeholder="Search..." value="{{ q }}">
            <button type="submit">Search</button>
        </form>
    </div>

    <!-- Import dropdown (existing) -->
    <div class="import-container">
        <button id="import-toggle-btn" onclick="toggleImportDropdown()">📥 Import</button>
        <div id="import-dropdown" class="import-dropdown">
            <form method="POST" action="/fetch_cdx">
                <label>🌐 Domain:
                    <input type="text" name="domain" placeholder="example.com" required>
                </label>
                <button type="submit">Fetch</button>
            </form>
            <form method="POST" action="/import_json" enctype="multipart/form-data">
                <label>📄 NDJSON:
                    <input type="file" name="json_file" required>
                </label>
                <button type="submit">Import</button>
            </form>
        </div>
    </div>

    <!-- NEW: Tools dropdown live next to “Import” -->
    <div class="dropdown">
      <button class="dropbtn">Tools ▾</button>
      <div class="dropdown-content">
        <a href="#" id="launch-webpack-exploder">Webpack Exploder</a>
      </div>
    </div>
</div>
<!-- ============================== -->



{% if urls %}
<form method="POST" action="/bulk_action">
    <div class="bulk-controls">
        <select name="action">
            <option value="add_tag" selected>Add Tag</option>
            <option value="remove_tag">Remove Tag</option>
            <option value="delete">Delete</option>
        </select>
        <input type="text" name="tag" placeholder="Tag">
        <button type="submit">Apply</button>
        <label>
            <input type="checkbox" onchange="toggleSelectAllMatching(this)">
            Select all matching
        </label>
        <input type="hidden" name="q" value="{{ q }}">
        <input type="hidden" name="domain" value="{{ domain }}">
        <input type="hidden" name="tag" value="{{ tag }}">
        <input type="hidden" name="select_all_matching" value="false">
    </div>

    <ul class="url-list">
        {% for url in urls %}
            <li>
                <div class="url-info">
                    <div class="url-row">
                        <input type="checkbox" name="selected_ids" value="{{ url.id }}">
                        {% if url.url %}
                            <a href="{{ url.url }}" target="_blank"><strong>{{ url.url }}</strong></a>
                        {% else %}
                            <strong style="color:red">⚠️ Invalid URL</strong>
                        {% endif %}
                    </div>
                    {% if url.tags %}<small>[{{ url.tags }}]</small>{% endif %}
                    {% if url.url %}
                        <a class="btn-wayback" href="https://web.archive.org/web/*/{{ url.url }}" target="_blank">⏳ Wayback</a>
                    {% endif %}
                </div>
            </li>
        {% endfor %}
    </ul>
</form>

<div class="pagination">
    {% if total_pages > 1 %}
        <div class="pagination-top">
            {% if page > 1 %}
                <a href="?page=1&q={{ q }}&domain={{ domain }}&tag={{ tag }}">⏮ First</a>
                <a href="?page={{ page - 1 }}&q={{ q }}&domain={{ domain }}&tag={{ tag }}">◀ Prev</a>
            {% endif %}

            {% for p in range(1 if page - 3 < 1 else page - 3, total_pages + 1 if page + 3 >= total_pages else page + 4) %}
                {% if p == page %}
                    <strong>[{{ p }}]</strong>
                {% else %}
                    <a href="?page={{ p }}&q={{ q }}&domain={{ domain }}&tag={{ tag }}">{{ p }}</a>
                {% endif %}
            {% endfor %}

            {% if page < total_pages %}
                <a href="?page={{ page + 1 }}&q={{ q }}&domain={{ domain }}&tag={{ tag }}">Next ▶</a>
                <a href="?page={{ total_pages }}&q={{ q }}&domain={{ domain }}&tag={{ tag }}">Last ⏭</a>
            {% endif %}
        </div>
        <br>
        <div class="pagination-bottom">
            <strong>Page {{ page }} of {{ total_pages }}</strong>
        </div>
    {% endif %}
</div>
{% else %}
<p>No results found.</p>
{% endif %}


<!-- ======= HIDDEN CONTAINER FOR WEBPACK EXPLODER ======= -->
<!--
     We include a partial template that has the “.js.map URL → Explode” form and its own <script> + <link> to tools.js/css.
     By default, this entire div is display:none; when the user clicks “Webpack Exploder,” we’ll flip it to display:block.
-->
<div id="webpack-exploder-container" style="display:none;">
  {% include "_webpack_exploder_form.html" %}
</div>
<!-- =================================================== -->


<!-- ======= INLINE SCRIPT TO TOGGLE THE EXPLODER FORM ======= -->
<script>
  document.getElementById('launch-webpack-exploder').addEventListener('click', function(e) {
    e.preventDefault();
    var container = document.getElementById('webpack-exploder-container');
    if (!container.style.display || container.style.display === 'none') {
      container.style.display = 'block';
      container.scrollIntoView({ behavior: 'smooth' });
    } else {
      container.style.display = 'none';
    }
  });
</script>
<!-- ========================================================= -->

</body>
</html>
