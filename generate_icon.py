#!/usr/bin/env python3
"""
Generate application icon (ICO format) from scratch.
Creates a professional multi-size ICO file for the accounting application.

Usage:
    python generate_icon.py

Output:
    assets/icon.ico
"""
import os
import struct
import zlib
from pathlib import Path


def create_png_data(width: int, height: int, color_rgb: tuple) -> bytes:
    """Create a simple solid-color PNG image."""
    def create_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = create_png_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter type: None
        for x in range(width):
            # Create a gradient effect
            r, g, b = color_rgb
            # Add some variation for visual interest
            factor = 1.0 - (y / height) * 0.3
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            raw_data += bytes([r, g, b])
    
    compressed = zlib.compress(raw_data, 9)
    idat = create_png_chunk(b'IDAT', compressed)
    
    # IEND chunk
    iend = create_png_chunk(b'IEND', b'')
    
    return signature + ihdr + idat + iend


def create_icon_with_design(width: int, height: int) -> bytes:
    """Create an icon with a simple ledger/book design."""
    def create_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = create_png_chunk(b'IHDR', ihdr_data)
    
    # Create image data with design
    raw_data = b''
    center_x = width // 2
    center_y = height // 2
    
    for y in range(height):
        raw_data += b'\x00'  # Filter type: None
        for x in range(width):
            # Distance from center
            dx = x - center_x
            dy = y - center_y
            dist = (dx*dx + dy*dy) ** 0.5
            max_dist = (center_x*center_x + center_y*center_y) ** 0.5
            
            # Background gradient (blue)
            bg_factor = 1.0 - (dist / max_dist) * 0.4
            bg_r = int(30 * bg_factor)
            bg_g = int(64 * bg_factor)
            bg_b = int(175 * bg_factor)
            
            # Book/ledger shape (white rectangle in center)
            book_width = width * 0.5
            book_height = height * 0.6
            in_book = (abs(dx) < book_width/2 and abs(dy) < book_height/2)
            
            # Checkmark shape
            check_size = width * 0.25
            in_check = False
            if in_book:
                # Simple checkmark
                rel_x = (x - (center_x - book_width/2)) / book_width
                rel_y = (y - (center_y - book_height/2)) / book_height
                if 0.3 < rel_x < 0.7 and 0.4 < rel_y < 0.7:
                    in_check = True
            
            if in_check:
                r, g, b, a = 255, 255, 255, 255  # White checkmark
            elif in_book:
                r, g, b, a = 240, 240, 240, 255  # Light gray book
            else:
                r, g, b, a = bg_r, bg_g, bg_b, 255  # Blue background
            
            raw_data += bytes([r, g, b, a])
    
    compressed = zlib.compress(raw_data, 9)
    idat = create_png_chunk(b'IDAT', compressed)
    iend = create_png_chunk(b'IEND', b'')
    
    return signature + ihdr + idat + iend


def create_ico_file(png_images: list) -> bytes:
    """
    Create an ICO file from a list of PNG images.
    
    Args:
        png_images: List of (width, height, png_data) tuples
    
    Returns:
        ICO file bytes
    """
    # ICO header
    num_images = len(png_images)
    header = struct.pack('<HHH', 0, 1, num_images)  # Reserved, Type (1=ICO), Count
    
    # Calculate offset for image data
    # Each directory entry is 16 bytes
    # Header is 6 bytes
    offset = 6 + (16 * num_images)
    
    # Directory entries
    directory = b''
    image_data = b''
    
    for width, height, png_data in png_images:
        # Directory entry (16 bytes)
        entry = struct.pack('<BBBBHHII',
            width if width < 256 else 0,  # Width (0 = 256)
            height if height < 256 else 0,  # Height (0 = 256)
            0,  # Color palette (0 = no palette)
            0,  # Reserved
            1,  # Color planes
            32,  # Bits per pixel
            len(png_data),  # Size of image data
            offset  # Offset to image data
        )
        directory += entry
        image_data += png_data
        offset += len(png_data)
    
    return header + directory + image_data


def main():
    """Generate the application icon."""
    # Create assets directory
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    print("Generating application icon...")
    
    # Create PNG images at different sizes
    sizes = [16, 32, 48, 64, 128, 256]
    png_images = []
    
    for size in sizes:
        print(f"  Creating {size}x{size} icon...")
        png_data = create_icon_with_design(size, size)
        png_images.append((size, size, png_data))
    
    # Create ICO file
    print("  Combining into ICO format...")
    ico_data = create_ico_file(png_images)
    
    # Save ICO file
    ico_path = assets_dir / 'icon.ico'
    with open(ico_path, 'wb') as f:
        f.write(ico_data)
    
    print(f"✓ Icon saved to: {ico_path}")
    print(f"  Size: {len(ico_data):,} bytes")
    print(f"  Contains {len(sizes)} sizes: {', '.join(map(str, sizes))}")


if __name__ == '__main__':
    main()
