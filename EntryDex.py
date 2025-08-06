import customtkinter as ctk
import json
import os
import re
import shutil
from tkinter import messagebox, filedialog
from PIL import Image

# --- Backend Functions ---
DATA_FILE = 'bottles.json'
IMAGE_DIR = 'images'


def load_data():
    """Loads bottle data from the JSON file."""
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return []
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error",
                                 "Could not decode JSON. File might be corrupted or empty. Starting with empty data.")
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


# --- Main Application Class ---
class EntryDexApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.add_image_pil = None
        self.edit_image_pil = None
        self.current_edit_bottle_id = None

        self.title("EntryDex")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # --- Initial Setup ---
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Reusable field definitions
        self.fields = [
            ("Name/Description:", "name"), ("Type/Category:", "type"),
            ("Color:", "color"), ("Era/Date Range:", "era"),
            ("Condition:", "condition"), ("Embossing/Markings (optional):", "embossing"),
            ("Closure Type (optional):", "closure_type"),
            ("Finish Type (optional):", "finish_type"),
            ("Base Markings (optional):", "base_markings"),
            ("Location in Collection (optional):", "location")
        ]

        self.placeholder_image = ctk.CTkImage(light_image=Image.new("RGB", (200, 200), "#E0E0E0"),
                                              dark_image=Image.new("RGB", (200, 200), "#2A2A2A"),
                                              size=(200, 200))
        # --- Sidebar Frame ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="EntryDex", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0,
                                                                                                         column=0,
                                                                                                         padx=20,
                                                                                                         pady=20)
        ctk.CTkButton(self.sidebar_frame, text="Add Entry", command=self.show_add_frame).grid(row=1, column=0, padx=20,
                                                                                              pady=10)
        ctk.CTkButton(self.sidebar_frame, text="View All", command=self.show_view_frame).grid(row=2, column=0, padx=20,
                                                                                              pady=10)
        ctk.CTkButton(self.sidebar_frame, text="Search/Edit", command=self.show_search_edit_delete_frame).grid(row=3,
                                                                                                               column=0,
                                                                                                               padx=20,
                                                                                                               pady=10)
        ctk.CTkButton(self.sidebar_frame, text="Reports", command=self.show_reports_frame).grid(row=4, column=0,
                                                                                                padx=20, pady=10)

        ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w").grid(row=6, column=0, padx=20,
                                                                                   pady=(10, 0))
        ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode).grid(
            row=7, column=0, padx=20, pady=(10, 20))

        # --- Main Content Frame ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        self.main_content_frame.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self._create_add_frame()
        self._create_view_frame()
        self._create_search_edit_delete_frame()
        self._create_reports_frame()

        self.bottles_data = load_data()
        self.show_add_frame()

    # --- Frame Switching ---
    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
        frame = self.frames[frame_name]
        frame.grid(row=0, column=0, sticky="nsew")

    def show_add_frame(self):
        self.show_frame("AddBottleFrame")
        self._clear_add_form()

    def show_view_frame(self):
        self.show_frame("ViewAllFrame")
        self._view_all_bottles_gui()

    def show_search_edit_delete_frame(self):
        self.show_frame("SearchEditDeleteFrame")
        self._clear_search_edit_form()

    def show_reports_frame(self):
        self.show_frame("ReportsFrame")
        self.report_output_textbox.delete("1.0", "end")

    # --- Reusable Form Builder ---
    def _create_entry_form(self, parent):
        """Creates the labels, entries, and textboxes for a form."""
        widgets = {}
        parent.grid_columnconfigure(1, weight=1)

        row_counter = 0
        for i, (label_text, key) in enumerate(self.fields):
            label = ctk.CTkLabel(parent, text=label_text, anchor="w")
            label.grid(row=i, column=0, padx=(10, 5), pady=5, sticky="w")
            entry = ctk.CTkEntry(parent)
            entry.grid(row=i, column=1, padx=(5, 10), pady=5, sticky="ew")
            widgets[key] = entry
            row_counter = i

        row_counter += 1
        notes_label = ctk.CTkLabel(parent, text="Notes/Comments:", anchor="w")
        notes_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        widgets["notes"] = ctk.CTkTextbox(parent, height=100, wrap="word")
        widgets["notes"].grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        row_counter += 1
        addresses_label = ctk.CTkLabel(parent, text="Related Addresses:", anchor="w")
        addresses_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        widgets["addresses"] = ctk.CTkTextbox(parent, height=100, wrap="word")
        widgets["addresses"].grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        parent.grid_rowconfigure(row_counter, weight=1)
        return widgets

    # --- Frame Creation ---
    def _create_add_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["AddBottleFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        scrollable_form = ctk.CTkScrollableFrame(container, label_text="Enter New Entry Details")
        scrollable_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.add_widgets = self._create_entry_form(scrollable_form)

        image_frame = ctk.CTkFrame(container)
        image_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        self.add_image_preview = ctk.CTkLabel(image_frame, text="", image=self.placeholder_image)
        self.add_image_preview.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(image_frame, text="Select Image", command=lambda: self._select_image('add')).grid(row=1, column=0,
                                                                                                        padx=10, pady=5)
        ctk.CTkButton(image_frame, text="Rotate Image", command=lambda: self._rotate_image_preview('add')).grid(row=2,
                                                                                                                column=0,
                                                                                                                padx=10,
                                                                                                                pady=5)

        ctk.CTkButton(frame, text="Add Entry to Collection", command=self._add_bottle_gui).pack(pady=20)

    def _create_view_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["ViewAllFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Full Collection", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0,
                                                                                                   pady=(20, 10),
                                                                                                   padx=20)
        self.view_scrollable_frame = ctk.CTkScrollableFrame(frame)
        self.view_scrollable_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.view_scrollable_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(frame, text="Refresh List", command=self._view_all_bottles_gui).grid(row=2, column=0, pady=20)

    def _create_search_edit_delete_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["SearchEditDeleteFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)  # Row for results

        # Search bar
        search_bar_frame = ctk.CTkFrame(frame)
        search_bar_frame.grid(row=0, column=0, pady=10, padx=20, sticky="ew")
        search_bar_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_bar_frame, text="Search Term:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(search_bar_frame, placeholder_text="Enter keyword or specific value")
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_type_combobox = ctk.CTkComboBox(search_bar_frame, values=["Keyword", "Type", "Color", "Era"])
        self.search_type_combobox.set("Keyword")
        self.search_type_combobox.grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(search_bar_frame, text="Search", command=self._search_bottles_gui).grid(row=0, column=3, padx=5,
                                                                                              pady=5)

        # ID direct entry / delete
        id_bar_frame = ctk.CTkFrame(frame)
        id_bar_frame.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        id_bar_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(id_bar_frame, text="Entry ID:").grid(row=0, column=0, padx=5, pady=5)
        self.id_entry_delete = ctk.CTkEntry(id_bar_frame, placeholder_text="Enter ID to Delete")
        self.id_entry_delete.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(id_bar_frame, text="Delete by ID", command=self._delete_bottle_gui).grid(row=0, column=2, padx=5,
                                                                                               pady=5)

        # Search Results Frame
        self.search_results_frame = ctk.CTkScrollableFrame(frame, label_text="Search Results")
        self.search_results_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.search_results_frame.grid_columnconfigure(0, weight=1)

        # Edit Form
        edit_container = ctk.CTkFrame(frame, fg_color="transparent")
        edit_container.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        edit_container.grid_columnconfigure(0, weight=2)
        edit_container.grid_columnconfigure(1, weight=1)
        edit_container.grid_rowconfigure(0, weight=1)

        self.edit_fields_frame = ctk.CTkScrollableFrame(edit_container, label_text="Edit Entry Details")
        self.edit_fields_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.edit_widgets = self._create_entry_form(self.edit_fields_frame)

        edit_image_frame = ctk.CTkFrame(edit_container)
        edit_image_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        edit_image_frame.grid_rowconfigure(0, weight=1)
        edit_image_frame.grid_columnconfigure(0, weight=1)
        self.edit_image_preview = ctk.CTkLabel(edit_image_frame, text="", image=self.placeholder_image)
        self.edit_image_preview.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(edit_image_frame, text="Change Image", command=lambda: self._select_image('edit')).grid(row=1,
                                                                                                              column=0,
                                                                                                              padx=10,
                                                                                                              pady=5)
        ctk.CTkButton(edit_image_frame, text="Rotate Image", command=lambda: self._rotate_image_preview('edit')).grid(
            row=2, column=0, padx=10, pady=5)

        ctk.CTkButton(frame, text="Save Changes", command=self._edit_bottle_gui).grid(row=4, column=0, pady=(10, 20))

    def _create_reports_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["ReportsFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="Collection Reports", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0,
                                                                                                      pady=20,
                                                                                                      sticky="w",
                                                                                                      padx=20)
        report_buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        report_buttons_frame.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        ctk.CTkButton(report_buttons_frame, text="Count by Type",
                      command=lambda: self._generate_report_gui("type")).pack(pady=5, fill="x")
        ctk.CTkButton(report_buttons_frame, text="Count by Color",
                      command=lambda: self._generate_report_gui("color")).pack(pady=5, fill="x")
        ctk.CTkButton(report_buttons_frame, text="List by Condition",
                      command=lambda: self._generate_report_gui("condition")).pack(pady=5, fill="x")
        self.report_output_textbox = ctk.CTkTextbox(frame, wrap="word")
        self.report_output_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

    # --- Image Handling ---
    def _select_image(self, mode):
        path = filedialog.askopenfilename(title="Select an Image",
                                          filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")))
        if not path:
            return

        try:
            pil_image = Image.open(path)
            if mode == 'add':
                self.add_image_pil = pil_image
                self._update_image_preview(self.add_image_preview, self.add_image_pil)
            elif mode == 'edit':
                self.edit_image_pil = pil_image
                self._update_image_preview(self.edit_image_preview, self.edit_image_pil)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to open image file: {e}")

    def _update_image_preview(self, image_label, pil_image=None, path=None, size=(200, 200)):
        img_to_display = None
        if pil_image:
            img_to_display = pil_image
        elif path and os.path.exists(path):
            try:
                img_to_display = Image.open(path)
            except Exception as e:
                print(f"Error loading image from path {path}: {e}")

        if img_to_display:
            img_copy = img_to_display.copy()
            img_copy.thumbnail(size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
            image_label.configure(image=ctk_img)
        else:
            image_label.configure(image=self.placeholder_image)

    def _rotate_image_preview(self, mode):
        if mode == 'add' and self.add_image_pil:
            self.add_image_pil = self.add_image_pil.rotate(-90, expand=True)
            self._update_image_preview(self.add_image_preview, self.add_image_pil)
        elif mode == 'edit' and self.edit_image_pil:
            self.edit_image_pil = self.edit_image_pil.rotate(-90, expand=True)
            self._update_image_preview(self.edit_image_preview, self.edit_image_pil)

    def _save_image(self, pil_image, bottle_id):
        """Saves a PIL image to the designated image directory."""
        if not pil_image:
            return None
        try:
            destination_path = os.path.join(IMAGE_DIR, f"{bottle_id}.png")
            pil_image.save(destination_path, "PNG")
            return destination_path
        except Exception as e:
            messagebox.showerror("Image Save Error", f"Could not save image: {e}")
            return None

    # --- Core GUI Logic ---
    def _add_bottle_gui(self):
        new_bottle = {"id": generate_id(self.bottles_data)}

        for key, widget in self.add_widgets.items():
            if isinstance(widget, ctk.CTkEntry):
                new_bottle[key] = widget.get().strip()
            elif isinstance(widget, ctk.CTkTextbox):
                new_bottle[key] = widget.get("1.0", "end-1c").strip()

        if not new_bottle.get("name"):
            messagebox.showerror("Input Error", "Name/Description is a required field.")
            return

        new_bottle["image_path"] = self._save_image(self.add_image_pil, new_bottle["id"])
        self.bottles_data.append(new_bottle)
        save_data(self.bottles_data)
        messagebox.showinfo("Success", f"Entry '{new_bottle['name']}' (ID: {new_bottle['id']}) added successfully!")
        self._clear_add_form()

    def _edit_bottle_gui(self):
        if not self.current_edit_bottle_id:
            messagebox.showwarning("No Entry Loaded", "Please load an entry for editing first.")
            return

        bottle_to_edit, index = find_bottle_by_id(self.current_edit_bottle_id, self.bottles_data)
        if not bottle_to_edit:
            messagebox.showerror("Error", "Entry to edit not found.")
            return

        for key, widget in self.edit_widgets.items():
            if isinstance(widget, ctk.CTkEntry):
                bottle_to_edit[key] = widget.get().strip()
            elif isinstance(widget, ctk.CTkTextbox):
                bottle_to_edit[key] = widget.get("1.0", "end-1c").strip()

        bottle_to_edit["image_path"] = self._save_image(self.edit_image_pil, bottle_to_edit["id"])
        self.bottles_data[index] = bottle_to_edit
        save_data(self.bottles_data)
        messagebox.showinfo("Success", f"Entry '{self.current_edit_bottle_id}' updated successfully!")
        self._clear_search_edit_form()

    def _delete_bottle_gui(self):
        bottle_id = self.id_entry_delete.get().upper().strip()
        if not bottle_id:
            messagebox.showwarning("Input Error", "Please enter an Entry ID to delete.")
            return

        bottle_to_delete, index = find_bottle_by_id(bottle_id, self.bottles_data)
        if bottle_to_delete:
            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete '{bottle_to_delete.get('name')}' (ID: {bottle_id})?")
            if confirm:
                image_path = bottle_to_delete.get("image_path")
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)

                del self.bottles_data[index]
                save_data(self.bottles_data)
                messagebox.showinfo("Success", f"Entry '{bottle_id}' deleted successfully!")
                self._clear_search_edit_form()
        else:
            messagebox.showerror("Not Found", f"Entry with ID '{bottle_id}' not found.")

    def _load_bottle_for_edit(self, bottle_id):
        self._clear_search_edit_form()
        bottle, index = find_bottle_by_id(bottle_id, self.bottles_data)

        if bottle:
            self.current_edit_bottle_id = bottle_id
            self.edit_fields_frame.configure(label_text=f"Editing: {bottle.get('name', '')} ({bottle_id})")

            for key, widget in self.edit_widgets.items():
                value = bottle.get(key, "")
                if isinstance(widget, ctk.CTkEntry):
                    widget.insert(0, value)
                elif isinstance(widget, ctk.CTkTextbox):
                    widget.insert("1.0", value)

            image_path = bottle.get('image_path')
            if image_path and os.path.exists(image_path):
                self.edit_image_pil = Image.open(image_path)
                self._update_image_preview(self.edit_image_preview, pil_image=self.edit_image_pil)
            else:
                self.edit_image_pil = None
                self._update_image_preview(self.edit_image_preview)

            messagebox.showinfo("Loaded", f"Entry '{bottle_id}' is ready for editing.")
        else:
            messagebox.showerror("Not Found", f"Could not load Entry ID '{bottle_id}'.")

    def _search_bottles_gui(self):
        self.bottles_data = load_data()
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        query = self.search_entry.get().lower().strip()
        search_type = self.search_type_combobox.get()
        results = []

        if not query:
            results = self.bottles_data
        elif search_type == "Keyword":
            for bottle in self.bottles_data:
                if any(query in str(value).lower() for value in bottle.values()):
                    results.append(bottle)
        else:
            field_map = {"Type": "type", "Color": "color", "Era": "era"}
            field = field_map.get(search_type)
            if field:
                for bottle in self.bottles_data:
                    if query in bottle.get(field, '').lower():
                        results.append(bottle)

        if results:
            for bottle in results:
                bottle_id = bottle.get('id')
                display_text = f"{bottle_id}: {bottle.get('name', 'N/A')} ({bottle.get('type', 'N/A')})"
                btn = ctk.CTkButton(self.search_results_frame, text=display_text, anchor="w",
                                    command=lambda b_id=bottle_id: self._load_bottle_for_edit(b_id))
                btn.pack(fill="x", padx=5, pady=2)
        else:
            label = ctk.CTkLabel(self.search_results_frame, text=f"No entries found matching '{query}'.")
            label.pack(pady=10)

    def _view_all_bottles_gui(self):
        for widget in self.view_scrollable_frame.winfo_children():
            widget.destroy()
        self.bottles_data = load_data()
        if not self.bottles_data:
            ctk.CTkLabel(self.view_scrollable_frame, text="No entries found in the collection.").pack(pady=20)
            return

        for bottle in self.bottles_data:
            card = ctk.CTkFrame(self.view_scrollable_frame, border_width=1)
            card.pack(fill="x", expand=True, padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)

            img_label = ctk.CTkLabel(card, text="", image=self.placeholder_image)
            img_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="n")

            self._update_image_preview(img_label, path=bottle.get("image_path"), size=(250, 250))

            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

            id_name_text = f"{bottle.get('id', 'N/A')} - {bottle.get('name', 'N/A')}"
            ctk.CTkLabel(details_frame, text=id_name_text, font=ctk.CTkFont(weight="bold")).pack(anchor="w")

            for label, key in self.fields[1:] + [("Notes", "notes"), ("Addresses", "addresses")]:
                value = bottle.get(key, "").strip()
                if value:
                    label_text = label.replace(" (optional):", "")
                    ctk.CTkLabel(details_frame, text=f"{label_text}: {value}", wraplength=700, justify="left").pack(
                        anchor="w", pady=(2, 0))

    def _generate_report_gui(self, report_type):
        self.bottles_data = load_data()
        self.report_output_textbox.delete("1.0", "end")
        if not self.bottles_data:
            self.report_output_textbox.insert("end", "No entries to report on. Collection is empty.")
            return

        output_text = ""
        if report_type == "type":
            counts = {}
            for bottle in self.bottles_data:
                item = bottle.get('type', 'Unknown').title()
                counts[item] = counts.get(item, 0) + 1
            output_text += "--- Entries by Type ---\n"
            for item, count in sorted(counts.items()):
                output_text += f"{item}: {count}\n"
        elif report_type == "color":
            counts = {}
            for bottle in self.bottles_data:
                item = bottle.get('color', 'Unknown').title()
                counts[item] = counts.get(item, 0) + 1
            output_text += "--- Entries by Color ---\n"
            for item, count in sorted(counts.items()):
                output_text += f"{item}: {count}\n"
        elif report_type == "condition":
            groups = {}
            for bottle in self.bottles_data:
                item = bottle.get('condition', 'Unknown').title()
                if item not in groups:
                    groups[item] = []
                groups[item].append(bottle.get('name', 'Unnamed'))
            output_text += "--- Entries by Condition ---\n"
            for item, names in sorted(groups.items()):
                output_text += f"\n{item}:\n"
                for name in names:
                    output_text += f"  - {name}\n"

        self.report_output_textbox.insert("end", output_text)

    # --- Form Clearing ---
    def _clear_add_form(self):
        for widget in self.add_widgets.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", 'end')
        self.add_image_pil = None
        self.add_image_preview.configure(image=self.placeholder_image)

    def _clear_search_edit_form(self):
        self.id_entry_delete.delete(0, 'end')
        self.current_edit_bottle_id = None
        self.edit_fields_frame.configure(label_text="Edit Entry Details")

        for widget in self.edit_widgets.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, 'end')
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", 'end')
        self.edit_image_pil = None
        self.edit_image_preview.configure(image=self.placeholder_image)

        for widget in self.search_results_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EntryDexApp()
    app.mainloop()
