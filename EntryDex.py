import customtkinter as ctk
import json
import os
import re
from tkinter import messagebox, filedialog
from PIL import Image

# --- Backend Functions ---
DATA_FILE = 'bottles.json'


def load_data():
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
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def generate_id(data):
    if not data:
        return "BTL001"
    last_id = "BTL000"
    for item in data:
        if 'id' in item and item['id'].startswith("BTL") and item['id'][3:].isdigit():
            if item['id'] > last_id:
                last_id = item['id']
    try:
        current_num = int(last_id[3:])
    except ValueError:
        current_num = 0
    new_num = current_num + 1
    return f"BTL{new_num:03d}"


def find_bottle_by_id(bottle_id, bottles):
    for i, bottle in enumerate(bottles):
        if bottle.get('id') == bottle_id:
            return bottle, i
    return None, -1


# --- Main Application Class ---
class EntryDexApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EntryDex")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fields = [
            ("Name/Description:", "name"),
            ("Type/Category:", "type"),
            ("Color:", "color"),
            ("Era/Date Range:", "era"),
            ("Condition:", "condition"),
            ("Embossing/Markings (optional):", "embossing"),
            ("Closure Type (optional):", "closure_type"),
            ("Base Markings (optional):", "base_markings"),
            ("Location in Collection (optional):", "location")
        ]

        self.add_image_path = None
        self.edit_image_path = None
        self.placeholder_image = ctk.CTkImage(light_image=Image.new("RGB", (150, 150), "#E0E0E0"),
                                              dark_image=Image.new("RGB", (150, 150), "#2A2A2A"),
                                              size=(150, 150))

        # --- Sidebar Frame ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="EntryDex", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.add_button = ctk.CTkButton(self.sidebar_frame, text="Add Entry", command=self.show_add_frame)
        self.add_button.grid(row=1, column=0, padx=20, pady=10)

        self.view_button = ctk.CTkButton(self.sidebar_frame, text="View All", command=self.show_view_frame)
        self.view_button.grid(row=2, column=0, padx=20, pady=10)

        self.search_button = ctk.CTkButton(self.sidebar_frame, text="Search/Edit",
                                           command=self.show_search_edit_delete_frame)
        self.search_button.grid(row=3, column=0, padx=20, pady=10)

        self.reports_button = ctk.CTkButton(self.sidebar_frame, text="Reports", command=self.show_reports_frame)
        self.reports_button.grid(row=4, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

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

        self.show_frame("AddBottleFrame")

        self.bottles_data = load_data()
        if not os.path.exists(DATA_FILE):
            save_data([])

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
        frame = self.frames[frame_name]
        frame.grid(row=0, column=0, sticky="nsew")

    def _create_add_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["AddBottleFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)
        frame.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        scrollable_form_frame = ctk.CTkScrollableFrame(container, label_text="Enter New Entry Details")
        scrollable_form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        scrollable_form_frame.grid_columnconfigure(1, weight=1)

        self.entry_widgets = {}
        row_counter = 0
        for i, (label_text, key) in enumerate(self.fields):
            label = ctk.CTkLabel(scrollable_form_frame, text=label_text, anchor="w")
            label.grid(row=i, column=0, padx=(10, 5), pady=5, sticky="w")
            entry = ctk.CTkEntry(scrollable_form_frame)
            entry.grid(row=i, column=1, padx=(5, 10), pady=5, sticky="ew")
            self.entry_widgets[key] = entry
            row_counter = i

        row_counter += 1
        notes_label = ctk.CTkLabel(scrollable_form_frame, text="Notes/Comments (optional):", anchor="w")
        notes_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        self.notes_entry = ctk.CTkTextbox(scrollable_form_frame, height=80, wrap="word")
        self.notes_entry.grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        row_counter += 1
        addresses_label = ctk.CTkLabel(scrollable_form_frame, text="Related Addresses (optional):", anchor="w")
        addresses_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        self.add_addresses_entry = ctk.CTkTextbox(scrollable_form_frame, height=80, wrap="word")
        self.add_addresses_entry.grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        scrollable_form_frame.grid_rowconfigure(row_counter, weight=1)

        image_frame = ctk.CTkFrame(container)
        image_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        image_frame.grid_rowconfigure(0, weight=1)

        self.add_image_preview = ctk.CTkLabel(image_frame, text="", image=self.placeholder_image)
        self.add_image_preview.grid(row=0, column=0, padx=20, pady=20, sticky="n")

        select_image_button = ctk.CTkButton(image_frame, text="Select Image", command=self._select_add_image)
        select_image_button.grid(row=1, column=0, padx=20, pady=20, sticky="s")

        add_button_submit = ctk.CTkButton(frame, text="Add Entry to Collection", command=self._add_bottle_gui)
        add_button_submit.pack(pady=20)

    def _create_view_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["ViewAllFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        label = ctk.CTkLabel(frame, text="Full Collection", font=ctk.CTkFont(size=18, weight="bold"))
        label.grid(row=0, column=0, pady=(20, 10), padx=20)

        self.view_scrollable_frame = ctk.CTkScrollableFrame(frame)
        self.view_scrollable_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.view_scrollable_frame.grid_columnconfigure(0, weight=1)

        refresh_button = ctk.CTkButton(frame, text="Refresh List", command=lambda: self._view_all_bottles_gui())
        refresh_button.grid(row=2, column=0, pady=20)

    def _create_search_edit_delete_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["SearchEditDeleteFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        label = ctk.CTkLabel(frame, text="Search, Edit & Delete Entries", font=ctk.CTkFont(size=18, weight="bold"))
        label.grid(row=0, column=0, pady=20, columnspan=2)

        search_frame = ctk.CTkFrame(frame)
        search_frame.grid(row=1, column=0, pady=10, padx=20, sticky="ew", columnspan=2)
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Search Term:").grid(row=0, column=0, padx=(5, 0), pady=5, sticky="w")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Enter keyword or specific value")
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_type_combobox = ctk.CTkComboBox(search_frame, values=["Keyword", "Type", "Color", "Era"])
        self.search_type_combobox.set("Keyword")
        self.search_type_combobox.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkButton(search_frame, text="Search", command=self._search_bottles_gui).grid(row=0, column=3, padx=(0, 5),
                                                                                          pady=5)

        self.search_results_textbox = ctk.CTkTextbox(frame, wrap="word", height=100)
        self.search_results_textbox.grid(row=2, column=0, pady=10, padx=20, sticky="nsew", columnspan=2)

        edit_delete_control_frame = ctk.CTkFrame(frame)
        edit_delete_control_frame.grid(row=3, column=0, pady=10, padx=20, sticky="ew", columnspan=2)
        edit_delete_control_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(edit_delete_control_frame, text="Entry ID:").grid(row=0, column=0, padx=(5, 0), pady=5, sticky="w")
        self.id_entry_edit_delete = ctk.CTkEntry(edit_delete_control_frame, placeholder_text="Enter ID to Load/Delete")
        self.id_entry_edit_delete.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(edit_delete_control_frame, text="Load for Edit", command=self._load_bottle_for_edit).grid(row=0,
                                                                                                                column=2,
                                                                                                                padx=5,
                                                                                                                pady=5)
        ctk.CTkButton(edit_delete_control_frame, text="Delete Entry", command=self._delete_bottle_gui).grid(row=0,
                                                                                                            column=3,
                                                                                                            padx=(0, 5),
                                                                                                            pady=5)

        edit_container = ctk.CTkFrame(frame, fg_color="transparent")
        edit_container.grid(row=4, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)
        edit_container.grid_columnconfigure(0, weight=2)
        edit_container.grid_columnconfigure(1, weight=1)
        edit_container.grid_rowconfigure(0, weight=1)

        self.edit_fields_frame = ctk.CTkScrollableFrame(edit_container, label_text="Edit Entry Details")
        self.edit_fields_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.edit_fields_frame.grid_columnconfigure(1, weight=1)

        self.edit_entry_widgets = {}
        row_counter = 0
        for i, (label_text, key) in enumerate(self.fields):
            label = ctk.CTkLabel(self.edit_fields_frame, text=label_text, anchor="w")
            label.grid(row=i, column=0, padx=(10, 5), pady=5, sticky="w")
            entry = ctk.CTkEntry(self.edit_fields_frame)
            entry.grid(row=i, column=1, padx=(5, 10), pady=5, sticky="ew")
            self.edit_entry_widgets[key] = entry
            row_counter = i

        row_counter += 1
        edit_notes_label = ctk.CTkLabel(self.edit_fields_frame, text="Notes/Comments:", anchor="w")
        edit_notes_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        self.edit_notes_entry = ctk.CTkTextbox(self.edit_fields_frame, height=80, wrap="word")
        self.edit_notes_entry.grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        row_counter += 1
        edit_addresses_label = ctk.CTkLabel(self.edit_fields_frame, text="Related Addresses:", anchor="w")
        edit_addresses_label.grid(row=row_counter, column=0, padx=(10, 5), pady=5, sticky="nw")
        self.edit_addresses_entry = ctk.CTkTextbox(self.edit_fields_frame, height=80, wrap="word")
        self.edit_addresses_entry.grid(row=row_counter, column=1, padx=(5, 10), pady=5, sticky="nsew")

        self.edit_fields_frame.grid_rowconfigure(row_counter, weight=1)

        edit_image_frame = ctk.CTkFrame(edit_container)
        edit_image_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        edit_image_frame.grid_rowconfigure(0, weight=1)
        self.edit_image_preview = ctk.CTkLabel(edit_image_frame, text="", image=self.placeholder_image)
        self.edit_image_preview.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        select_edit_image_button = ctk.CTkButton(edit_image_frame, text="Change Image", command=self._select_edit_image)
        select_edit_image_button.grid(row=1, column=0, padx=20, pady=20, sticky="s")

        self.current_edit_bottle_id = None
        ctk.CTkButton(frame, text="Save Changes", command=self._edit_bottle_gui).grid(row=5, column=0, pady=10,
                                                                                      columnspan=2)

    def _create_reports_frame(self):
        frame = ctk.CTkFrame(self.main_content_frame, corner_radius=10)
        self.frames["ReportsFrame"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        label = ctk.CTkLabel(frame, text="Collection Reports", font=ctk.CTkFont(size=18, weight="bold"))
        label.grid(row=0, column=0, pady=20, sticky="w", padx=20)
        report_buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        report_buttons_frame.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        ctk.CTkButton(report_buttons_frame, text="Count by Type",
                      command=lambda: self._generate_report_gui("type")).pack(pady=5, fill="x")
        ctk.CTkButton(report_buttons_frame, text="Count by Color",
                      command=lambda: self._generate_report_gui("color")).pack(pady=5, fill="x")
        ctk.CTkButton(report_buttons_frame, text="List by Condition",
                      command=lambda: self._generate_report_gui("condition")).pack(pady=5, fill="x")
        ctk.CTkButton(report_buttons_frame, text="Entries by Era Range",
                      command=lambda: self._generate_report_gui("era_range")).pack(pady=5, fill="x")
        self.report_output_textbox = ctk.CTkTextbox(frame, wrap="word")
        self.report_output_textbox.grid(row=1, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)

    def _select_add_image(self):
        path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*"))
        )
        if path:
            self.add_image_path = path
            self._update_image_preview(self.add_image_preview, path, (150, 150))

    def _select_edit_image(self):
        path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=(("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*"))
        )
        if path:
            self.edit_image_path = path
            self._update_image_preview(self.edit_image_preview, path, (150, 150))

    def _update_image_preview(self, image_label, path, size):
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                image_label.configure(image=ctk_img)
            except Exception as e:
                print(f"Error loading image: {e}")
                image_label.configure(image=self.placeholder_image)
        else:
            image_label.configure(image=self.placeholder_image)

    def _add_bottle_gui(self):
        new_bottle = {"id": generate_id(self.bottles_data)}
        required_fields = ["name"]
        for key, entry_widget in self.entry_widgets.items():
            value = entry_widget.get().strip()
            if key in required_fields and not value:
                messagebox.showerror("Input Error", f"{key.replace('_', ' ').title()} is required!")
                return
            new_bottle[key] = value
        new_bottle["notes"] = self.notes_entry.get("1.0", "end-1c").strip()
        new_bottle["image_path"] = self.add_image_path
        new_bottle["related_addresses"] = self.add_addresses_entry.get("1.0", "end-1c").strip()
        self.bottles_data.append(new_bottle)
        save_data(self.bottles_data)
        messagebox.showinfo("Success", f"Entry '{new_bottle['name']}' (ID: {new_bottle['id']}) added successfully!")
        self._clear_add_form()

    def _clear_add_form(self):
        for entry_widget in self.entry_widgets.values():
            entry_widget.delete(0, 'end')
        self.notes_entry.delete("1.0", 'end')
        self.add_addresses_entry.delete("1.0", 'end')
        self.add_image_path = None
        self.add_image_preview.configure(image=self.placeholder_image)

    def _view_all_bottles_gui(self):
        for widget in self.view_scrollable_frame.winfo_children():
            widget.destroy()

        self.bottles_data = load_data()

        if not self.bottles_data:
            no_items_label = ctk.CTkLabel(self.view_scrollable_frame, text="No entries found in the collection.")
            no_items_label.pack(pady=20)
            return

        for i, bottle in enumerate(self.bottles_data):
            card = ctk.CTkFrame(self.view_scrollable_frame, border_width=1)
            card.pack(fill="x", expand=True, padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)

            img_label = ctk.CTkLabel(card, text="", image=self.placeholder_image)
            img_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
            self._update_image_preview(img_label, bottle.get("image_path"), (120, 120))

            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

            id_name_text = f"{bottle.get('id', 'N/A')} - {bottle.get('name', 'N/A')}"
            id_name_label = ctk.CTkLabel(details_frame, text=id_name_text, font=ctk.CTkFont(weight="bold"))
            id_name_label.pack(anchor="w")

            fields_to_display = [
                ("Type", "type"),
                ("Color", "color"),
                ("Condition", "condition"),
                ("Era", "era"),
                ("Embossing", "embossing"),
                ("Closure Type", "closure_type"),
                ("Base Markings", "base_markings"),
                ("Location", "location"),
            ]

            for label, key in fields_to_display:
                value = bottle.get(key, "").strip()
                if value:
                    field_label = ctk.CTkLabel(details_frame, text=f"{label}: {value}", wraplength=600, justify="left")
                    field_label.pack(anchor="w", pady=(2, 0))

            notes = bottle.get('notes', '').strip()
            if notes:
                notes_text = f"Notes: {notes}"
                notes_label = ctk.CTkLabel(details_frame, text=notes_text, wraplength=600, justify="left")
                notes_label.pack(anchor="w", pady=(5, 0))

            addresses = bottle.get('related_addresses', '').strip()
            if addresses:
                addresses_text = f"Addresses: {addresses}"
                addresses_label = ctk.CTkLabel(details_frame, text=addresses_text, wraplength=600, justify="left",
                                               font=ctk.CTkFont(slant="italic"))
                addresses_label.pack(anchor="w", pady=(5, 0))

    def _load_bottle_for_edit(self):
        bottle_id = self.id_entry_edit_delete.get().upper().strip()
        if not bottle_id:
            messagebox.showwarning("Input Error", "Please enter an Entry ID to load.")
            return
        bottle, index = find_bottle_by_id(bottle_id, self.bottles_data)
        if bottle:
            self.current_edit_bottle_id = bottle_id
            messagebox.showinfo("Entry Loaded", f"Entry '{bottle.get('name')}' loaded for editing.")

            for entry_widget in self.edit_entry_widgets.values(): entry_widget.delete(0, 'end')
            self.edit_notes_entry.delete("1.0", 'end')
            self.edit_addresses_entry.delete("1.0", 'end')

            for key, entry_widget in self.edit_entry_widgets.items():
                if key in bottle:
                    entry_widget.insert(0, bottle[key])
            if 'notes' in bottle:
                self.edit_notes_entry.insert("1.0", bottle['notes'])
            if 'related_addresses' in bottle:
                self.edit_addresses_entry.insert("1.0", bottle['related_addresses'])

            self.edit_image_path = bottle.get('image_path')
            self._update_image_preview(self.edit_image_preview, self.edit_image_path, (150, 150))
        else:
            messagebox.showerror("Not Found", f"Entry with ID '{bottle_id}' not found.")
            self.current_edit_bottle_id = None

    def _edit_bottle_gui(self):
        if not self.current_edit_bottle_id:
            messagebox.showwarning("No Entry Selected", "Please load an entry for editing first using its ID.")
            return
        bottle_id = self.current_edit_bottle_id
        bottle_to_edit, index = find_bottle_by_id(bottle_id, self.bottles_data)
        if bottle_to_edit:
            updated = False
            for key, entry_widget in self.edit_entry_widgets.items():
                new_value = entry_widget.get().strip()
                if bottle_to_edit.get(key) != new_value:
                    bottle_to_edit[key] = new_value
                    updated = True

            new_notes = self.edit_notes_entry.get("1.0", "end-1c").strip()
            if bottle_to_edit.get('notes') != new_notes:
                bottle_to_edit['notes'] = new_notes
                updated = True

            new_addresses = self.edit_addresses_entry.get("1.0", "end-1c").strip()
            if bottle_to_edit.get('related_addresses') != new_addresses:
                bottle_to_edit['related_addresses'] = new_addresses
                updated = True

            if bottle_to_edit.get('image_path') != self.edit_image_path:
                bottle_to_edit['image_path'] = self.edit_image_path
                updated = True

            if updated:
                self.bottles_data[index] = bottle_to_edit
                save_data(self.bottles_data)
                messagebox.showinfo("Success", f"Entry '{bottle_id}' updated successfully!")
                self.show_search_edit_delete_frame()
            else:
                messagebox.showinfo("No Changes", "No changes were made to the entry details.")
        else:
            messagebox.showerror("Error", "Entry to edit not found.")

    def _search_bottles_gui(self):
        self.bottles_data = load_data()
        self.search_results_textbox.delete("1.0", "end")
        query = self.search_entry.get().lower()
        search_type = self.search_type_combobox.get()
        results = []
        if search_type == "Keyword":
            for bottle in self.bottles_data:
                if any(query in str(value).lower() for key, value in bottle.items() if isinstance(value, str)):
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
                self.search_results_textbox.insert("end",
                                                   f"ID: {bottle.get('id')}, Name: {bottle.get('name')}, Type: {bottle.get('type')}\n")
        else:
            self.search_results_textbox.insert("end", f"No entries found matching '{query}'.")

    def _delete_bottle_gui(self):
        bottle_id = self.id_entry_edit_delete.get().upper().strip()
        if not bottle_id:
            messagebox.showwarning("Input Error", "Please enter an Entry ID to delete.")
            return
        bottle_to_delete, index = find_bottle_by_id(bottle_id, self.bottles_data)
        if bottle_to_delete:
            confirm = messagebox.askyesno("Confirm Delete",
                                          f"Are you sure you want to delete '{bottle_to_delete.get('name')}' (ID: {bottle_id})?")
            if confirm:
                del self.bottles_data[index]
                save_data(self.bottles_data)
                messagebox.showinfo("Success", f"Entry '{bottle_id}' deleted successfully!")
                self.show_search_edit_delete_frame()
            else:
                messagebox.showinfo("Cancelled", "Deletion cancelled.")
        else:
            messagebox.showerror("Not Found", f"Entry with ID '{bottle_id}' not found.")

    def _generate_report_gui(self, report_type):
        self.bottles_data = load_data()
        self.report_output_textbox.delete("1.0", "end")
        output_text = ""
        if not self.bottles_data:
            self.report_output_textbox.insert("end", "No entries to report on. Collection is empty.")
            return
        if report_type == "type":
            type_counts = {}
            for bottle in self.bottles_data:
                b_type = bottle.get('type', 'Unknown').title()
                type_counts[b_type] = type_counts.get(b_type, 0) + 1
            output_text += "--- Entries by Type ---\n"
            for b_type, count in sorted(type_counts.items()):
                output_text += f"{b_type}: {count}\n"
        elif report_type == "color":
            color_counts = {}
            for bottle in self.bottles_data:
                color = bottle.get('color', 'Unknown').title()
                color_counts[color] = color_counts.get(color, 0) + 1
            output_text += "--- Entries by Color ---\n"
            for color, count in sorted(color_counts.items()):
                output_text += f"{color}: {count}\n"
        elif report_type == "condition":
            condition_groups = {}
            for bottle in self.bottles_data:
                condition = bottle.get('condition', 'Unknown').title()
                if condition not in condition_groups:
                    condition_groups[condition] = []
                condition_groups[condition].append(bottle.get('name', 'Unnamed'))
            output_text += "--- Entries by Condition ---\n"
            for condition, names in sorted(condition_groups.items()):
                output_text += f"\n{condition}:\n"
                for name in names:
                    output_text += f"  - {name}\n"
        elif report_type == "era_range":
            start_year_input = ctk.CTkInputDialog(text="Enter start year (e.g., 1850):", title="Era Range").get_input()

            if start_year_input is None:
                self.report_output_textbox.insert("end", "Era range report cancelled.")
                return

            end_year_input = ctk.CTkInputDialog(text="Enter end year (e.g., 1870):", title="Era Range").get_input()

            if end_year_input is None:
                self.report_output_textbox.insert("end", "Era range report cancelled.")
                return

            if not start_year_input.strip() and not end_year_input.strip():
                output_text += "No years were entered."
            else:
                try:
                    start_year = int(start_year_input) if start_year_input.strip() else None
                    end_year = int(end_year_input) if end_year_input.strip() else None
                except ValueError:
                    output_text += "Invalid year input. Please enter numbers for years."
                    self.report_output_textbox.insert("end", output_text)
                    return

                era_results = []
                for bottle in self.bottles_data:
                    era_str = bottle.get('era', '')
                    if not era_str:
                        continue

                    years_in_era = re.findall(r'\d{4}', era_str)

                    bottle_within_range = False
                    for year_str in years_in_era:
                        try:
                            year = int(year_str)
                            if start_year is not None and year < start_year:
                                continue
                            if end_year is not None and year > end_year:
                                continue
                            bottle_within_range = True
                            break
                        except ValueError:
                            continue
                    if bottle_within_range:
                        era_results.append(bottle)

                if era_results:
                    start_display = start_year or 'Any'
                    end_display = end_year or 'Any'
                    output_text += f"--- Entries from Era Range {start_display} - {end_display} ---\n"
                    for bottle in era_results:
                        output_text += f"- {bottle.get('name')} (Era: {bottle.get('era')})\n"
                else:
                    output_text += "No entries found within the specified era range.\n"
        self.report_output_textbox.insert("end", output_text)

    def show_add_frame(self):
        self.show_frame("AddBottleFrame")
        self._clear_add_form()

    def show_view_frame(self):
        self.show_frame("ViewAllFrame")
        self._view_all_bottles_gui()

    def show_search_edit_delete_frame(self):
        self.show_frame("SearchEditDeleteFrame")
        self.search_results_textbox.delete("1.0", "end")
        self.id_entry_edit_delete.delete(0, 'end')
        self.current_edit_bottle_id = None
        self.edit_fields_frame.configure(label_text="Edit Entry Details")
        for entry_widget in self.edit_entry_widgets.values():
            entry_widget.delete(0, 'end')
        self.edit_notes_entry.delete("1.0", 'end')
        self.edit_addresses_entry.delete("1.0", 'end')
        self.edit_image_path = None
        self.edit_image_preview.configure(image=self.placeholder_image)

    def show_reports_frame(self):
        self.show_frame("ReportsFrame")
        self.report_output_textbox.delete("1.0", "end")


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = EntryDexApp()
    app.mainloop()
