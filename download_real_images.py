#!/usr/bin/env python3
"""
Download real images of Toyo Ito buildings from Wikimedia Commons
"""

import requests
import os
from pathlib import Path

# Create images directory
Path("images").mkdir(exist_ok=True)

# Image URLs from Wikimedia Commons
images = {
    "sendai-mediatheque.jpg": "https://upload.wikimedia.org/wikipedia/commons/c/cb/Sendai_Mediatheque_2009.jpg",
    "taichung-opera.jpg": "https://upload.wikimedia.org/wikipedia/commons/f/f5/Taichung_Metropolitan_Opera_House.JPG",
    "tods-omotesando.jpg": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Tod%27s_at_Omotesando.jpg"
}

print("Downloading real images from Wikimedia Commons...")
print("=" * 60)

for filename, url in images.items():
    filepath = os.path.join("images", filename)
    print(f"\nDownloading: {filename}")
    print(f"URL: {url}")

    try:
        # Send request with user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)

        file_size = len(response.content) / 1024
        print(f"✓ Success! Saved as {filepath} ({file_size:.1f} KB)")

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {filename}: {e}")

print("\n" + "=" * 60)
print("Download complete!")
