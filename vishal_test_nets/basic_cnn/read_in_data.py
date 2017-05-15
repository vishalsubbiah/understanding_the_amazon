import os.path
from PIL import Image

import tifffile
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
import torch
from torch import np 
from torch.utils.data import DataLoader
from torch.utils.data.dataset import Dataset
from torchvision import transforms


class AmazonDataset(Dataset):
    """
    class to conform data to pytorch API
    """
    def __init__(self, csv_path, img_path, img_ext, dtype):
    
        self.img_path = img_path
        self.img_ext = img_ext
        self.dtype = dtype

        df = pd.read_csv(csv_path)
        
        self.mlb = MultiLabelBinarizer()
        ## prepend other img transforms to this list
        self.transforms = transforms.Compose([transforms.ToTensor()])
        ## the paths to the images
        self.X_train = df['image_name']
        self.y_train = self.mlb.fit_transform(df['tags'].str.split()).astype(np.float32)

    def __getitem__(self, index):
        """
        return X_train image and y_train index
        """
        img_str = self.X_train[index] + self.img_ext
        load_path = os.path.join(self.img_path, img_str)
        ## branching for different backends
        if self.img_ext == '.jpg':
            img = Image.open(load_path)
        ## tifffile
        elif self.img_ext == '.tif':
            img = tifffile.imread(load_path)
            img = np.asarray(img, dtype=np.int32)

        img = self.transforms(img)
        label = torch.from_numpy(self.y_train[index]).type(self.dtype)
        return img, label

    def __len__(self):
        return len(self.X_train.index)


if __name__ == '__main__':
    csv_path = 'data/train_v2.csv'
    img_path = 'data/train-tif-v2'
    img_ext = '.tif'
    dtype = torch.FloatTensor
    training_dataset = AmazonDataset(csv_path, img_path, img_ext, dtype)
    train_loader = DataLoader(
        training_dataset,
        batch_size=256,
        shuffle=True,
        num_workers=4 # 1 for CUDA
        # pin_memory=True # CUDA only
    )
    for t, (x, y) in enumerate(train_loader):
        try:
            print(x.size())
            break
        except FileNotFoundError:
            continue