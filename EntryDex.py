# By @SpaceOrganism or u/JustBottleDiggin
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Dict, List
import os
from PIL import Image, ImageTk


class EntryCollectionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("EntryDex")
        self.root.geometry("1150x600")
        self.data_file = "entry_collection.json" # Load or initialize the data
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
        self.root.update_idletasks()  # Update window size
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
        self.name_entry = tk.Text(input_frame, wrap=tk.WORD, height=1)  #
        self.name_entry.grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(input_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_var = tk.StringVar()
        self.desc_entry = tk.Text(input_frame, wrap=tk.WORD, height=2)  # Use Text widget for description
        self.desc_entry.grid(row=1, column=1, sticky=tk.EW)

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

        # Search bar
        search_frame = ttk.Frame(left_frame, padding="5")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.search_entries)  # Bind search function
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.refresh_entry_list()
        self.refresh_custom_attributes()

        # --- Image display area ---
        self.image_frame = ttk.LabelFrame(right_frame, text="Images", padding="5")
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.image_labels = []  # To store image labels for display

        # --- Image buttons ---
        image_button_frame = ttk.Frame(right_frame)
        image_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(image_button_frame, text="Upload Image", command=self.upload_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(image_button_frame, text="Delete Image", command=self.delete_image).pack(side=tk.LEFT, padx=5)

    def upload_image(self):
        selection = self.entry_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to upload an image for!")
            return

        index = selection[0]
        entry = self.entries[index]

        file_path = filedialog.askopenfilename(
            defaultextension=".png",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # Save the image to the project root folder
            image_name = os.path.basename(file_path)
            destination_path = os.path.join(os.getcwd(), image_name)  # Save to project root
            with Image.open(file_path) as img:
                img.save(destination_path)

            # Store the image path in the entry
            if 'images' not in entry:
                entry['images'] = []
            entry['images'].append(image_name)
            self.save_data()

            # Display the image
            self.display_images(entry)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload image: {e}")

    def delete_image(self):
        selection = self.entry_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry!")
            return

        index = selection[0]
        entry = self.entries[index]

        if 'images' not in entry or not entry['images']:
            messagebox.showinfo("Info", "No images to delete for this entry.")
            return

        # Ask the user to select an image to delete (you can modify this for multiple image selection)
        image_to_delete = filedialog.askopenfilename(
            initialdir=os.getcwd(),  # Start in the project root folder
            title="Select Image to Delete",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if not image_to_delete:
            return

        try:
            image_name = os.path.basename(image_to_delete)
            if image_name in entry['images']:
                # Remove the image from the entry
                entry['images'].remove(image_name)

                # Remove the 'images' attribute if the list is now empty
                if not entry['images']:
                    del entry['images']

                self.save_data()

                # Delete the image file
                os.remove(image_to_delete)

                # Refresh the image display
                self.display_images(entry)
            else:
                messagebox.showerror("Error", "Image not found in this entry.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete image: {e}")

    def display_images(self, entry):
        # Clear existing image labels
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        self.image_labels.clear()

        if 'images' in entry:
            for i, image_name in enumerate(entry['images']):
                try:
                    image_path = os.path.join(os.getcwd(), image_name)
                    img = Image.open(image_path)
                    img.thumbnail((100, 100))  # Resize image for display
                    photo = ImageTk.PhotoImage(img)

                    label = ttk.Label(self.image_frame, image=photo)
                    label.image = photo  # Keep a reference to avoid garbage collection
                    label.grid(row=i // 3, column=i % 3, padx=5, pady=5)  # Grid layout (3 images per row)
                    self.image_labels.append(label)

                    # --- Bind click event to open popup ---
                    label.bind("<Button-1>", lambda e, path=image_path: self.open_popup(path))

                except Exception as e:
                    print(f"Failed to load image {image_name}: {e}")

    def open_popup(self, image_path):
        # Create a new Toplevel window for the popup
        popup = tk.Toplevel(self.root)
        popup.title("Zoomable Image")

        # Load and display the image in the popup
        self.zoom_factor = 1.0  # Initialize zoom factor
        self.current_image = Image.open(image_path)  # Store the original image
        photo = ImageTk.PhotoImage(self.current_image)
        image_label = ttk.Label(popup, image=photo)
        image_label.image = photo
        image_label.pack()

        # --- Variables for dragging ---
        self.drag_start_x = 0
        self.drag_start_y = 0

        def start_drag(event):
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        def drag(event):
            x = image_label.winfo_x() + event.x - self.drag_start_x
            y = image_label.winfo_y() + event.y - self.drag_start_y
            image_label.place(x=x, y=y)

        image_label.bind("<ButtonPress-1>", start_drag)
        image_label.bind("<B1-Motion>", drag)

        # Bind mouse wheel event for zoom
        image_label.bind("<MouseWheel>", self.zoom)

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_factor *= 1.1  # Zoom in
        else:
            self.zoom_factor /= 1.1  # Zoom out

        # Calculate the center of the zoom based on cursor position
        x = event.x
        y = event.y
        width, height = self.current_image.size

        # --- Calculate zoom size while maintaining aspect ratio ---
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)

        # --- Prevent image from getting too large ---
        max_width = self.root.winfo_screenwidth() // 2  # Limit to half the screen width
        max_height = self.root.winfo_screenheight() // 2  # Limit to half the screen height
        if new_width > max_width or new_height > max_height:
            return  # Don't zoom if it exceeds the limits

        # Determine the zoom factor that limits the scaling to the smaller dimension
        if new_width > new_height:
            zoom_factor = new_height / height
        else:
            zoom_factor = new_width / width

        new_width = int(width * zoom_factor)
        new_height = int(height * zoom_factor)

        # Calculate the bounding box for the zoomed image
        left = max(0, x - new_width // 2)
        top = max(0, y - new_height // 2)
        right = min(width, x + new_width // 2)
        bottom = min(height, y + new_height // 2)

        # Crop and resize the image
        zoomed_image = self.current_image.crop((left, top, right, bottom)).resize((new_width, new_height))
        photo = ImageTk.PhotoImage(zoomed_image)

        # Update the image label in the popup
        image_label = event.widget  # Get the label from the event
        image_label.config(image=photo)
        image_label.image = photo

    def search_entries(self, *args):
        search_term = self.search_var.get().lower()
        self.entry_listbox.delete(0, tk.END)
        for entry in self.entries:
            if search_term in entry['name'].lower() or \
                    search_term in entry.get('description', '').lower() or \
                    any(search_term in str(value).lower() for value in entry.values()):
                self.entry_listbox.insert(tk.END, entry['name'])

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
            if bbox:
                x, y, width, height = bbox  # Unpack bbox tuple

                if y <= event.y <= y + height:  # Check within bounds
                    entry = self.entries[index]

                    # Create tooltip text
                    tooltip_text = f"Name: {entry['name']}\n"

                    # Check if description is not blank
                    description = entry.get('description', '').strip()
                    if description:
                        words_per_line = 20
                        words = description.split()
                        wrapped_description = "\n".join(
                            " ".join(words[i:i + words_per_line])
                            for i in range(0, len(words), words_per_line)
                        )
                        tooltip_text += f"Description: {wrapped_description}\n"

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
                    return

        self.tooltip.withdraw()

    def refresh_entry_list(self):
        # --- Store selected index ---
        selected_index = self.entry_listbox.curselection()
        selected_index = selected_index if selected_index else None

        self.entry_listbox.delete(0, tk.END)
        for entry in self.entries:
            self.entry_listbox.insert(tk.END, entry['name'])

        # --- Restore selection ---
        if selected_index is not None:
            self.entry_listbox.selection_set(selected_index)
            self.entry_listbox.see(selected_index)  # Make sure it's visible

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
        # Create a blank entry with "Blank Entry" as the name
        entry = {
            'name': "Blank Entry",  # Set the name here
            'description': ''
        }

        # Add custom attributes with blank values
        for attr in self.custom_attributes:
            entry[attr] = ''

        self.entries.append(entry)
        self.save_data()
        self.refresh_entry_list()

        # Select the newly added entry
        self.entry_listbox.selection_clear(0, tk.END)
        self.entry_listbox.selection_set(tk.END)
        self.entry_listbox.see(tk.END)

        # Optionally, you can automatically focus on the name entry field
        self.name_entry.focus()

    def update_entry(self):
        selection = self.entry_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an entry to update!")
            return

        index = selection[0]  # Get the first element of the tuple (the index)
        entry = self.entries[index]

        entry['name'] = self.name_entry.get("1.0", tk.END).strip()
        entry['description'] = self.desc_entry.get("1.0", tk.END)

        for attr, var in self.custom_entries.items():
            value = var.get()
            if value:
                entry[attr] = value
            elif attr in entry:
                del entry[attr]

        self.save_data()
        self.refresh_entry_list()

        messagebox.showinfo("Applied", "Changes applied successfully!")

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

        self.name_entry.delete("1.0", tk.END)  # Clear and insert into Text widget
        self.name_entry.insert("1.0", entry.get('name', ''))
        self.desc_entry.delete("1.0", tk.END)  # Clear and insert into Text widget
        self.desc_entry.insert("1.0", entry.get('description', ''))

        # Fill custom attributes
        for attr, var in self.custom_entries.items():
            var.set(entry.get(attr, ''))

        selection = self.entry_listbox.curselection()
        if selection:
            index = selection[0]
            entry = self.entries[index]
            self.display_images(entry)  # Display images when an entry is selected

    def clear_inputs(self):
        self.name_entry.delete("1.0", tk.END)  # Clear Text widget
        self.desc_entry.delete("1.0", tk.END)  # Clear Text widget
        for var in self.custom_entries.values():
            var.set("")

        # Update the listbox to reflect the cleared input
        self.refresh_entry_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = EntryCollectionManager(root)
    root.mainloop()
