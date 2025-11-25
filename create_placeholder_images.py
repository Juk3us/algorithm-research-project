#!/usr/bin/env python3
"""
Create placeholder images for the three Toyo Ito buildings
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, title, dimensions, color):
    """Create a placeholder image with text"""

    # Create image with specified color
    img = Image.new('RGB', (1200, 800), color=color)
    draw = ImageDraw.Draw(img)

    # Try to use a decent font, fall back to default if not available
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_dim = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_dim = ImageFont.load_default()

    # Add title text (centered)
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (1200 - title_width) // 2
    title_y = 300

    draw.text((title_x, title_y), title, fill='white', font=font_title)

    # Add dimensions text (centered below title)
    dim_text = f"{dimensions}"
    dim_bbox = draw.textbbox((0, 0), dim_text, font=font_dim)
    dim_width = dim_bbox[2] - dim_bbox[0]
    dim_x = (1200 - dim_width) // 2
    dim_y = title_y + title_height + 40

    draw.text((dim_x, dim_y), dim_text, fill='white', font=font_dim)

    # Save image
    img.save(filename, 'JPEG', quality=85)
    print(f"✓ Created: {filename}")

# Create images directory
os.makedirs('images', exist_ok=True)

# Create placeholder images for each building
create_placeholder_image(
    'images/sendai-mediatheque.jpg',
    'Sendai Mediatheque',
    'Toyo Ito, 2001',
    (52, 73, 94)  # Dark blue-gray
)

create_placeholder_image(
    'images/taichung-opera.jpg',
    'Taichung Opera House',
    'Toyo Ito, 2016',
    (44, 62, 80)  # Darker blue-gray
)

create_placeholder_image(
    'images/tods-omotesando.jpg',
    "TOD'S Omotesando",
    'Toyo Ito, 2004',
    (41, 128, 185)  # Blue
)

print("\nAll placeholder images created successfully!")
