import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.utils import save_image
import numpy as np

import net
from function import adaptive_instance_normalization, coral

mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])

def adain(content_paths,
          style_paths,
          output_dir,
          args,
          interpolation_weights=None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    decoder = net.decoder
    vgg = net.vgg

    decoder.eval()
    vgg.eval()

    decoder.load_state_dict(torch.load(args.AdaINdecoder))
    vgg.load_state_dict(torch.load(args.AdaINvgg))
    vgg = nn.Sequential(*list(vgg.children())[:31])

    vgg.to(device)
    decoder.to(device)

    content_tf = test_transform(args.content_size, args.crop)
    style_tf = test_transform(args.style_size, args.crop)
    do_interpolation = False

    for content_path in content_paths:
        if do_interpolation:  # one content image, N style image
            style = torch.stack(
                [style_tf(Image.open(str(p))) for p in style_paths])
            content = content_tf(Image.open(str(content_path))) \
                .unsqueeze(0).expand_as(style)
            style = style.to(device)
            content = content.to(device)
            with torch.no_grad():
                output = style_transfer(vgg, decoder, content, style,
                                        args.alpha, interpolation_weights)
            output = output.cpu()
            output_name = output_dir / '{:s}_interpolation{:s}'.format(
                content_path.stem, args.save_ext)
            save_image(output, str(output_name))

        else:  # process one content and one style
            for style_path in style_paths:
                content = content_tf(Image.open(str(content_path)))
                style = style_tf(Image.open(str(style_path)))
                if args.preserve_color:
                    style = coral(style, content)
                style = style.to(device).unsqueeze(0)
                content = content.to(device).unsqueeze(0)
                with torch.no_grad():
                    output = style_transfer(vgg, decoder, content, style,
                                            args.alpha)
                # denormalize(output)
                output = output.cpu()
                output_name = output_dir / "{content_path}_adain_{style_path}{save_ext}".format(
                    content_path=content_path.stem,
                    style_path=style_path.stem,
                    save_ext=args.save_ext)
                # output_name = output_dir / '{:s}_stylized_{:s}{:s}'.format(
                #     content_path.stem, style_path.stem, args.save_ext)
                save_image(output, str(output_name))


def test_transform(size, crop):
    transform_list = []
    if size != 0:
        transform_list.append(transforms.Resize(size))
    if crop:
        transform_list.append(transforms.CenterCrop(size))
    transform_list.append(transforms.ToTensor())
    # transform_list.append(transforms.Normalize(mean, std))
    transform = transforms.Compose(transform_list)
    return transform


def denormalize(tensors):
    """ Denormalizes image tensors using mean and std """
    for c in range(3):
        tensors[:, c].mul_(std[c]).add_(mean[c])
    return tensors

def style_transfer(vgg,
                   decoder,
                   content,
                   style,
                   alpha=1.0,
                   interpolation_weights=None):
    assert (0.0 <= alpha <= 1.0)
    content_f = vgg(content)
    style_f = vgg(style)
    if interpolation_weights:
        _, C, H, W = content_f.size()
        feat = torch.FloatTensor(1, C, H, W).zero_().to(device)
        base_feat = adaptive_instance_normalization(content_f, style_f)
        for i, w in enumerate(interpolation_weights):
            feat = feat + w * base_feat[i:i + 1]
        content_f = content_f[0:1]
    else:
        feat = adaptive_instance_normalization(content_f, style_f)
    feat = feat * alpha + content_f * (1 - alpha)
    return decoder(feat)
