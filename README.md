# Photomosaic

This tool helps you build photomosaics from a source image and a catalog of images for tiles.

It doesn't just find the color average for each pixel and each image to match, but does a pixel by pixel color comparison for images of a given size. In this example I used images cropped 30x30, so it would compare all 900 pixels to a 30x30 section of the cropped and resized source image. You can see this in the datails of the eyebrows and mouth.

[photomosaic](example/10x10_angryface.png)
[original](example/10x10_angryface.png)

The images were sourced from a set of 1600 nature photos from Pexels.com. An included tool will let you collect images from pexels on your own.

## Usage

### Generate Tile Images

First you need to make a `.npy` file of the tile images using either [import_image](import_image.py) or [import_pexels](import_pexels.py).

It is highly encouraged you use the `-o` argument for your numpy file, or you can accidentally combine files of source images.

### Generate Photomosaic

Next run [make_image](make_image.py) with the `.npy` file you generated and a source image, and it will generate your photomosaic!
