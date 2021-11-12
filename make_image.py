import argparse
import numpy as np
import os
from PIL import Image as PIL_Image

try:
    import quacainia.progress.progress as progress
except ImportError:
    progress = None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'image',
    )
    parser.add_argument(
        'mosaic_images',
    )
    parser.add_argument(
        '-s', '--size',
        dest='size',
        default=30,
        type=int,
        help="Will make the new image {size} mosaic images high and wide."
    )

    args = parser.parse_args()

    images_dict = get_images(args.mosaic_images)
    make_image(
        images_dict,
        args.image,
        args.size)


def make_image(images_dict, image, size=30):
    original_image_name = os.path.basename(image)
    filename = f"{size}x{size}_{original_image_name}"
    if filename[-3:] != 'png':
        filename += '.png'
    filepath = os.path.join(os.path.dirname(image), filename)
    if os.path.exists(filepath):
        print(f"File already exists: {filepath}")
        return

    source_image, source_image_shape = get_source_image(
        image, size, images_dict)

    images = np.array(list(images_dict.values()))
    image_names = list(images_dict.keys())

    mosaic, used_images = get_pixels(
        images, source_image, image_names, filepath)

    new_image = PIL_Image.new('RGB', source_image_shape)
    for x in range(source_image_shape[0]//30):
        for y in range(source_image_shape[1]//30):
            image = used_images[x][y]
            new_image.paste(PIL_Image.fromarray(image, mode="RGB"), (x*30, y*30))
    # new_image.show()

    num_images_shape = [d//30 for d in source_image_shape]

    new_image.save(filepath)
    print(f"Saved to: {filepath}")


def get_images(images_filepath):
    images_dict = np.load(images_filepath, allow_pickle=True)[()]
    return images_dict


def get_source_image(image, size, images_dict):
    tile_key, tile_image = images_dict.popitem()
    images_dict[tile_key] = tile_image
    pixel_shape = tuple(np.array(tile_image.shape[:2]) * size)

    image = PIL_Image.open(
        image
    )

    tile_image_size = tile_image.shape[:2]

    size_ratios = np.divide(
        np.array(image.size), np.array(tile_image_size)
    )

    min_ratio_idx = np.argmin(size_ratios)
    crop_size = [0, 0]
    crop_size[min_ratio_idx] = image.size[min_ratio_idx]
    crop_size[not min_ratio_idx] = int(round(
        tile_image_size[not min_ratio_idx] * size_ratios[min_ratio_idx]
    ))
    crop_size = tuple(crop_size)
    img_width, img_height = image.size

    image2 = image.crop((
        (img_width - crop_size[0]) // 2,
        (img_height - crop_size[1]) // 2,
        (img_width + crop_size[0]) // 2,
        (img_height + crop_size[1]) // 2
    ))
    # shape = (30*size, 30*size)
    image3 = image2.resize(pixel_shape)
    image4 = image3.convert('RGB')

    imarr = np.asarray(image4)

    return (imarr, pixel_shape)


def get_pixels(images, source_image, image_names, filepath):
    pb = progress.ProgressBar([{'align': 'right'}, {}])
    mosaic_shape = (
        np.shape(source_image)[0]//30,
        np.shape(source_image)[1]//30,
        30,
        30,
        3
    )
    try:
        images_16 = images.astype(np.int32)
    except ValueError:
        print(images[0].shape)
        print('poo')
        raise
    source_image = source_image.astype('int32')
    mosaic = np.empty(mosaic_shape)
    selected_images = []
    used_images = []
    i = 0
    pb.refresh(0, "0%")
    images_len = np.shape(images)[0]
    for y in range(np.shape(source_image)[1]//30):
        row = []
        for x in range(np.shape(source_image)[0]//30):
            image_slice = source_image[x*30:(x+1)*30, y*30:(y+1)*30]
            sub = np.subtract(images_16, image_slice)
            distance = np.sqrt(np.sum(np.square(sub), axis=3))
            ave = np.abs(
                np.average(
                    np.average(
                        distance,
                        axis=1
                    ),
                    axis=1
                )
            )
            i += 1
            while True:
                idx = np.argmin(ave)
                pct = i / mosaic_shape[0] / mosaic_shape[1]
                pb.refresh(
                    pct,
                    [
                        f"{int(pct * 100):d}%",
                        f"{i} {image_names[idx]}"
                    ]
                )
                if idx in used_images:
                    if ave[idx] > 300:
                        raise Exception("Ran out of images.")
                    ave[idx] += 1000
                    continue
                row.append(images[idx])
                used_images.append(idx)
                mosaic[x, y] = images[idx]
                break
        selected_images.append(row)
    pb.refresh(1, ["0%", "Done!"])
    with open(f"{filepath}_used_images.txt", 'w') as used_images_file:
        for idx in used_images:
            used_images_file.write(f"{image_names[idx]}\n")
    return (mosaic, selected_images)


if __name__ == '__main__':
    main()
