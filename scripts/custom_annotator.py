#!/usr/bin/env python3
import argparse
import os
import sys
import json

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
from PIL import Image, ImageTk


class ImageAnnotator:
    def __init__(
        self,
        master: tk.Tk,
        image_paths: List[str],
        base_annotation_dir: str,
        start_image_index: int = 0,
    ):
        self.master = master
        self.image_paths = image_paths
        self.base_annotation_dir = base_annotation_dir
        self.current_image = None
        self.image_index = self.find_first_unannotated_image(start_image_index)

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

    def load_image(self) -> None:
        if 0 <= self.image_index < len(self.image_paths):
            image_path = self.image_paths[self.image_index]
            self.current_image = Image.open(image_path)
            self.tk_image = ImageTk.PhotoImage(self.current_image)
            self.center_image()
            self.master.title(
                f"Annotating: {os.path.relpath(image_path)}"
            )  # Show the path in the window title
            # Load existing annotations if any
            self.load_annotations(image_path)
        else:
            messagebox.showinfo("Finished", "No more images to annotate.")
            self.master.quit()

    def find_first_unannotated_image(self, start_index: int) -> int:
        for index in range(start_index, len(self.image_paths)):
            json_file_path = self.get_annotation_file_path(self.image_paths[index])
            if not os.path.exists(json_file_path):
                return index
        return start_index

    def delete_last_point(self, _: tk.Event) -> None:
        if self.coordinates:
            self.coordinates.pop()
            self.center_image()  # Redraw the image and points

    def prev_image(self, _: tk.Event) -> None:
        if self.image_index > 0:
            self.image_index -= 1
            self.coordinates = []  # Clear current points
            self.load_image()  # Load the previous image

    def load_annotations(self, image_path: str) -> None:
        json_file_path = self.get_annotation_file_path(image_path)
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as f:
                data = json.load(f)
                self.coordinates = data.get("centers", [])
                self.redraw_points()  # Function to redraw points

    def get_annotation_file_path(self, image_path: str) -> str:
        annotation_dir = os.path.join(self.base_annotation_dir, self.get_last_directory(image_path))
        json_file = os.path.splitext(os.path.basename(image_path))[0] + ".json"
        return os.path.join(annotation_dir, json_file)

    def redraw_points(self) -> None:
        self.center_image()  # Clear the canvas and redraw the image
        image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
        image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2
        for coord in self.coordinates:
            canvas_x = coord[0] + image_x
            canvas_y = coord[1] + image_y
            self.canvas.create_oval(
                canvas_x - 5, canvas_y - 5, canvas_x + 5, canvas_y + 5, fill="red"
            )

    def center_image(self, _: Optional[tk.Event] = None) -> None:
        self.canvas.delete("all")  # Clear the canvas
        if self.tk_image:
            # Set the scroll region to encompass the image
            self.canvas.config(scrollregion=(0, 0, self.tk_image.width(), self.tk_image.height()))

            # Calculate the coordinates to center the image
            image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
            image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2

            # Place the image in the center
            self.canvas.create_image(image_x, image_y, anchor="nw", image=self.tk_image)

            # Redraw the points at the new relative positions
            for coord in self.coordinates:
                x, y = coord
                # Translate the image coordinates back to canvas coordinates
                canvas_x = x + image_x
                canvas_y = y + image_y
                self.canvas.create_oval(
                    canvas_x - 5, canvas_y - 5, canvas_x + 5, canvas_y + 5, fill="red"
                )

    def set_point(self, event: tk.Event) -> None:
        image_x = (self.canvas.winfo_width() - self.tk_image.width()) // 2
        image_y = (self.canvas.winfo_height() - self.tk_image.height()) // 2

        # Translate event coordinates to image coordinates
        x = self.canvas.canvasx(event.x) - image_x
        y = self.canvas.canvasy(event.y) - image_y
        # Check if the click is within the bounds of the image
        if (
            0 <= x < self.tk_image.width()
            and 0 <= y < self.tk_image.height()
            and (int(x), int(y)) not in self.coordinates
        ):
            self.coordinates.append((int(x), int(y)))
            # We draw the point relative to the canvas, not the image
            self.canvas.create_oval(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill="red")

    def get_last_directory(self, path: str) -> str:
        # Normalize the path to remove any trailing slash
        path = os.path.normpath(path)

        # Split the path into parts
        path_parts = path.split(os.sep)

        return path_parts[-2]

    def save_coordinates_wrapper(self, _: Optional[tk.Event] = None) -> None:
        self.save_coordinates()

    def save_coordinates(self) -> None:
        image_path = self.image_paths[self.image_index]
        annotation_dir = os.path.join(self.base_annotation_dir, self.get_last_directory(image_path))
        os.makedirs(annotation_dir, exist_ok=True)

        json_data = {"centers": self.coordinates}
        json_file = os.path.splitext(os.path.basename(image_path))[0] + ".json"
        json_file_path = os.path.join(annotation_dir, json_file)

        with open(json_file_path, "w") as f:
            json.dump(json_data, f, indent=4)

        self.image_index += 1
        self.coordinates = []  # Reset the coordinates for the next image
        self.canvas.delete("all")  # Clear the canvas
        self.load_image()


def find_images(image_dir: str) -> List[str]:
    image_paths = []
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.endswith((".png")):
                image_paths.append(os.path.join(root, file))
    return sorted(image_paths)


def main():
    args = parse_args()
    image_dir = args.image_dir
    base_annotation_dir = args.annot_dir

    image_paths = find_images(image_dir)
    if not image_paths:
        print("Error: no images found in '{image_dir}'.", file=sys.stderr)
        return

    start_image_index = 0
    start_image_path = os.path.join(
        image_dir, "0" * (5 - len(str(args.start_from_doc))) + str(args.start_from_doc), "00000.png"
    )
    if args.start_from_doc > 0:
        try:
            start_image_index = image_paths.index(start_image_path)
        except ValueError:
            messagebox.showerror(
                "Error", f"The specified start image was not found: {start_image_path}"
            )
            sys.exit(1)

    print(f"Found {len(image_paths)} images in {image_dir}")
    print(f"Writing annotations to '{base_annotation_dir}'.")

    root = tk.Tk()
    root.geometry("800x600")

    ImageAnnotator(root, image_paths, base_annotation_dir, start_image_index=start_image_index)
    root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Custom annotator for ForgeSigner dataset")
    parser.add_argument(
        "--image_dir",
        type=str,
        default="../CUAD_v1_rasterized",
        help="base directory to search for images",
    )
    parser.add_argument(
        "--annot_dir",
        type=str,
        default="../CUAD_v1_annotations",
        help="base directory to write annotations to",
    )
    parser.add_argument("--start_from_doc", type=int, default=0, help="Skip first N documents")
    return parser.parse_args()


if __name__ == "__main__":
    main()
