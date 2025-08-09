import json
import os
import re
import shutil
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

# --- Constants ---
DATA_FILE = 'bottles.json'
IMAGE_DIR = 'images'


# --- Backend Functions ---

def load_data():
    """Loads bottle data from the JSON file."""
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return []
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
            # Backward compatibility for old single-image format
            for item in data:
                if 'image_path' in item and 'image_paths' not in item:
                    item['image_paths'] = [item['image_path']] if item['image_path'] else []
                    del item['image_path']
            return data
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Could not decode JSON. Starting with empty data.")
            return []


def save_data(data):
    """Saves bottle data to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_id(data):
    """Generates a new unique ID for a bottle."""
    if not data:
        return "BTL001"
    last_id_num = 0
    for item in data:
        if 'id' in item and item['id'].startswith("BTL") and item['id'][3:].isdigit():
            num = int(item['id'][3:])
            if num > last_id_num:
                last_id_num = num
    new_num = last_id_num + 1
    return f"BTL{new_num:03d}"


def find_bottle_by_id(bottle_id, bottles):
    """Finds a bottle and its index by its ID."""
    for i, bottle in enumerate(bottles):
        if bottle.get('id') == bottle_id:
            return bottle, i
    return None, -1


# --- Custom Widget for Viewing Entries ---

class EntryCard(ctk.CTkFrame):
    """A custom widget to display a single bottle entry with an image gallery."""

    def __init__(self, master, bottle_data, app_instance):
        super().__init__(master, border_width=1)
        self.bottle_data = bottle_data
        self.app = app_instance
        self.image_paths = self.bottle_data.get("image_paths", [])
        self.current_image_index = 0

        self.pack(fill="x", padx=20, pady=5)

        self.grid_columnconfigure(1, weight=1)

        # Image Frame with Gallery Controls
        self.image_gallery_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.image_gallery_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="n")

        self.img_label = ctk.CTkLabel(self.image_gallery_frame, text="", image=self.app.placeholder_image_small)
        self.img_label.pack()

        # Gallery Controls
        self.controls_frame = ctk.CTkFrame(self.image_gallery_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=5)

        self.prev_button = ctk.CTkButton(self.controls_frame, text="<", width=30, command=self.prev_image)
        self.image_counter_label = ctk.CTkLabel(self.controls_frame, text="")
        self.next_button = ctk.CTkButton(self.controls_frame, text=">", width=30, command=self.next_image)

        # Details Frame
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.details_frame.bind("<Configure>", self.on_details_frame_configure)
        self.details_frame.grid_columnconfigure(0, weight=1)

        self.create_details_widgets()
        self.update_image_display()

    def create_details_widgets(self):
        row = 0
        id_name_text = f"{self.bottle_data.get('id', 'N/A')} - {self.bottle_data.get('name', 'N/A')}"
        id_label = ctk.CTkLabel(self.details_frame, text=id_name_text, font=ctk.CTkFont(weight="bold"), justify="left",
                                anchor="w")
        id_label.grid(row=row, column=0, sticky="w", padx=5, pady=(0, 2))
        row += 1

        fields_to_display = self.app.fields[1:] + [("Related Addresses:", "addresses")]
        for label, key in fields_to_display:
            value = self.bottle_data.get(key, "").strip()
            if value:
                label_text = label
                detail_label = ctk.CTkLabel(
                    self.details_frame,
                    text=f"{label_text} {value}",
                    justify="left",
                    anchor="w",
                    wraplength=self.details_frame.winfo_width() - 20
                )
                detail_label.grid(row=row, column=0, sticky="we", padx=5, pady=(2, 0))
                row += 1

        links_text = self.bottle_data.get("links", "").strip()
        if links_text:
            links_header = ctk.CTkLabel(self.details_frame, text="Related Links:", justify="left", anchor="w")
            links_header.grid(row=row, column=0, sticky="w", padx=5, pady=(5, 0))
            row += 1
            for link in links_text.splitlines():
                if link.strip():
                    link_label = ctk.CTkLabel(
                        self.details_frame,
                        text=link.strip(),
                        text_color="#3399FF",
                        cursor="hand2",
                        font=ctk.CTkFont(underline=True),
                        justify="left",
                        anchor="w",
                        wraplength=self.details_frame.winfo_width() - 20
                    )
                    link_label.grid(row=row, column=0, sticky="w", padx=5)
                    link_label.bind("<Button-1>", lambda event, url=link.strip(): webbrowser.open(url))
                    row += 1

    def on_details_frame_configure(self, event):
        wrap_width = event.width - 20
        for widget in event.widget.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                widget.configure(wraplength=wrap_width)

    def update_image_display(self):
        if self.image_paths:
            self.app._update_image_preview(
                self.img_label, path=self.image_paths[self.current_image_index], size=(250, 250)
            )
            self.image_counter_label.configure(text=f"{self.current_image_index + 1} / {len(self.image_paths)}")
        else:
            self.img_label.configure(image=self.app.placeholder_image_small)
            self.image_counter_label.configure(text="0 / 0")
        self.update_controls_visibility()

    def update_controls_visibility(self):
        if len(self.image_paths) > 1:
            self.prev_button.grid(row=0, column=0, sticky="w", padx=5)
            self.image_counter_label.grid(row=0, column=1, sticky="ew", padx=5)
            self.next_button.grid(row=0, column=2, sticky="e", padx=5)
            self.controls_frame.grid_columnconfigure(1, weight=1)

            self.prev_button.configure(state="normal" if self.current_image_index > 0 else "disabled")
            self.next_button.configure(
                state="normal" if self.current_image_index < len(self.image_paths) - 1 else "disabled"
            )
        else:
            self.prev_button.grid_forget()
            self.image_counter_label.grid_forget()
            self.next_button.grid_forget()

    def prev_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_image_display()

    def next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.update_image_display()


# --- Main Application Class ---

class EntryDexApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EntryDex")

        # --- Center window ---
        window_width = 1200
        window_height = 800
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.minsize(1000, 700)

        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Data & State ---
        self.bottles_data = load_data()
        self.view_is_dirty = True
        self.current_edit_bottle_id = None
        self.add_images_pils = []
        self.add_image_index = 0
        self.edit_images_pils = []
        self.edit_image_index = 0

        # --- Field Definitions ---
        self.fields = [
            ("Name:", "name"), ("Type/Category:", "type"),
            ("Color:", "color"), ("Era/Date Range:", "era"),
            ("Condition:", "condition"), ("Embossing/Markings:", "embossing"),
            ("Closure Type:", "closure_type"), ("Finish Type:", "finish_type"),
            ("Base Markings:", "base_markings"), ("Location in Collection:", "location")
        ]

        # --- Image Placeholders ---
        self.placeholder_image = ctk.CTkImage(
            light_image=Image.new("RGB", (300, 300), "#E0E0E0"),
            dark_image=Image.new("RGB", (300, 300), "#2A2A2A"),
            size=(300, 300)
        )
        self.placeholder_image_small = ctk.CTkImage(
            light_image=Image.new("RGB", (250, 250), "#E0E0E0"),
            dark_image=Image.new("RGB", (250, 250), "#2A2A2A"),
            size=(250, 250)
        )

        # --- UI Construction ---
        self._create_sidebar()
        self._create_main_content_area()

        self.show_view_frame()

    def _create_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        sidebar_frame.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(sidebar_frame, text="EntryDex", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0,
                                                                                                    padx=20, pady=20)
        ctk.CTkButton(sidebar_frame, text="View All", command=self.show_view_frame).grid(row=1, column=0, padx=20,
                                                                                         pady=10)
        ctk.CTkButton(sidebar_frame, text="Add Entry", command=self.show_add_frame).grid(row=2, column=0, padx=20,
                                                                                         pady=10)
        ctk.CTkButton(sidebar_frame, text="Search/Edit", command=self.show_search_edit_delete_frame).grid(row=3,
                                                                                                          column=0,
                                                                                                          padx=20,
                                                                                                          pady=10)
        ctk.CTkButton(sidebar_frame, text="Reports", command=self.show_reports_frame).grid(row=4, column=0, padx=20,
                                                                                           pady=10)
        ctk.CTkLabel(sidebar_frame, text="Appearance Mode:", anchor="w").grid(row=6, column=0, padx=20, pady=(10, 0))
        ctk.CTkOptionMenu(sidebar_frame, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode).grid(
            row=7, column=0, padx=20, pady=(10, 20))

    def _create_main_content_area(self):
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for F in (AddBottleFrame, ViewAllFrame, SearchEditDeleteFrame, ReportsFrame):
            frame = F(self.main_content_frame, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

    def show_add_frame(self):
        self.show_frame("AddBottleFrame")
        self.frames["AddBottleFrame"].clear_form()

    def show_view_frame(self):
        if self.view_is_dirty:
            self.frames["ViewAllFrame"].refresh_view()
            self.view_is_dirty = False
        self.show_frame("ViewAllFrame")

    def show_search_edit_delete_frame(self):
        self.show_frame("SearchEditDeleteFrame")
        # Reset the editor area and buttons
        self.frames["SearchEditDeleteFrame"].clear_form()
        # Always refresh results (blank query => show all; otherwise keep the user’s last query)
        self.frames["SearchEditDeleteFrame"].refresh_results()

    def show_reports_frame(self):
        self.show_frame("ReportsFrame")
        self.frames["ReportsFrame"].generate_report("type")

    # --- Image Handling ---
    def _update_image_preview(self, image_label, pil_image=None, path=None, size=(300, 300)):
        img_to_display = None
        if pil_image is not None:
            img_to_display = pil_image
        elif path and os.path.exists(path):
            try:
                img_to_display = Image.open(path)
            except Exception as e:
                print(f"Error loading image from path {path}: {e}")

        if img_to_display:
            img_copy = img_to_display.copy()
            img_copy.thumbnail(size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy,
                                   size=(img_copy.width, img_copy.height))
            image_label.configure(image=ctk_img)
        else:
            w, h = size
            w = max(10, int(w))
            h = max(10, int(h))
            bg_light = "#E0E0E0"
            bg_dark = "#2A2A2A"
            ph_light = Image.new("RGB", (w, h), bg_light)
            ph_dark = Image.new("RGB", (w, h), bg_dark)
            ctk_img = ctk.CTkImage(light_image=ph_light, dark_image=ph_dark, size=(w, h))
            image_label.configure(image=ctk_img)

    def _save_images(self, pil_images, bottle_id):
        if not pil_images:
            return []
        saved_paths = []
        for i, pil_image in enumerate(pil_images):
            try:
                if pil_image.mode in ('RGBA', 'P'):
                    pil_image = pil_image.convert('RGB')
                destination_path = os.path.join(IMAGE_DIR, f"{bottle_id}_{i}.png")
                pil_image.save(destination_path, "PNG")
                saved_paths.append(destination_path)
            except Exception as e:
                messagebox.showerror("Image Save Error", f"Could not save image #{i + 1}: {e}")
        return saved_paths


# --- Frame Classes ---

class BaseFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=10)
        self.controller = controller


class AddBottleFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1, minsize=320)
        container.grid_rowconfigure(0, weight=1)

        self.scrollable_form = ctk.CTkScrollableFrame(container, label_text="Enter New Entry Details")
        self.scrollable_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.widgets = self._create_entry_form(self.scrollable_form)

        (self.image_preview, self.counter_label, self.prev_btn, self.next_btn) = self._create_image_editor(container)

        ctk.CTkButton(self, text="Add Entry to Collection", command=self._add_bottle_gui).pack(pady=20)

    def _create_entry_form(self, parent):
        widgets = {}
        parent.grid_columnconfigure(1, weight=1)
        for i, (label_text, key) in enumerate(self.controller.fields):
            label = ctk.CTkLabel(parent, text=label_text, anchor="w")
            label.grid(row=i, column=0, padx=(10, 5), pady=5, sticky="w")
            entry = ctk.CTkEntry(parent)
            entry.grid(row=i, column=1, padx=(5, 10), pady=5, sticky="ew")
            widgets[key] = entry
        row_counter = len(self.controller.fields)
        addresses_label = ctk.CTkLabel(parent, text="Related Addresses:", anchor="w")
        addresses_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        widgets["addresses"] = ctk.CTkTextbox(parent, height=40, wrap="word")
        widgets["addresses"].grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")
        row_counter += 1
        links_label = ctk.CTkLabel(parent, text="Related Links:", anchor="w")
        links_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        widgets["links"] = ctk.CTkTextbox(parent, height=80, wrap="word")
        widgets["links"].grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")
        parent.grid_rowconfigure(row_counter, weight=1)
        return widgets

    def _create_image_editor(self, parent):
        image_frame = ctk.CTkFrame(parent)
        image_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        image_frame.grid_rowconfigure(1, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        image_preview_label = ctk.CTkLabel(image_frame, text="", image=self.controller.placeholder_image)
        image_preview_label.grid(row=1, column=0, padx=10, pady=10)
        controls_frame = ctk.CTkFrame(image_frame)
        controls_frame.grid(row=2, column=0, pady=5)
        ctk.CTkButton(controls_frame, text="Add Image(s)", command=self._select_images).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Remove Current", command=self._remove_current_image).pack(side="left", padx=5)
        ctk.CTkButton(controls_frame, text="Rotate 90°", command=self._rotate_current_image).pack(side="left", padx=5)

        gallery_nav_frame = ctk.CTkFrame(image_frame, fg_color="transparent")
        gallery_nav_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        prev_button = ctk.CTkButton(gallery_nav_frame, text="<", width=30, command=lambda: self._navigate_images(-1))
        prev_button.pack(side="left")
        counter_label = ctk.CTkLabel(gallery_nav_frame, text="Image 0 / 0")
        counter_label.pack(side="left", expand=True)
        next_button = ctk.CTkButton(gallery_nav_frame, text=">", width=30, command=lambda: self._navigate_images(1))
        next_button.pack(side="right")
        return image_preview_label, counter_label, prev_button, next_button

    def _add_bottle_gui(self):
        new_bottle = {"id": generate_id(self.controller.bottles_data)}
        for key, widget in self.widgets.items():
            value = widget.get("1.0", "end-1c").strip() if isinstance(widget, ctk.CTkTextbox) else widget.get().strip()
            new_bottle[key] = value

        if not new_bottle.get("name"):
            messagebox.showerror("Input Error", "Name is required.")
            return

        new_bottle["image_paths"] = self.controller._save_images(self.controller.add_images_pils, new_bottle["id"])
        self.controller.bottles_data.append(new_bottle)
        save_data(self.controller.bottles_data)
        self.controller.view_is_dirty = True
        messagebox.showinfo("Success", f"Entry '{new_bottle['name']}' added successfully!")
        self.clear_form()

    def clear_form(self):
        for widget in self.widgets.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", 'end')
        self.controller.add_images_pils.clear()
        self.controller.add_image_index = 0
        self._update_image_editor_display()

    def _select_images(self):
        paths = filedialog.askopenfilenames(title="Select one or more images",
                                            filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp"),
                                                       ("All files", "*.*")))
        if not paths:
            return
        for path in paths:
            try:
                self.controller.add_images_pils.append(Image.open(path))
            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to open image file: {path}\n{e}")
        self._update_image_editor_display()

    def _remove_current_image(self):
        if self.controller.add_images_pils:
            self.controller.add_images_pils.pop(self.controller.add_image_index)
            if self.controller.add_image_index >= len(self.controller.add_images_pils):
                self.controller.add_image_index = max(0, len(self.controller.add_images_pils) - 1)
            self._update_image_editor_display()

    def _rotate_current_image(self):
        """Rotate the currently selected image 90° clockwise in Add view."""
        if not self.controller.add_images_pils:
            return
        i = self.controller.add_image_index
        try:
            img = self.controller.add_images_pils[i]
            self.controller.add_images_pils[i] = img.rotate(-90, expand=True)
            self._update_image_editor_display()
        except Exception as e:
            messagebox.showerror("Rotate Error", f"Could not rotate image: {e}")

    def _navigate_images(self, direction):
        new_index = self.controller.add_image_index + direction
        if 0 <= new_index < len(self.controller.add_images_pils):
            self.controller.add_image_index = new_index
            self._update_image_editor_display()

    def _update_image_editor_display(self):
        pils, index = self.controller.add_images_pils, self.controller.add_image_index
        if pils:
            self.controller._update_image_preview(self.image_preview, pil_image=pils[index])
            self.counter_label.configure(text=f"Image {index + 1} / {len(pils)}")
            self.prev_btn.configure(state="normal" if index > 0 else "disabled")
            self.next_btn.configure(state="normal" if index < len(pils) - 1 else "disabled")
        else:
            self.controller._update_image_preview(self.image_preview)
            self.counter_label.configure(text="Image 0 / 0")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")


class ViewAllFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Full Collection", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0,
                                                                                                  pady=(20, 10),
                                                                                                  padx=20)
        self.view_scrollable_frame = ctk.CTkScrollableFrame(self)
        self.view_scrollable_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.view_scrollable_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(self, text="Refresh List", command=self.refresh_view).grid(row=2, column=0, pady=20)

    def refresh_view(self):
        for widget in self.view_scrollable_frame.winfo_children():
            widget.destroy()

        if not self.controller.bottles_data:
            ctk.CTkLabel(self.view_scrollable_frame, text="No entries in the collection.").pack(pady=20)
            return

        for bottle in sorted(self.controller.bottles_data, key=lambda x: x.get('id')):
            EntryCard(self.view_scrollable_frame, bottle, self.controller)


class SearchEditDeleteFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- UI Elements ---
        # Search Bar
        search_bar_frame = ctk.CTkFrame(self)
        search_bar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        search_bar_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_bar_frame, text="Search Term:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(search_bar_frame, placeholder_text="Enter keyword, ID, name, color, etc.")
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<Return>", self._search_bottles_gui)
        ctk.CTkButton(search_bar_frame, text="Search", command=self._search_bottles_gui).grid(row=0, column=3, padx=5,
                                                                                              pady=5)

        # Search Results
        self.search_results_frame = ctk.CTkScrollableFrame(self, label_text="Search Results")
        self.search_results_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10, ipady=10)
        self.search_results_frame.grid_columnconfigure(0, weight=1)

        # Editor Container
        editor_container = ctk.CTkFrame(self, fg_color="transparent")
        editor_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        editor_container.grid_columnconfigure(0, weight=2)
        editor_container.grid_columnconfigure(1, weight=1, minsize=320)
        editor_container.grid_rowconfigure(0, weight=1)

        self.scrollable_form = ctk.CTkScrollableFrame(editor_container, label_text="Edit Entry Details")
        self.scrollable_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.widgets = self._create_entry_form(self.scrollable_form)

        (self.image_preview, self.counter_label, self.prev_btn, self.next_btn) = self._create_image_editor(
            editor_container)

        # Action Buttons
        self.action_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        self.action_button_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_button = ctk.CTkButton(self.action_button_frame, text="Save Changes", command=self._edit_bottle_gui)
        self.delete_button = ctk.CTkButton(self.action_button_frame, text="Delete Entry",
                                           command=self._delete_bottle_gui, fg_color="#D32F2F", hover_color="#B71C1C")

        self.clear_form()  # Initial state setup

    def refresh_results(self):
        """Repopulate the results list using whatever is currently in the search box.
        If blank, shows all entries."""
        self._search_bottles_gui()

    def _create_entry_form(self, parent):
        return AddBottleFrame._create_entry_form(self, parent)

    def _create_image_editor(self, parent):
        return AddBottleFrame._create_image_editor(self, parent)

    def _search_bottles_gui(self, event=None):
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        query = self.search_entry.get().lower().strip()
        results = []

        # Use in-memory data
        source_data = self.controller.bottles_data

        if not query:
            results = sorted(source_data, key=lambda x: x.get('id'))
        else:
            for bottle in source_data:
                is_match = any(query in str(value).lower() for value in bottle.values() if isinstance(value, str))
                if is_match:
                    results.append(bottle)
            results.sort(key=lambda x: x.get('id'))

        if results:
            for bottle in results:
                bottle_id = bottle.get('id')
                display_text = f"{bottle_id}: {bottle.get('name', 'N/A')} ({bottle.get('type', 'N/A')})"
                btn = ctk.CTkButton(self.search_results_frame, text=display_text, anchor="w",
                                    command=lambda b_id=bottle_id: self._load_bottle_for_edit(b_id))
                btn.pack(fill="x", padx=5, pady=2)
        else:
            ctk.CTkLabel(self.search_results_frame, text=f"No entries found matching '{query}'.").pack(pady=10)

    def _load_bottle_for_edit(self, bottle_id):
        self.clear_form()
        bottle, _ = find_bottle_by_id(bottle_id, self.controller.bottles_data)
        if bottle:
            self.controller.current_edit_bottle_id = bottle_id
            self.scrollable_form._label.configure(text=f"Editing: {bottle.get('name', '')} ({bottle_id})")
            for key, widget in self.widgets.items():
                value = bottle.get(key, "")
                if isinstance(widget, ctk.CTkTextbox):
                    widget.delete("1.0", "end")
                    widget.insert("1.0", value)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, value)
            self.controller.edit_images_pils.clear()
            for path in bottle.get('image_paths', []):
                if os.path.exists(path):
                    try:
                        self.controller.edit_images_pils.append(Image.open(path))
                    except Exception:
                        pass
            self.controller.edit_image_index = 0
            self._update_image_editor_display()
            # Show buttons
            self.save_button.grid(row=0, column=0, padx=5, pady=5)
            self.delete_button.grid(row=0, column=1, padx=5, pady=5)
        else:
            messagebox.showerror("Not Found", f"Could not load Entry ID '{bottle_id}'.")

    def _edit_bottle_gui(self):
        bottle_id = self.controller.current_edit_bottle_id
        if not bottle_id:
            messagebox.showwarning("No Entry Loaded", "Please search for and load an entry first.")
            return

        bottle_to_edit, index = find_bottle_by_id(bottle_id, self.controller.bottles_data)
        if not bottle_to_edit:
            messagebox.showerror("Error", "Entry to edit not found in database.")
            return

        for key, widget in self.widgets.items():
            value = widget.get("1.0", "end-1c").strip() if isinstance(widget, ctk.CTkTextbox) else widget.get().strip()
            bottle_to_edit[key] = value

        bottle_to_edit["image_paths"] = self.controller._save_images(self.controller.edit_images_pils,
                                                                     bottle_to_edit["id"])
        self.controller.bottles_data[index] = bottle_to_edit
        save_data(self.controller.bottles_data)
        self.controller.view_is_dirty = True
        messagebox.showinfo("Success", f"Entry '{bottle_id}' updated successfully!")
        self.clear_form()
        self._search_bottles_gui()

    def _delete_bottle_gui(self):
        bottle_id = self.controller.current_edit_bottle_id
        if not bottle_id:
            messagebox.showwarning("No Entry Loaded", "Please load an entry to delete.")
            return

        bottle_to_delete, index = find_bottle_by_id(bottle_id, self.controller.bottles_data)
        if bottle_to_delete:
            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to permanently delete '{bottle_to_delete.get('name')}' (ID: {bottle_id})?")
            if confirm:
                for path in bottle_to_delete.get("image_paths", []):
                    if os.path.exists(path):
                        os.remove(path)
                del self.controller.bottles_data[index]
                save_data(self.controller.bottles_data)
                self.controller.view_is_dirty = True
                messagebox.showinfo("Success", f"Entry '{bottle_id}' deleted successfully!")
                self.clear_form()
                self._search_bottles_gui()
        else:
            messagebox.showerror("Not Found", f"Entry with ID '{bottle_id}' not found.")

    def clear_form(self):
        self.controller.current_edit_bottle_id = None
        self.scrollable_form._label.configure(text="Edit Entry Details")
        for widget in self.widgets.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", 'end')

        self.controller.edit_images_pils.clear()
        self.controller.edit_image_index = 0
        self._update_image_editor_display()

        # Hide action buttons
        self.save_button.grid_forget()
        self.delete_button.grid_forget()

    def _select_images(self):
        paths = filedialog.askopenfilenames(title="Select one or more images",
                                            filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp"),
                                                       ("All files", "*.*")))
        if not paths:
            return
        for path in paths:
            try:
                self.controller.edit_images_pils.append(Image.open(path))
            except Exception as e:
                messagebox.showerror("Image Error", f"Failed to open image file: {path}\n{e}")
        self._update_image_editor_display()

    def _remove_current_image(self):
        if self.controller.edit_images_pils:
            self.controller.edit_images_pils.pop(self.controller.edit_image_index)
            if self.controller.edit_image_index >= len(self.controller.edit_images_pils):
                self.controller.edit_image_index = max(0, len(self.controller.edit_images_pils) - 1)
            self._update_image_editor_display()

    def _rotate_current_image(self):
        """Rotate the currently selected image 90° clockwise in Edit view."""
        if not self.controller.edit_images_pils:
            return
        i = self.controller.edit_image_index
        try:
            img = self.controller.edit_images_pils[i]
            self.controller.edit_images_pils[i] = img.rotate(-90, expand=True)
            self._update_image_editor_display()
        except Exception as e:
            messagebox.showerror("Rotate Error", f"Could not rotate image: {e}")

    def _navigate_images(self, direction):
        new_index = self.controller.edit_image_index + direction
        if 0 <= new_index < len(self.controller.edit_images_pils):
            self.controller.edit_image_index = new_index
            self._update_image_editor_display()

    def _update_image_editor_display(self):
        pils, index = self.controller.edit_images_pils, self.controller.edit_image_index
        if pils:
            self.controller._update_image_preview(self.image_preview, pil_image=pils[index])
            self.counter_label.configure(text=f"Image {index + 1} / {len(pils)}")
            self.prev_btn.configure(state="normal" if index > 0 else "disabled")
            self.next_btn.configure(state="normal" if index < len(pils) - 1 else "disabled")
        else:
            self.controller._update_image_preview(self.image_preview)
            self.counter_label.configure(text="Image 0 / 0")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")


class ReportsFrame(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, pady=20, padx=20, sticky="ew")

        ctk.CTkLabel(header_frame, text="Collection Reports", font=ctk.CTkFont(size=18, weight="bold")).pack(
            side="left")

        report_buttons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        report_buttons_frame.pack(side="right")
        ctk.CTkButton(report_buttons_frame, text="Count by Type", command=lambda: self.generate_report("type")).pack(
            side="left", padx=5)
        ctk.CTkButton(report_buttons_frame, text="Count by Color", command=lambda: self.generate_report("color")).pack(
            side="left", padx=5)
        ctk.CTkButton(report_buttons_frame, text="List by Condition",
                      command=lambda: self.generate_report("condition")).pack(side="left", padx=5)

        self.report_output_textbox = ctk.CTkTextbox(self, wrap="word")
        self.report_output_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

    def generate_report(self, report_type):
        self.report_output_textbox.delete("1.0", "end")
        if not self.controller.bottles_data:
            self.report_output_textbox.insert("end", "No entries to report on. Collection is empty.")
            return

        output_text = ""
        if report_type in ("type", "color"):
            counts = {}
            for bottle in self.controller.bottles_data:
                item = bottle.get(report_type, 'Unknown').strip().title()
                if not item:
                    item = 'Unknown'
                counts[item] = counts.get(item, 0) + 1
            output_text += f"--- Entries by {report_type.title()} ---\n\n"
            for item, count in sorted(counts.items()):
                output_text += f"{item}: {count}\n"
        elif report_type == "condition":
            groups = {}
            for bottle in self.controller.bottles_data:
                item = bottle.get('condition', 'Unknown').strip().title()
                if not item:
                    item = 'Unknown'
                if item not in groups:
                    groups[item] = []
                groups[item].append(f"{bottle.get('name', 'Unnamed')} (ID: {bottle.get('id')})")
            output_text += "--- Entries by Condition ---\n"
            for item, names in sorted(groups.items()):
                output_text += f"\n{item}:\n"
                for name in sorted(names):
                    output_text += f"  - {name}\n"

        self.report_output_textbox.insert("end", output_text)


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EntryDexApp()
    app.mainloop()
