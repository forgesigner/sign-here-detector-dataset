import os
import sys
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm
from typing import List, Tuple

# from config import ANNOTATED_PDFS_DIR, BASE_HEATMAPS_DIR

RASTEIZED_PDFS_DIR = "../CUAD_v1_rasterized"
ANNOTATED_PDFS_DIR = "../CUAD_v1_annotations"
BASE_HEATMAPS_DIR = "../CUAD_v1_heatmaps"


def get_last_directory(path: str) -> str:
    path = os.path.normpath(path)
    path_parts = path.split(os.sep)
    return path_parts[-2]


def generate_heatmap(dimensions: Tuple[int, int], centers: List[List[int]], sds: List[Tuple[int, int]]) -> np.ndarray:
    combined_heatmap = np.zeros((dimensions[1], dimensions[0]))
    if not centers:
        return combined_heatmap
    for center, sd in zip(centers, sds):
        x = np.linspace(0, dimensions[0] - 1, dimensions[0])
        y = np.linspace(0, dimensions[1] - 1, dimensions[1])
        x, y = np.meshgrid(x, y)

        heatmap = np.exp(
            -(((x - center[0]) ** 2 / (2 * sd[0] ** 2)) + ((y - center[1]) ** 2 / (2 * sd[1] ** 2)))
        )

        combined_heatmap = np.maximum(combined_heatmap, heatmap)

    return combined_heatmap


def generate_single_heatmap_for_image(img_path: str, width: int = 662, height: int = 936, dy: int = 100,
                                      dx: int = 100) -> np.ndarray:
    annotation_path = img_path.replace("rasterized", "annotations").replace(".png", ".json")
    with open(annotation_path, "r") as f:
        annotation = json.load(f)
    coordinates = annotation.get("centers", None)
    heatmap = generate_heatmap((width, height), coordinates, [(dx, dy)] * len(coordinates))
    return heatmap


class HeatmapGenerator:
    def __init__(self, annotation_paths: List[str], heatmap_dir: str, dy: int = 100, dx: int = 100):
        self.annotation_paths = annotation_paths
        self.heatmap_dir = heatmap_dir
        self.dy = dy
        self.dx = dx
        self.kek = 0

    def get_heatmap_dir_and_file_path(self, annotation_path: str) -> Tuple[str, str]:
        heatmap_dir = os.path.join(self.heatmap_dir, get_last_directory(annotation_path))
        heatmap_file = os.path.splitext(os.path.basename(annotation_path))[0] + ".png"
        return heatmap_dir, heatmap_file

    def generate_heatmap_from_annotation(self, annotation_path: str, width: int = 662, height: int = 936) -> None:
        with open(annotation_path, "r") as f:
            annotation = json.load(f)
        coordinates = annotation.get("centers", None)
        heatmap = generate_heatmap((width, height), coordinates, [(self.dx, self.dy)] * len(coordinates))
        dir_path, heatmap_file_path = self.get_heatmap_dir_and_file_path(annotation_path)
        os.makedirs(dir_path, exist_ok=True)
        plt.imsave(os.path.join(dir_path, heatmap_file_path), heatmap, cmap="gray")

    def generate_heatmaps(self) -> None:
        for annotation_path in tqdm(self.annotation_paths):
            self.generate_heatmap_from_annotation(annotation_path)


def find_annotations(annotation_dir: str) -> List[str]:
    annotation_paths = []
    for root, dirs, files in os.walk(annotation_dir):
        for file in files:
            if file.endswith(".json"):
                annotation_paths.append(os.path.join(root, file))
    return sorted(annotation_paths)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate heatmaps from annotations")
    parser.add_argument(
        "--annot_dir",
        type=str,
        default=ANNOTATED_PDFS_DIR,
        help="base directory to write annotations to",
    )
    parser.add_argument(
        "--heatmaps_dir",
        type=str,
        default=BASE_HEATMAPS_DIR,
        help="base directory to write heatmaps to",
    )

    parser.add_argument(
        "--dx",
        type=int,
        default=100,
        help="x deviation for heatmap generation",
    )

    parser.add_argument(
        "--dy",
        type=int,
        default=100,
        help="y deviation for heatmap generation",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    annotations_dir = args.annot_dir
    heatmap_dir = args.heatmaps_dir
    dy = args.dy
    dx = args.dx

    annotation_paths = find_annotations(annotations_dir)
    if not annotation_paths:
        print(f"Error: no annotations found in '{annotations_dir}'.", file=sys.stderr)
        return

    print(f"Found {len(annotation_paths)} annotations in {annotations_dir}")
    print(f"Writing annotations to '{heatmap_dir}'.")
    heatmap_generator = HeatmapGenerator(annotation_paths, heatmap_dir, dy, dx)
    heatmap_generator.generate_heatmaps()


if __name__ == "__main__":
    main()
