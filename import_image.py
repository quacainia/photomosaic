import argparse
import glob
import io
import numpy as np
import os
from PIL import Image as PIL_Image
import requests
import sys

try:
    import quacainia.progress.progress as progress
except ImportError:
    progress = None


class FailedLoadError(Exception):
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'width',
        type=int,
        help="Width that images for mosaic tiles should be cropped to."
    )

    parser.add_argument(
        'height',
        type=int,
        help="Height that images for mosaic tiles should be cropped to."
    )

    parser.add_argument(
        'path',
        action='store',
        nargs='+',
        help="Path to image directory or glob for images."
    )

    parser.add_argument(
        '-o', '--output',
        dest='output_file',
        default='images.npy',
        help="Output npy file path."
    )

    args = parser.parse_args()

    path = args.path

    if len(path) == 1 and os.path.isdir(path[0]):
        glob_path = os.path.join(path[0], '*')
        images = glob.glob(glob_path)
    else:
        images = path

    tile_image_size = (args.width, args.height)

    importer = ImportImage(args.output_file, tile_image_size)
    importer.add_images(images)


class ImportImage():
    def __init__(self, output_file, output_image_size):
        self.output_file = output_file
        self.output_image_size = output_image_size
        try:
            self.images_dict = np.load(output_file, allow_pickle=True)[()]
        except FileNotFoundError:
            self.images_dict = {}

    def add_image(self, image_path):
        image_name = os.path.basename(image_path)
        if '?' in image_name:
            image_name = image_name[:image_name.find('?')]
        try:
            if image_path.startswith('//') or image_path.startswith('http'):
                response = requests.get(image_path)
                if response.status_code != 200 and response.status_code != 304:
                    return
                image = PIL_Image.open(io.BytesIO(response.content))
            else:
                if not os.path.exists(image_path):
                    return
                    # raise FileNotFoundError(image_path)
                image = PIL_Image.open(image_path)

            size_ratios = np.divide(
                np.array(image.size), np.array(self.output_image_size)
            )

            min_ratio_idx = np.argmin(size_ratios)
            crop_size = [0, 0]
            crop_size[min_ratio_idx] = image.size[min_ratio_idx]
            crop_size[not min_ratio_idx] = int(round(
                self.output_image_size[not min_ratio_idx]
                * size_ratios[min_ratio_idx]
            ))
            crop_size = tuple(crop_size)
            img_width, img_height = image.size

            image2 = image.crop((
                (img_width - crop_size[0]) // 2,
                (img_height - crop_size[1]) // 2,
                (img_width + crop_size[0]) // 2,
                (img_height + crop_size[1]) // 2
            ))
            image3 = image2.resize(self.output_image_size)

            # show the image
            # image3.show()

            imarr = np.asarray(image3)

            try:
                if np.shape(imarr)[2] != 3:
                    image4 = image3.convert('RGB')
                    imarr = np.asarray(image4)
                self.images_dict[image_name] = imarr
            except IndexError:
                # GIFs Mislabeled
                raise FailedLoadError(f"Bad Image Format: {image_name}")
        except FileNotFoundError:
            raise
        except OSError as e:
            raise FailedLoadError(
                f"Unexpected OSError: {image_name}\n{str(e)}")

    def add_images(self, images, show_progress=True):
        if progress and show_progress:
            pb = progress.ProgressBar([{'align': 'right'}, {}])
            pb.refresh(0, "0%")

        for i in range(len(images)):
            image_name = os.path.basename(images[i])
            if '?' in image_name:
                image_name = image_name[:image_name.find('?')]

            if progress and show_progress:
                pb.refresh(
                    i/len(images),
                    [
                        f"{int(i/len(images) * 100):d}%",
                        f"{i}/{len(images)} {image_name}"
                    ]
                )

            filepath = images[i]

            if image_name in self.images_dict:
                continue
            try:
                self.add_image(filepath)
            except FailedLoadError as e:
                if progress and show_progress:
                    pb.print(str(e))
                else:
                    print(str(e))
            if i % 100 == 0:
                self.save()

        if show_progress:
            if progress:
                pb.refresh(100, ["100%", "Done!"])
            else:
                print("Done!")

        self.save()

    def save(self):
        np.save(self.output_file, self.images_dict)


if __name__ == '__main__':
    main()
