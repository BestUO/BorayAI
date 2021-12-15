import argparse
import os
import sys
import random
from PIL import Image
import numpy as np
import torch
import glob
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.utils import save_image
from torchvision import models
from FastNeuralStyleTransfer.models import TransformerNet, VGG16
from utils import *
import matplotlib.pyplot as plt
import time
from datetime import timedelta

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parser for Fast-Neural-Style")
    parser.add_argument("--vgg16_path", type=str, required=True, help="path to training dataset")
    parser.add_argument("--dataset_path", type=str, required=True, help="path to training dataset")
    parser.add_argument("--style_image", type=str, default="style-images/mosaic.jpg", help="path to style image")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--image_size", type=int, default=256, help="Size of training images")
    parser.add_argument("--style_size", type=int, help="Size of style image")
    parser.add_argument("--lambda_content", type=float, default=1e4, help="Weight for content loss")
    parser.add_argument("--lambda_style", type=float, default=1e10, help="Weight for style loss")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument("--checkpoint_model", type=str, help="Optional path to checkpoint model")
    parser.add_argument("--checkpoint_interval", type=int, default=500, help="Batches between saving model")
    parser.add_argument("--sample_interval", type=int, default=500, help="Batches between saving image samples")
    args = parser.parse_args()

    def get_time_dif(start_time):
        """获取已使用时间"""
        end_time = time.time()
        time_dif = end_time - start_time
        return timedelta(seconds=int(round(time_dif)))

    style_name = args.style_image.split("/")[-1].split(".")[0]
    os.makedirs(f"images/outputs/{style_name}-training", exist_ok=True)
    os.makedirs(f"checkpoints", exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Create dataloader for the training data
    train_dataset = datasets.ImageFolder(args.dataset_path, train_transform(args.image_size))
    dataloader = DataLoader(train_dataset, batch_size=args.batch_size)

    # Defines networks
    transformer = TransformerNet().to(device)
    model = models.vgg16(pretrained=False)
    netdatafile = torch.load(args.vgg16_path)
    model.load_state_dict(netdatafile)
    vgg = VGG16(model, requires_grad=False).to(device)

    # Load checkpoint model if specified
    if args.checkpoint_model:
        transformer.load_state_dict(torch.load(args.checkpoint_model))

    # Define optimizer and loss
    optimizer = Adam(transformer.parameters(), args.lr)
    l2_loss = torch.nn.MSELoss().to(device)

    # Load style image
    style = style_transform(args.style_size)(Image.open(args.style_image))
    style = style.repeat(args.batch_size, 1, 1, 1).to(device)

    # Extract style features
    features_style = vgg(style)
    gram_style = [gram_matrix(y) for y in features_style]

    # Sample 8 images for visual evaluation of the model
    image_samples = []
    for path in random.sample(glob.glob(f"{args.dataset_path}/*/*.jpg"), 8):
        image_samples += [train_transform(args.image_size)(Image.open(path))]
    image_samples = torch.stack(image_samples)

    def save_sample(batches_done):
        """ Evaluates the model and saves image samples """
        transformer.eval()
        with torch.no_grad():
            output = transformer(image_samples.to(device))
        # output = output.resize_as_(image_samples)
        image_grid = denormalize(torch.cat((image_samples.cpu(), output.cpu()), 2))
        save_image(image_grid, f"images/outputs/{style_name}-training/{batches_done}.jpg", nrow=4)

    total_batch = 0
    all_losses = []
    mintotal = float("inf")
    start_time = time.time()

    for epoch in range(args.epochs):
        epoch_metrics = {"content": [], "style": [], "total": []}
        for batch_i, (images, _) in enumerate(dataloader):
            # with torch.autograd.profiler.profile() as prof:
            transformer.train()
            optimizer.zero_grad()
            total_batch += 1

            images_original = images.to(device)
            images_transformed = transformer(images_original)

            # Extract features
            features_original = vgg(images_original)
            features_transformed = vgg(images_transformed)

            # Compute content loss as MSE between features
            content_loss = args.lambda_content * l2_loss(features_transformed.relu2_2, features_original.relu2_2)

            # Compute style loss as MSE between gram matrices
            style_loss = 0
            for ft_y, gm_s in zip(features_transformed, gram_style):
                gm_y = gram_matrix(ft_y)
                style_loss += l2_loss(gm_y, gm_s[: images.size(0), :, :])
            style_loss *= args.lambda_style

            total_loss = content_loss + style_loss

            total_loss.backward()
            optimizer.step()

            epoch_metrics["content"] += [content_loss.item()]
            epoch_metrics["style"] += [style_loss.item()]
            epoch_metrics["total"] += [total_loss.item()]
            
            if total_batch % args.sample_interval == 0:
                save_sample(total_batch)
                t = np.mean(epoch_metrics["total"])
                all_losses += [t]
                time_dif = get_time_dif(start_time)
                print(
                    "\r[Epoch %d/%d Batch %d Content: %.2f Style: %.2f Total: %.2f Time: %s"
                    % (
                        epoch,
                        args.epochs,
                        total_batch,
                        np.mean(epoch_metrics["content"]),
                        np.mean(epoch_metrics["style"]),
                        t,
                        time_dif
                    )
                )

                epoch_metrics["content"] = []
                epoch_metrics["style"] = []
                epoch_metrics["total"] = []

            # if total_batch % args.sample_interval and mintotal > all_losses[-1] == 0:
            #     mintotal = all_losses[-1]
            #     style_name = os.path.basename(args.style_image).split(".")[0]
            #     torch.save(transformer.state_dict(), f"checkpoints/{style_name}_minloss.pth")

            # print(prof.key_averages().table(sort_by="self_cpu_time_total"))
        style_name = os.path.basename(args.style_image).split(".")[0]
        torch.save(transformer.state_dict(), f"checkpoints/{style_name}_epoch.pth")

    plt.figure()
    plt.plot(all_losses)
    plt.show()