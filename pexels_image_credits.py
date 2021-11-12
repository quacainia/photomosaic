import argparse
import json


parser = argparse.ArgumentParser(
    "Given an image list, outputs list of photographers and IDs for Pexels "
    "sourced images")

parser.add_argument(
    'used_images_list',
    help="Text file of used images."
)

parser.add_argument(
    'pexels_query_list',
    help="JSON file with an array of the response objects from Pexels queries."
)

parser.add_argument(
    '-o', '--output',
    dest='output_file',
    help="Output file name."
)

args = parser.parse_args()

with open(args.used_images_list, 'r') as f:
    photos = f.readlines()

with open(args.pexels_query_list, 'r') as requests_file:
    requests_list = json.loads(requests_file.read()) or []

new_lines = []

for photo in photos:
    photo = photo.strip()
    for request_result in requests_list:
        for photo_dict in request_result['photos']:
            if photo in photo_dict['src']['original']:
                new_lines.append((photo, photo_dict))
                author = 1
                break
        else:
            continue
        break

output_file_name = args.output_file
if not output_file_name:
    if 'used' in args.used_images_list:
        output_file_name = args.used_images_list.replace('used', 'pexels')
    else:
        output_file_name = args.used_images_list+'.pexels.txt'

with open(output_file_name, 'w') as f:
    for (photo, photo_dict) in new_lines:
        f.write(
            f"{photo_dict['id']} {photo} {photo_dict['photographer']} "
            f"{photo_dict['photographer_id']}\n"
        )
