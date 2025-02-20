# By u/JustBottleDiggin or @SpaceOrganism

import tkinter as tk
from tkinter import ttk, messagebox
import json
from typing import Dict, List
import os

class EntryCollectionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("EntryDex")
        self.root.geometry("800x600")

        # Load or initialize the data
        self.data_file = "entry_collection.json"
        self.entries = self.load_data()
        self.custom_attributes = set()
        self.update_custom_attributes()

        self.create_gui()

    def load_data(self) -> List[Dict]:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.entries, f, indent=2)

    def update_custom_attributes(self):
        for entry in self.entries:
            self.custom_attributes.update(entry.keys())
        # Remove standard attributes
        self.custom_attributes.discard('name')
        self.custom_attributes.discard('description')

    def create_gui(self):
        # Center the window
        self.root.update_idletasks() # Update window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")

        # Left panel - Entry list
        left_frame = ttk.Frame(self.root, padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_frame, text="Entry Collection").pack()

        # Create a frame for the listbox and scrollbar
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.entry_listbox = tk.Listbox(listbox_frame, width=60, height=20, yscrollcommand=scrollbar.set)
        self.entry_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.entry_listbox.yview)

        # Bind events for selection and hover
        self.entry_listbox.bind('<<ListboxSelect>>', self.on_select_entry)
        self.entry_listbox.bind('<Enter>', lambda e: self.bind_motion())
        self.entry_listbox.bind('<Leave>', lambda e: self.unbind_motion())

        # Create tooltip
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.withdraw()
        self.tooltip.overrideredirect(True)
        self.tooltip_label = ttk.Label(self.tooltip, background='lightyellow', relief='solid')
        self.tooltip_label.pack()

        # Right panel - Details and input
        right_frame = ttk.Frame(self.root, padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Input fields
        input_frame = ttk.LabelFrame(right_frame, text="Entry Details", padding="5")
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(input_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.desc_var).grid(row=1, column=1, sticky=tk.EW)

        # Custom attributes frame
        self.custom_frame = ttk.LabelFrame(right_frame, text="Custom Attributes", padding="5")
        self.custom_frame.pack(fill=tk.X, pady=5)

        # Custom attribute entries
        self.custom_entries = {}

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Entry", command=self.update_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Entry", command=self.delete_entry).pack(side=tk.LEFT, padx=5)

        # New attribute section
        attr_frame = ttk.Frame(right_frame)
        attr_frame.pack(fill=tk.X, pady=5)

        ttk.Label(attr_frame, text="Attribute:").pack(side=tk.LEFT)
        self.new_attr_var = tk.StringVar()
        ttk.Entry(attr_frame, textvariable=self.new_attr_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(attr_frame, text="Add Attribute", command=self.add_attribute).pack(side=tk.LEFT)

        ttk.Button(attr_frame, text="Delete Attribute", command=self.delete_attribute).pack(side=tk.LEFT, padx=5)

        # --- Add Clear Fields button ---
        ttk.Button(button_frame, text="Clear Fields", command=self.clear_inputs).pack(side=tk.LEFT, padx=5)

        self.refresh_entry_list()
        self.refresh_custom_attributes()



    def bind_motion(self):
        self.motion_id = self.entry_listbox.bind('<Motion>', self.on_hover)

    def unbind_motion(self):
        self.entry_listbox.unbind('<Motion>', self.motion_id)
        self.tooltip.withdraw()

    def on_hover(self, event):
        index = self.entry_listbox.nearest(event.y)
        if 0 <= index < len(self.entries):
            # Get the item's bbox
            bbox = self.entry_listbox.bbox(index)
            if bbox and event.y >= bbox[1] and event.y <= bbox[1] + bbox[3]:
                entry = self.entries[index]

                # Create tooltip text
                tooltip_text = f"Name: {entry['name']}\n"
                tooltip_text += f"Description: {entry.get('description', 'N/A')}\n"

                # Add custom attributes
                for attr in sorted(self.custom_attributes):
                    if attr in entry:
                        tooltip_text += f"{attr}: {entry[attr]}\n"

                self.tooltip_label.config(text=tooltip_text)

                # Position tooltip near cursor
                x = self.root.winfo_pointerx() + 15
                y = self.root.winfo_pointery() + 10
                self.tooltip.geometry(f"+{x}+{y}")
                self.tooltip.deiconify()
            else:
                self.tooltip.withdraw()
        else:
            self.tooltip.withdraw()

    def refresh_entry_list(self):
        self.entry_listbox.delete(0, tk.END)
        for entry in self.entries:
            self.entry_listbox.insert(tk.END, entry['name'])

    def refresh_custom_attributes(self):
        # Save current values
        current_values = {}
        for attr, var in self.custom_entries.items():
            current_values[attr] = var.get()

        # Clear existing entries
        for widget in self.custom_frame.winfo_children():
            widget.destroy()

        self.custom_entries.clear()

        # Recreate custom attribute entries
        for i, attr in enumerate(sorted(self.custom_attributes)):
            ttk.Label(self.custom_frame, text=f"{attr}:").grid(row=i, column=0, sticky=tk.W)
            var = tk.StringVar()
            # Restore previous value if it existed
            if attr in current_values:
                var.set(current_values[attr])
            self.custom_entries[attr] = var
            ttk.Entry(self.custom_frame, textvariable=var).grid(row=i, column=1, sticky=tk.EW)

    def add_attribute(self):
        new_attr = self.new_attr_var.get().strip()
        if new_attr and new_attr not in self.custom_attributes:
            self.custom_attributes.add(new_attr)
            self.refresh_custom_attributes()
            self.new_attr_var.set("")

    def delete_attribute(self):
        attr_to_delete = self.new_attr_var.get().strip()
        if not attr_to_delete:
            messagebox.showerror("Error", "Please enter an attribute to delete.")
            return

        if attr_to_delete not in self.custom_attributes:
            messagebox.showerror("Error", "Attribute not found.")
            return

        # Optional: Confirmation dialog
        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete '{attr_to_delete}'? This may affect existing entries."):
            try:
                # Remove the attribute from custom_attributes
                self.custom_attributes.remove(attr_to_delete)

                # Remove the attribute from all entries
                for entry in self.entries:
                    if attr_to_delete in entry:
                        del entry[attr_to_delete]

                # Refresh the GUI
                self.refresh_custom_attributes()
                self.save_data()
                self.new_attr_var.set("")  # Clear the input field
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting the attribute: {e}")

    def add_entry(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required!")
            return

        entry = {
            'name': name,
            'description': self.desc_var.get()
        }

        # Add custom attributes
        for attr, var in self.custom_entries.items():
            value = var.get()
            if value:
                entry[attr] = value

        self.entries.append(entry)
        self.save_data()
        self.refresh_entry_list()
        self.clear_inputs()

    def update_entry(self):
        selection = self.entry_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to update!")
            return

        index = selection
        entry = self.entries[index]

        entry['name'] = self.name_var.get()
        entry['description'] = self.desc_var.get()

        for attr, var in self.custom_entries.items():
            value = var.get()
            if value:
                entry[attr] = value
            elif attr in entry:
                del entry[attr]

        self.save_data()
        self.refresh_entry_list()
        self.clear_inputs()

    def delete_entry(self):
        selection = self.entry_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to delete!")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this entry?"):
            # Extract the index from the tuple
            index = selection[0]  # Get the first element of the tuple

            del self.entries[index]
            self.save_data()
            self.refresh_entry_list()
            self.clear_inputs()

    def on_select_entry(self, event):
        selection = self.entry_listbox.curselection()
        if not selection:
            return

        # Extract the index from the tuple
        index = selection[0]  # Get the first element of the tuple

        entry = self.entries[index]

        self.name_var.set(entry.get('name', ''))
        self.desc_var.set(entry.get('description', ''))

        # Fill custom attributes
        for attr, var in self.custom_entries.items():
            var.set(entry.get(attr, ''))

    def clear_inputs(self):
        self.name_var.set("")
        self.desc_var.set("")
        for var in self.custom_entries.values():
            var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    app = EntryCollectionManager(root)
    root.mainloop()
