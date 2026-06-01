import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio
import json
import webbrowser
import os
import sys

# --- Constants ---
MAX_SEARCH_RESULTS = 54
DATA_FILE = './sites.json'
CLICK_COUNT_MULTIPLIER = 100

# --- Helper Functions ---
def load_site_data():
    # if not os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if 'click_count' not in item or not isinstance(item['click_count'], int):
                    item['click_count'] = 0
            return data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading data file {DATA_FILE}: {e}")
        return [] 

def save_site_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving data file {DATA_FILE}: {e}")

# --- Custom Widgets ---
class SearchResultButton(Gtk.Button):
    def __init__(self, site_data, app_window):
        super().__init__()
        self.site_data = site_data
        self.app_window = app_window 
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(hbox)
        name_label = Gtk.Label(label=f"{site_data.get('site_name_fa', '')} ({site_data.get('site_name_en', '')})")
        name_label.set_halign(Gtk.Align.CENTER)
        hbox.append(name_label)

        # Connect clicked signal to open URL and update click count
        self.connect('clicked', self.on_button_clicked)

    def on_button_clicked(self, widget):
        print(f"Button clicked for site: {self.site_data.get('site_name_en')}")
        self.app_window.update_click_count(self.site_data['id'])
        try:
            webbrowser.open(self.site_data['url'])
        except Exception as e:
            print(f"Error opening URL {self.site_data['url']}: {e}")

# --- Main Application Window ---
class SearchAppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("GTK 4 Advanced Search App")
        self.set_default_size(350, 600)
        self.set_resizable(True)

        self.all_sites_data = load_site_data()
        self.current_widgets_in_grid = [] 
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search sites (Name, Category, Keywords)...")
        self.search_entry.connect('search-changed', self.on_search_changed)

        # Scrollable area for search results
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Grid to hold the search results
        self.results_grid = Gtk.Grid()
        self.results_grid.set_column_spacing(6)
        self.results_grid.set_row_spacing(5)
        self.results_grid.set_margin_top(5)
        self.results_grid.set_margin_bottom(10)
        self.results_grid.set_margin_start(5)
        self.results_grid.set_margin_end(5)
        self.results_grid.set_column_homogeneous(True) # Make columns expand equally
        self.results_grid.set_row_homogeneous(False)  # Rows will size to content
        self.scrolled_window.set_child(self.results_grid)

        # Main vertical box layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(5)
        vbox.set_margin_bottom(5)
        vbox.set_margin_start(5)
        vbox.set_margin_end(5)
        vbox.append(self.search_entry)
        vbox.append(self.scrolled_window)
        self.set_child(vbox)

        self.perform_search("")



    def update_click_count(self, site_id):
        updated = False
        for site in self.all_sites_data:
            if site['id'] == site_id:
                site['click_count'] = site.get('click_count', 0) + 1
                updated = True
                break
        if updated:
            save_site_data(self.all_sites_data)
            self.perform_search(self.search_entry.get_text())

    def on_search_changed(self, widget):
        query = widget.get_text()
        self.perform_search(query)

    def clear_grid_children(self):
        # NEW METHOD: Remove widgets tracked in self.current_widgets_in_grid
        for widget in self.current_widgets_in_grid:
            self.results_grid.remove(widget)
        self.current_widgets_in_grid = [] # Clear the list

    def perform_search(self, query):
        if not self.all_sites_data:
            print("No site data loaded.")
            return

        query = query.lower().strip()
        search_terms = query.split()

        matched_sites = []

        for site in self.all_sites_data:
            score = 0
            matches_query = False

            # --- Scoring Logic ---
            # 1. Exact match in FA/EN name
            if query and (query in site.get('site_name_fa', '').lower() or \
                          query in site.get('site_name_en', '').lower()):
                score += 10 # High score for exact name match
                matches_query = True
            # 2. Partial match in FA/EN name
            elif query and (any(term in site.get('site_name_fa', '').lower() for term in search_terms) or \
                            any(term in site.get('site_name_en', '').lower() for term in search_terms)):
                score += 7
                matches_query = True

            # 3. Match in category
            if query and query in site.get('category', '').lower():
                score += 5
                matches_query = True
            elif query and any(term in site.get('category', '').lower() for term in search_terms):
                score += 3
                matches_query = True

            # 4. Match in keywords
            site_keywords = [kw.lower() for kw in site.get('keywords', [])]
            if query and any(kw for kw in site_keywords):
                score += 2
                matches_query = True
            elif query and any(any(term in kw for term in search_terms) for kw in site_keywords):
                score += 1
                matches_query = True

            # If no specific query term matched any field, but query is not empty, don't include
            if query and not matches_query:
                 continue # Skip this site if it doesn't match anything in the query

            # Calculate priority: Click count weighted heavily + score
            # If query is empty, we just sort by click count primarily
            if query:
                priority = site.get('click_count', 0) * CLICK_COUNT_MULTIPLIER + score
            else:
                priority = site.get('click_count', 0) * CLICK_COUNT_MULTIPLIER # For initial load, just sort by clicks

            matched_sites.append((priority, site))

        # Sort results: descending by priority, then ascending by ID for stability
        matched_sites.sort(key=lambda item: (-item[0], item[1]['id']))

        # --- Clear previous results using the new method ---
        self.clear_grid_children()

        # --- Display new results ---
        if not matched_sites and query:
            no_results_label = Gtk.Label(label="No results found.")
            no_results_label.set_halign(Gtk.Align.CENTER)
            no_results_label.set_valign(Gtk.Align.CENTER)
            self.results_grid.attach(no_results_label, 0, 0, 1, 1)
            self.current_widgets_in_grid.append(no_results_label) # Track the label widget
        else:
            # Determine grid layout based on available space, or fixed columns
            # For simplicity, let's use a fixed number of columns (e.g., 2)
            columns = 2
            row = 0
            col = 0
            for i, (priority, site_data) in enumerate(matched_sites):
                if i >= MAX_SEARCH_RESULTS:
                    break

                result_button = SearchResultButton(site_data, self)
                self.results_grid.attach(result_button, col, row, 1, 1)
                self.current_widgets_in_grid.append(result_button) # Track the button widget

                col += 1
                if col >= columns:
                    col = 0
                    row += 1

        # Ensure the grid is redrawn/refreshed if needed (often automatic with GTK 4 updates)
        self.results_grid.queue_resize()


# --- Application Class ---
class SearchApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='com.example.GtkSearchApp', **kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = SearchAppWindow(application=app)
        self.win.present()

# --- Main Execution ---
if __name__ == '__main__':
    app = SearchApp()
    app.run(sys.argv)
