import PytorchAdaIN.net as adainnet
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
from torchvision.utils import save_image
from PytorchAdaIN.function import adaptive_instance_normalization


def GetModel(usegpu, config):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    vgg = adainnet.vgg
    vgg.load_state_dict(torch.load(config["adain_vgg"]))
    vgg = nn.Sequential(*list(vgg.children())[:31])

    decoder = adainnet.decoder
    decoder.load_state_dict(torch.load(config["adain_decoder"]))
    return vgg.to(device), decoder.to(device)


def Eval(usegpu, model, contentsize, stylesize, params):
    with torch.no_grad():
        device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
        vgg, decoder = model
        vgg.eval()
        decoder.eval()
        content_tf = AdainTransform(contentsize)
        style_tf = AdainTransform(stylesize)

        for param in params:
            contentpath, stylepath, alpha, resultpath = param
            contentImg = content_tf(Image.open(
                str(contentpath))).to(device).unsqueeze(0)
            styleImg = style_tf(Image.open(stylepath)).to(device).unsqueeze(0)

            output = StyleTransfer(device, vgg, decoder, contentImg, styleImg, float(alpha))

            output = output.cpu()
            save_image(output, resultpath)


def AdainTransform(size, crop=False):
    transform_list = []
    if size != 0:
        transform_list.append(transforms.Resize(size))
    if crop:
        transform_list.append(transforms.CenterCrop(size))
    transform_list.append(transforms.ToTensor())
    # transform_list.append(transforms.Normalize(mean, std))
    transform = transforms.Compose(transform_list)
    return transform


def StyleTransfer(device,
                  vgg,
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
