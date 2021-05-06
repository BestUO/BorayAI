from util import WCT
import torch
from torchvision import transforms
from torchvision.utils import save_image
from PIL import Image


def GetModel(args):
    return WCT(args)


def Eval(usegpu, model, contentsize, stylesize, params):
    with torch.no_grad():
        device = torch.device(
            "cuda" if usegpu and torch.cuda.is_available() else "cpu")
        model = model.to(device)
        model.eval()
        content_tf = WCTTransform(contentsize)
        style_tf = WCTTransform(stylesize)
        csF = torch.Tensor().to(device)

        for param in params:
            contentpath, stylepath, alpha, resultpath = param
            contentImg = content_tf(
                Image.open(contentpath)).to(device).unsqueeze(0)
            styleImg = style_tf(Image.open(stylepath)).to(device).unsqueeze(0)
            output = StyleTransfer(model, float(alpha), contentImg, styleImg,
                                   csF)

            output = output.cpu()
            save_image(output, resultpath)


def WCTTransform(size, crop=False):
    transform_list = []
    if size != 0:
        transform_list.append(transforms.Resize(size))
    if crop:
        transform_list.append(transforms.CenterCrop(size))
    transform_list.append(transforms.ToTensor())
    # transform_list.append(transforms.Normalize(mean, std))
    transform = transforms.Compose(transform_list)
    return transform


def StyleTransfer(wct, alpha, contentImg, styleImg, csF):
    sF5 = wct.e5(styleImg)
    cF5 = wct.e5(contentImg)
    sF5 = sF5.data.cpu().squeeze(0)
    cF5 = cF5.data.cpu().squeeze(0)
    csF5 = wct.transform(cF5, sF5, csF, alpha)
    Im5 = wct.d5(csF5)

    sF4 = wct.e4(styleImg)
    cF4 = wct.e4(Im5)
    sF4 = sF4.data.cpu().squeeze(0)
    cF4 = cF4.data.cpu().squeeze(0)
    csF4 = wct.transform(cF4, sF4, csF, alpha)
    Im4 = wct.d4(csF4)

    sF3 = wct.e3(styleImg)
    cF3 = wct.e3(Im4)
    sF3 = sF3.data.cpu().squeeze(0)
    cF3 = cF3.data.cpu().squeeze(0)
    csF3 = wct.transform(cF3, sF3, csF, alpha)
    Im3 = wct.d3(csF3)

    sF2 = wct.e2(styleImg)
    cF2 = wct.e2(Im3)
    sF2 = sF2.data.cpu().squeeze(0)
    cF2 = cF2.data.cpu().squeeze(0)
    csF2 = wct.transform(cF2, sF2, csF, alpha)
    Im2 = wct.d2(csF2)

    sF1 = wct.e1(styleImg)
    cF1 = wct.e1(Im2)
    sF1 = sF1.data.cpu().squeeze(0)
    cF1 = cF1.data.cpu().squeeze(0)
    csF1 = wct.transform(cF1, sF1, csF, alpha)
    Im1 = wct.d1(csF1)
    return Im1
