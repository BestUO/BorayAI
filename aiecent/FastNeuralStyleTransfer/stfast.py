from FastNeuralStyleTransfer.models import TransformerNet
import torch
from torchvision import transforms
from torchvision.utils import save_image
from PIL import Image
from pathlib import Path
import numpy as np

mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])
lastmodelpath = ""

def GetModel(usegpu, args):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    return TransformerNet().to(device)


def Eval(usegpu, model, contentsize, stylesize, param):
    global lastmodelpath
    with torch.no_grad():
        device = torch.device(
            "cuda" if usegpu and torch.cuda.is_available() else "cpu")
        model.eval()
        content_tf = style_transform(contentsize)
        

        contentpath, modelpath, resultpath = param
        if lastmodelpath != modelpath:
            model.load_state_dict(torch.load(modelpath, map_location=torch.device(device)))
            lastmodelpath = modelpath
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
