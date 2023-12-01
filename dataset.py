from .splitter import TrainTestSplitter
from .scripts.generate_heat_maps import generate_single_heatmap_for_image
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from PIL import Image
import os



class SignatureDataset(Dataset):
    def __init__(self, train=True, transform=transforms.Compose([
        transforms.Resize((936, 662)),
        transforms.ToTensor(),
    ])):
        self.train = train
        self.transform = transform

        self.splitter = TrainTestSplitter(image_dir='CUAD_v1_rasterized',
                                          annotation_dir='CUAD_v1_annotations')

        self.image_paths = self.splitter.get_subset(train=self.train)

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert('RGB')
        heatmap = generate_single_heatmap_for_image(img_path)

        if self.transform:
            # image = Image.fromarray(image)
            heatmap = Image.fromarray(heatmap)
            image = self.transform(image).float()
            heatmap = self.transform(heatmap).float()

        return image, heatmap
