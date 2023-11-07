#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import json
import os

class ImageAnnotator:
    def __init__(self, master, image_paths, base_annotation_dir):
        self.master = master
        self.image_paths = image_paths
        self.base_annotation_dir = base_annotation_dir
        self.current_image = None
        self.image_index = 0
        self.coordinates = []

        self.canvas = tk.Canvas(master, cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Adding horizontal and vertical scrollbars
        hbar = tk.Scrollbar(master, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = tk.Scrollbar(master, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        hbar.config(command=self.canvas.xview)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        self.master.bind("<Return>", self.save_coordinates_wrapper)
        self.master.bind("<BackSpace>", self.delete_last_point)
        self.master.bind("<Left>", self.prev_image)

        self.canvas.bind("<Button-1>", self.set_point)
        self.canvas.bind("<Configure>", self.center_image)

        self.load_image()

    def load_image(self):
        if 0 <= self.image_index < len(self.image_paths):
            image_path = self.image_paths[self.image_index]
            self.current_image = Image.open(image_path)
            self.tk_image = ImageTk.PhotoImage(self.current_image)
            self.center_image()
            self.master.title(f"Annotating: {image_path}")  # Show the path in the window title
            # Load existing annotations if any
            self.load_annotations(image_path)
        else:
            messagebox.showinfo("Finished", "No more images to annotate.")
            self.master.quit()


    def delete_last_point(self, event):
        if self.coordinates:
            self.coordinates.pop()
            self.center_image()  # Redraw the image and points

    def prev_image(self, event):
        if self.image_index > 0:
            self.image_index -= 1
            self.coordinates = []  # Clear current points
            self.load_image()  # Load the previous image

    def load_annotations(self, image_path):
        json_file_path = self.get_annotation_file_path(image_path)
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                data = json.load(f)
                self.coordinates = data.get('centers', [])
                self.redraw_points()  # Function to redraw points

    def get_annotation_file_path(self, image_path):
        annotation_dir = os.path.join(self.base_annotation_dir, self.get_last_directory(image_path))
        json_file = os.path.splitext(os.path.basename(image_path))[0] + '.json'
        return os.path.join(annotation_dir, json_file)

    def redraw_points(self):
        self.center_image()  # Clear the canvas and redraw the image
        image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
        image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2
        for coord in self.coordinates:
            canvas_x = coord[0] + image_x
            canvas_y = coord[1] + image_y
            self.canvas.create_oval(
                canvas_x - 5, canvas_y - 5, canvas_x + 5, canvas_y + 5, fill='red'
            )


    def center_image(self, event=None):
        self.canvas.delete("all")  # Clear the canvas
        if self.tk_image:
            # Set the scroll region to encompass the image
            self.canvas.config(scrollregion=(0, 0, self.tk_image.width(), self.tk_image.height()))

            # Calculate the coordinates to center the image
            image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
            image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2

            # Place the image in the center
            self.canvas.create_image(
                image_x,
                image_y,
                anchor="nw",
                image=self.tk_image
            )

            # Redraw the points at the new relative positions
            for coord in self.coordinates:
                x, y = coord
                # Translate the image coordinates back to canvas coordinates
                canvas_x = x + image_x
                canvas_y = y + image_y
                self.canvas.create_oval(
                    canvas_x - 5, canvas_y - 5, canvas_x + 5, canvas_y + 5, fill='red'
                )


    def set_point(self, event):
        image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
        image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2

        # Translate event coordinates to image coordinates
        x = self.canvas.canvasx(event.x) - image_x
        y = self.canvas.canvasy(event.y) - image_y
        # Check if the click is within the bounds of the image
        if 0 <= x < self.tk_image.width() and 0 <= y < self.tk_image.height() and (int(x), int(y)) not in self.coordinates:
            self.coordinates.append((int(x), int(y)))
            # We draw the point relative to the canvas, not the image
            self.canvas.create_oval(
                event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill='red'
            )

    def get_last_directory(self, path):
        
        # Normalize the path to remove any trailing slash
        path = os.path.normpath(path)
        
        # Split the path into parts
        path_parts = path.split(os.sep)
        
        return path_parts[-2]

    def save_coordinates_wrapper(self, event=None):
        self.save_coordinates()

    def save_coordinates(self):
        image_path = self.image_paths[self.image_index]
        annotation_dir = os.path.join(self.base_annotation_dir, self.get_last_directory(image_path))
        os.makedirs(annotation_dir, exist_ok=True)
        
        json_data = {'centers': self.coordinates}
        json_file = os.path.splitext(os.path.basename(image_path))[0] + '.json'
        json_file_path = os.path.join(annotation_dir, json_file)
        
        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=4)
        
        self.image_index += 1
        self.coordinates = []  # Reset the coordinates for the next image
        self.canvas.delete("all")  # Clear the canvas
        self.load_image()


def find_images(image_dir):
    image_paths = []
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.endswith(('.png')):
                image_paths.append(os.path.join(root, file))
    return sorted(image_paths)

def main():
    root = tk.Tk()
    root.geometry("800x600")

    # Define the image directory relative to the annotator script's location
    script_dir = os.path.dirname(__file__)
    image_dir = os.path.join(script_dir, "../../CUAD_v1_rasterized")
    base_annotation_dir = os.path.join(script_dir, "../../CUAD_v1_annotations")

    image_paths = find_images(image_dir)

    if not image_paths:
        messagebox.showerror("Error", "No images found in the specified directory.")
        return

    ImageAnnotator(root, image_paths, base_annotation_dir)
    root.mainloop()

if __name__ == "__main__":
    main()
