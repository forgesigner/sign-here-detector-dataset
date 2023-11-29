import json
import os
import random
from typing import List, Tuple


def check_not_empty_annotation(file_path):
    with open(file_path, "r") as f:
        annotation = json.load(f)
    coordinates = annotation.get("centers", None)
    return coordinates is not None and len(coordinates) > 0


def find_annotations_and_images(annotation_dir: str) -> Tuple[List[str], List[str]]:
    annotation_paths = []
    image_paths = []
    for root, dirs, files in os.walk(annotation_dir):
        for file in files:
            if file.endswith(".json"):
                if not check_not_empty_annotation(os.path.join(root, file)):
                    continue
                if not os.path.exists(
                        os.path.join(root.replace('annotations', 'rasterized'), file.replace(".json", ".png"))):
                    continue
                annotation_paths.append(os.path.join(root, file))
                image_paths.append(
                    os.path.join(root.replace('annotations', 'rasterized'), file.replace(".json", ".png")))
    return sorted(annotation_paths), sorted(image_paths)


class TrainTestSplitter:
    def __init__(self, image_dir, annotation_dir, split_ratio=0.8):
        self.image_dir = image_dir
        self.annotation_dir = annotation_dir
        self.split_ratio = split_ratio

        self.valid_annotations, self.valid_images = find_annotations_and_images(annotation_dir)
        print(self.valid_annotations)
        print(self.valid_images)

        zipped = list(zip(self.valid_annotations, self.valid_images))
        random.shuffle(zipped)
        self.valid_annotations, self.valid_images = zip(*zipped)

        if len(self.valid_annotations) != len(self.valid_images):
            raise ValueError("Number of annotations and images are not equal")
        split_index = int(len(self.valid_annotations) * split_ratio)
        self.train_image_paths = self.valid_images[:split_index]
        self.test_image_paths = self.valid_images[split_index:]

    def get_subset(self, train=True):
        if train:
            return self.train_image_paths
        else:
            return self.test_image_paths
