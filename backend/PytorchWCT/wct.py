import torch
from PIL import Image
from util import WCT
from torchvision import transforms
from torchvision.utils import save_image
# from photo_gif import GIFSmoothing
import numpy as np

mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])

def wct(content_paths,
        style_paths,
        output_dir,
        args,
        interpolation_weights=None):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    wct = WCT(args).to(device)
    content_tf = test_transform(args.content_size, False)
    style_tf = test_transform(args.style_size, False)
    csF = torch.Tensor().to(device)
    # smoothing_module = GIFSmoothing(r=35, eps=0.001)

    for content_path in content_paths:
        contentImg = content_tf(Image.open(str(content_path)))
        contentImg = contentImg.cuda().unsqueeze(0)
        for style_path in style_paths:
            styleImg = style_tf(Image.open(str(style_path)))
            styleImg = styleImg.cuda().unsqueeze(0)
            output = styleTransfer(args, wct, contentImg, styleImg, csF)
            output_name = output_dir / "{content_path}_wct_{style_path}{save_ext}".format(
                content_path=content_path.stem,
                style_path=style_path.stem,
                save_ext=args.save_ext)
            # denormalize(output)
            output = output.cpu()
            save_image(output, str(output_name))

            # new_img_PIL = transforms.ToPILImage()(output.float()[-1]).convert('RGB')
            # contentImgcpu = transforms.ToPILImage()(contentImg.data.cpu().float()[-1]).convert('RGB')
            # new_img_PIL = new_img_PIL.resize((contentImgcpu.width, contentImgcpu.height),Image.ANTIALIAS)
            # Im1 = smoothing_module.process(new_img_PIL, contentImgcpu)
            # Im1.save(output_name)


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


def styleTransfer(args, wct, contentImg, styleImg, csF):
    sF5 = wct.e5(styleImg)
    cF5 = wct.e5(contentImg)
    sF5 = sF5.data.cpu().squeeze(0)
    cF5 = cF5.data.cpu().squeeze(0)
    csF5 = wct.transform(cF5, sF5, csF, args.alpha)
    Im5 = wct.d5(csF5)

    sF4 = wct.e4(styleImg)
    cF4 = wct.e4(Im5)
    sF4 = sF4.data.cpu().squeeze(0)
    cF4 = cF4.data.cpu().squeeze(0)
    csF4 = wct.transform(cF4, sF4, csF, args.alpha)
    Im4 = wct.d4(csF4)

    sF3 = wct.e3(styleImg)
    cF3 = wct.e3(Im4)
    sF3 = sF3.data.cpu().squeeze(0)
    cF3 = cF3.data.cpu().squeeze(0)
    csF3 = wct.transform(cF3, sF3, csF, args.alpha)
    Im3 = wct.d3(csF3)

    sF2 = wct.e2(styleImg)
    cF2 = wct.e2(Im3)
    sF2 = sF2.data.cpu().squeeze(0)
    cF2 = cF2.data.cpu().squeeze(0)
    csF2 = wct.transform(cF2, sF2, csF, args.alpha)
    Im2 = wct.d2(csF2)

    sF1 = wct.e1(styleImg)
    cF1 = wct.e1(Im2)
    sF1 = sF1.data.cpu().squeeze(0)
    cF1 = cF1.data.cpu().squeeze(0)
    csF1 = wct.transform(cF1, sF1, csF, args.alpha)
    Im1 = wct.d1(csF1)
    return Im1
