import gi
import webbrowser 
import json 

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
FILE_NAME = "./sites.json"

with open(FILE_NAME, "r", encoding="utf-8") as f:
    SAMPLE_DATA = json.load(f)

class SiteButton(Gtk.Button):
    def __init__(self, site_name, site_url):
        super().__init__(label=site_name)
        self.site_url = site_url
        self.connect("clicked", self.on_click)

    def on_click(self, widget):
        print(f"Clicked: {self.get_label()}")
        print(f"Site: {self.site_url}")

        try:
            webbrowser.open(self.site_url)
            print("Link is open in your Browser.")
        except Exception as e:
            print(f"Cant Open Link : {e}")

class InfoBox(Gtk.Box):
    def __init__(self, site_name, site_url):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        button = SiteButton(site_name, site_url)
        self.append(button)


class MySiteBrowserApp(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="OFFNET")
        self.set_default_size(380, 600) 
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True) 
        scrolled_window.set_hexpand(True) 
        self.main_box.append(scrolled_window)
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(6)
        self.grid.set_row_spacing(6)
        self.grid.set_margin_top(12)
        self.grid.set_margin_bottom(12)
        self.grid.set_margin_start(12)
        self.grid.set_margin_end(12)
        scrolled_window.set_child(self.grid)
        self.populate_grid()

    def populate_grid(self):
        row = 0
        col = 0
        boxes_per_row = 2

        for i, data in enumerate(SAMPLE_DATA):

            site_name = data["site_name_en"]
            site_url = data["url"]
            info_box = InfoBox(site_name, site_url)
            self.grid.attach(info_box, col, row, 1, 1) 

            col += 1
            if col >= boxes_per_row:
                col = 0
                row += 1


class MyApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.example.sitebrowserapp')
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = MySiteBrowserApp(self)
        self.window.present()

app = MyApp()
exit_status = app.run(None)
exit(exit_status)
