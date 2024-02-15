# %%
from tqdm import tqdm
import io
import json
import os
import requests
import time
import zipfile

NORTHSTAR_THUNDERSTORE_API_URL = (
    "https://northstar.thunderstore.io/c/northstar/api/v1/package/"
)

response = requests.get(NORTHSTAR_THUNDERSTORE_API_URL)

# Check if the request was successful (status code 200)
if response.status_code != 200:
    print(f"Error: {response.status_code}")
    assert False

data = response.json()

with open("res.json", "wt") as file:
    json.dump(data, file, indent=4)

# %%
BLACKLIST_FULLNAME = [
    "northstar-Northstar",
    "ebkr-r2modman",
    "northstar-NorthstarReleaseCandidate",
]

DOWNLOAD_LOCATION = "../thunderstore/"

filtered_data = [x for x in data if x["full_name"] not in BLACKLIST_FULLNAME]

MAX_SIZE = 100_000_000
MAX_SIZE = 10_000_000


# Stupid LLM-generated code
def convert_bytes_to_human_readable(size_in_bytes):
    # Define the units and their respective labels
    units = ["bytes", "KB", "MB", "GB", "TB"]

    # Iterate through the units
    for unit in units:
        # If the size is less than 1000, break the loop
        if size_in_bytes < 1000.0:
            break
        # Otherwise, divide the size by 1000 to convert to the next unit
        size_in_bytes /= 1000.0

    # Return the size and the corresponding unit
    return f"{size_in_bytes:.2f} {unit}"


number_of_skipped_mods = 0
number_of_mods_downloaded = 0
number_of_mods_cached = 0
for entry in tqdm(filtered_data):
    latest_version = entry["versions"][0]

    download_location = f"{DOWNLOAD_LOCATION}/{latest_version['full_name']}"  # <-- BAD does arbitrary write if malicious endpoint

    # Skip if already downloaded
    if os.path.exists(download_location):
        number_of_mods_cached += 1
        print(f"Skipping {latest_version['full_name']} as it already exists")
        continue

    # Skip mods that are too big to save bandwidth
    if latest_version["file_size"] > MAX_SIZE:
        number_of_skipped_mods += 1
        print(
            f"Skipping {latest_version['full_name']} as it's {convert_bytes_to_human_readable(latest_version['file_size'])} big"
        )
        continue

    response = requests.get(latest_version["download_url"])
    if response.status_code != 200:
        number_of_skipped_mods += 1
        print(f"Downloading {latest_version['full_name']} failed, skipping")
        continue

    with zipfile.ZipFile(io.BytesIO(response.content), "r") as zip_ref:
        # Extract all contents of the ZIP file to a directory (you can specify the directory)
        zip_ref.extractall(download_location)

    number_of_mods_downloaded += 1

    # Sleep for a second to not hammer API too much
    time.sleep(1)

# %%
print(f"Downloaded {number_of_mods_downloaded} mods")
print(f"Cached {number_of_mods_cached} mods")
print(f"Skipped {number_of_skipped_mods} mods")

assert (
    number_of_mods_downloaded + number_of_mods_cached + number_of_skipped_mods
    == len(filtered_data)
)
