# from models import TransformerNet
from FastNeuralStyleTransfer.models import TransformerNet
from pathlib import Path
from utils import style_transform, denormalize
import torch
from torchvision.utils import save_image
from PIL import Image
import argparse

import numpy as np
from torchvision import transforms
mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])


def fastneuralstyletransfer(content_paths,
                            style_paths,
                            output_dir,
                            args,
                            interpolation_weights=None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = style_transform()
    transformer = TransformerNet().to(device)

    modelsdir = Path(args.fnstmodel_dir)
    modelpaths = [modelpath for modelpath in modelsdir.iterdir()]

    for modelpath in modelpaths:
        transformer.load_state_dict(torch.load(modelpath))
        transformer.eval()

        for content_path in content_paths:
            image_tensor = transform(Image.open(content_path)).to(device)
            image_tensor = image_tensor.unsqueeze(0)

            stylized_image = denormalize(transformer(image_tensor)).cpu()

            output_name = output_dir / "{content_path}_fnst_{style_path}{save_ext}".format(
                content_path=content_path.stem,
                style_path=modelpath.stem,
                save_ext=".jpg")
            save_image(stylized_image, str(output_name))


def GetContentAndStylePaths(args):
    content_dirpeople = []
    contentandstyle = []

    if args.content_dir:
        content_dirdata = Path(args.content_dir)
        content_dirpeople = [name for name in content_dirdata.iterdir()]

    for peoplepath in content_dirpeople:
        stylepath = peoplepath.joinpath("style")
        style_paths = [style for style in stylepath.iterdir()]
        if len(style_paths) == 0:
            style_dir = Path(args.style_dir)
            style_paths = [f for f in style_dir.glob('*')]
        content_paths = [
            content for content in peoplepath.iterdir() if content.is_file()
        ]
        contentandstyle.append([content_paths, style_paths])

    return contentandstyle

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--content_dir',
                        type=str,
                        default='/home/uncle_orange/mydevice/cv/style_transfer/content/20210225',
                        help='Directory path to a batch of content images')
    parser.add_argument('--output',
                        type=str,
                        default='../output',
                        help='Directory to save the output image(s)')
    # modelspaths
    parser.add_argument('--fnstmodel_dir',
                        type=str,
                        default='../models/fnst')
    # Additional options
    parser.add_argument('--content_size',
                        type=int,
                        default=512,
                        help='New (minimum) size for the content image,cccc \
                        keeping the original size if set to 0')
    parser.add_argument('--style_size',
                        type=int,
                        default=512,
                        help='New (minimum) size for the style image, \
                        keeping the original size if set to 0')
    # nouse
    parser.add_argument('--style_dir',
                    type=str,
                    default="/home/uncle_orange/mydevice/cv/style_transfer/FastNeuralStyleTransfer/images/styles",
                    help='Directory path to a batch of style images')

    args = parser.parse_args()

    output_dirday = Path(args.output)
    contentandstyle = GetContentAndStylePaths(args)
    for content_paths, style_paths in contentandstyle:
        date, name = content_paths[0].parts[-3:-1]
        output_dir = output_dirday.joinpath(date, name)
        output_dir.mkdir(exist_ok=True, parents=True)

        fastneuralstyletransfer(content_paths, style_paths, output_dir, args)