from models import TransformerNet
import torch
from torchvision import transforms
from torchvision.utils import save_image
from PIL import Image
from pathlib import Path
import numpy as np

mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])

def GetModel(args):
    return TransformerNet()


def Eval(usegpu, model, contentsize, stylesize, params):
    with torch.no_grad():
        device = torch.device(
            "cuda" if usegpu and torch.cuda.is_available() else "cpu")
        model = model.to(device)
        model.eval()
        content_tf = style_transform(contentsize)
        
        for param in params:
            contentpath, stylemodel, resultpath = param
            model.load_state_dict(torch.load(stylemodel, map_location=torch.device(device)))
            contentImg = content_tf(Image.open(str(contentpath))).to(device).unsqueeze(0)
            output = denormalize(model(contentImg)).cpu()
            save_image(output, resultpath)


def style_transform(image_size=512):
    """ Transforms for style image """
    transform = transforms.Compose(
        [
            transforms.Resize(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean, std)
        ]
    )
    return transform


def denormalize(tensors):
    """ Denormalizes image tensors using mean and std """
    for c in range(3):
        tensors[:, c].mul_(std[c]).add_(mean[c])
    return tensors
