import argparse
import json
import os
import pdb
import requests
import time

import import_image

URL = 'https://api.pexels.com/v1/search'


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
        '-o', '--output',
        dest='output_file',
        default='images.npy',
        help="Output npy file path."
    )
    parser.add_argument(
        '-n',
        dest='number_images',
        default=1600,
        type=int,
        help="Number of images to get from pexels."
    )
    args = parser.parse_args()

    token_path = os.path.join(os.path.dirname(__file__), 'pexels_api_key')
    with open(token_path, 'r') as token_file:
        token = token_file.read().strip()

    try:
        with open(f"{args.output_file}.json", 'r') as requests_file:
            requests_list = json.loads(requests_file.read()) or []
    except FileNotFoundError:
        requests_list = []
    # pdb.set_trace()

    output_image_size = (args.width, args.height)

    get_data(
        token,
        requests_list,
        args.output_file,
        output_image_size,
        args.number_images)


def get_data(
        token,
        requests_list,
        output_file,
        output_image_size,
        number_images):

    importImage = import_image.ImportImage(output_file, output_image_size)

    imageCount = 0

    for request_result in requests_list:
        images = [p['src']['small'] for p in request_result['photos']]
        imageCount += len(images)
        importImage.add_images(images, show_progress=False)
        if imageCount > 10000:
            return

    while True:
        headers = {"Authorization": token}
        if not requests_list:
            url = URL
            params = {
                'page': 1,
                'query': 'Nature',
                'size': 'small',
                'per_page': 80,
            }
        else:
            url = requests_list[-1]['next_page']
            params = {}
        response = requests.get(url, headers=headers, params=params)
        requests_list.append(response.json())

        with open(f"{output_file}.json", 'w') as f:
            f.write(json.dumps(requests_list))

        images = [p['src']['small'] for p in response.json()['photos']]
        imageCount += len(images)
        importImage.add_images(images, show_progress=False)
        if imageCount > number_images:
            return


if __name__ == '__main__':
    main()
