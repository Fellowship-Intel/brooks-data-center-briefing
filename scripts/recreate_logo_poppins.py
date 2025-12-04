"""
Script to recreate logo with Poppins font text while preserving background and icon.
Uses the original source file and replaces only the text.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import sys

def download_poppins_font(weight: str = "Regular", output_dir: Path = None):
    """
    Download Poppins font from Google Fonts if not found locally.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "static" / "fonts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    font_file = output_dir / f"Poppins-{weight}.ttf"
    
    if font_file.exists():
        return font_file
    
    try:
        import requests
        
        # Google Fonts API URL for Poppins
        weight_map = {
            "Regular": "regular",
            "Bold": "700",
            "SemiBold": "600",
        }
        weight_param = weight_map.get(weight, "regular")
        
        url = f"https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-{weight}.ttf"
        
        print(f"   📥 Downloading Poppins-{weight} from Google Fonts...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            with open(font_file, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Downloaded Poppins-{weight}.ttf")
            return font_file
        else:
            # Try alternative URL
            url2 = f"https://fonts.google.com/download?family=Poppins"
            print(f"   ⚠️  Direct download failed, please install Poppins manually")
            return None
    except Exception as e:
        print(f"   ⚠️  Could not download Poppins: {e}")
        return None

def get_poppins_font(size: int, weight: str = "Regular"):
    """
    Try to load Poppins font from various locations, download if needed.
    Returns font object or None if not found.
    """
    font_paths = [
        f"C:/Windows/Fonts/Poppins-{weight}.ttf",
        f"C:/Windows/Fonts/poppins-{weight.lower()}.ttf",
        f"/usr/share/fonts/truetype/poppins/Poppins-{weight}.ttf",
        f"/System/Library/Fonts/Supplemental/Poppins-{weight}.ttf",
    ]
    
    # Check local fonts directory
    local_fonts = Path(__file__).parent.parent / "static" / "fonts"
    if local_fonts.exists():
        font_paths.insert(0, str(local_fonts / f"Poppins-{weight}.ttf"))
    
    # Also try common variations
    weight_variations = {
        "Regular": ["Regular", "normal", ""],
        "Bold": ["Bold", "bold"],
        "SemiBold": ["SemiBold", "Semibold", "Semi-Bold"],
    }
    
    for path_template in font_paths:
        variations = weight_variations.get(weight, [weight])
        for var in variations:
            if var:
                path = path_template.replace(weight, var) if weight in path_template else path_template
            else:
                path = path_template.replace(f"-{weight}", "").replace(f"-{weight.lower()}", "")
            
            path_obj = Path(path)
            if path_obj.exists():
                try:
                    return ImageFont.truetype(str(path_obj), size)
                except:
                    continue
    
    # Try to find any Poppins font in Windows Fonts directory
    try:
        font_dir = Path("C:/Windows/Fonts")
        if font_dir.exists():
            poppins_files = list(font_dir.glob("Poppins*.ttf")) + list(font_dir.glob("poppins*.ttf"))
            if poppins_files:
                return ImageFont.truetype(str(poppins_files[0]), size)
    except:
        pass
    
    # Try to download if not found
    downloaded_font = download_poppins_font(weight)
    if downloaded_font and downloaded_font.exists():
        try:
            return ImageFont.truetype(str(downloaded_font), size)
        except:
            pass
    
    return None

def find_text_regions_precise(img_array, preserve_icon=True):
    """
    More precise method to find text regions while preserving icon and background.
    """
    alpha_channel = img_array[:, :, 3]
    rgb_channels = img_array[:, :, :3]
    
    brightness = np.mean(rgb_channels, axis=2)
    color_std = np.std(rgb_channels, axis=2)
    
    # Identify gray background (typically medium brightness, low variation)
    background_mask = (
        (alpha_channel > 0) &
        (brightness > 100) &
        (brightness < 180) &
        (color_std < 20)  # Very uniform = background
    )
    
    # Identify icon (has color variation or specific patterns)
    icon_mask = (
        (alpha_channel > 0) &
        (
            (color_std > 35) |  # High color variation
            (brightness > 220) |  # Very bright (highlights)
            (brightness < 50)  # Very dark (shadows)
        )
    )
    
    # Text is everything else that's not background or icon
    text_mask = (
        (alpha_channel > 0) &
        (~background_mask) &
        (~icon_mask) &
        (brightness > 80) &  # Not too dark
        (brightness < 240)  # Not too bright
    )
    
    return text_mask, background_mask, icon_mask

def recreate_logo_with_poppins(source_path: Path, output_path: Path, 
                                text_lines: list = None, text_positions: list = None):
    """
    Recreate logo with Poppins font text.
    
    Args:
        source_path: Original logo file
        output_path: Output path for new logo
        text_lines: List of text strings to render (e.g., ["Fellowship", "Intelligence"])
        text_positions: List of (x, y, font_size) tuples for each text line
    """
    try:
        print(f"📖 Reading source logo from: {source_path}")
        original_img = Image.open(source_path)
        
        if original_img.mode != 'RGBA':
            original_img = original_img.convert('RGBA')
        
        print(f"   Image size: {original_img.width}x{original_img.height}px")
        
        # Convert to numpy for analysis
        img_array = np.array(original_img)
        alpha_channel = img_array[:, :, 3]
        rgb_channels = img_array[:, :, :3]
        
        # Find regions
        print("🔍 Analyzing image regions...")
        text_mask, background_mask, icon_mask = find_text_regions_precise(img_array)
        
        # If text_lines not provided, try to infer from filename or use defaults
        if text_lines is None:
            # Try to infer from filename
            filename = source_path.stem.lower()
            if "fellowship" in filename and "intelligence" in filename:
                text_lines = ["Fellowship", "Intelligence"]
            else:
                text_lines = ["Fellowship", "Intelligence"]  # Default
        
        # If positions not provided, estimate from text mask
        if text_positions is None:
            coords = np.where(text_mask)
            if len(coords[0]) > 0:
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                
                # Estimate positions for two lines of text
                text_height = y_max - y_min
                center_x = (x_min + x_max) // 2
                
                if len(text_lines) == 2:
                    # Two lines: top and bottom
                    top_y = y_min + text_height // 4
                    bottom_y = y_min + 3 * text_height // 4
                    font_size = max(24, text_height // 3)
                    
                    text_positions = [
                        (center_x, top_y, font_size),
                        (center_x, bottom_y, font_size),
                    ]
                else:
                    # Single line
                    center_y = (y_min + y_max) // 2
                    font_size = max(24, text_height // 2)
                    text_positions = [(center_x, center_y, font_size)]
            else:
                # Fallback: center of image
                center_x = original_img.width // 2
                if len(text_lines) == 2:
                    text_positions = [
                        (center_x, original_img.height // 3, 40),
                        (center_x, 2 * original_img.height // 3, 40),
                    ]
                else:
                    text_positions = [(center_x, original_img.height // 2, 40)]
        
        print(f"📝 Rendering {len(text_lines)} text line(s) in Poppins font...")
        
        # Start with original image
        new_img = original_img.copy()
        
        # First, erase old text regions by restoring background color
        print("🧹 Removing old text...")
        img_array_new = np.array(new_img)
        rgb_channels_new = img_array_new[:, :, :3]
        
        # Find the background gray color (most common color in background mask)
        if np.any(background_mask):
            bg_pixels = rgb_channels_new[background_mask]
            if len(bg_pixels) > 0:
                bg_color = np.median(bg_pixels, axis=0).astype(int)
            else:
                # Fallback: use a medium gray
                bg_color = np.array([128, 128, 128])
        else:
            bg_color = np.array([128, 128, 128])  # Default gray
        
        # Replace text regions with background color
        img_array_new[text_mask, 0] = bg_color[0]
        img_array_new[text_mask, 1] = bg_color[1]
        img_array_new[text_mask, 2] = bg_color[2]
        # Keep alpha channel
        
        new_img = Image.fromarray(img_array_new)
        draw = ImageDraw.Draw(new_img)
        
        # Render each text line
        for i, (text, (x, y, font_size)) in enumerate(zip(text_lines, text_positions)):
            # Try to get Poppins font
            font_weight = "SemiBold" if i == 0 else "Regular"
            font = get_poppins_font(font_size, font_weight)
            
            if font is None:
                print(f"   ⚠️  Poppins font not found for line {i+1}, trying clean sans-serif alternatives...")
                # Try clean sans-serif alternatives
                fallback_fonts = [
                    "C:/Windows/Fonts/calibri.ttf",
                    "C:/Windows/Fonts/segoeui.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                ]
                font = None
                for fallback in fallback_fonts:
                    if Path(fallback).exists():
                        try:
                            font = ImageFont.truetype(fallback, font_size)
                            print(f"   ✅ Using fallback font: {Path(fallback).name}")
                            break
                        except:
                            continue
                
                if font is None:
                    font = ImageFont.load_default()
                    print(f"   ⚠️  Using default system font")
            else:
                print(f"   ✅ Using Poppins-{font_weight} for: '{text}'")
            
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height_actual = bbox[3] - bbox[1]
            
            # Calculate position (x, y is center point)
            text_x = x - text_width // 2
            text_y = y - text_height_actual // 2
            
            # Draw white text
            draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
        
        # Apply sharpening for crisp text
        print("✨ Applying sharpening for crisp text...")
        new_img = new_img.filter(ImageFilter.SHARPEN)
        new_img = new_img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Sharpness(new_img)
        new_img = enhancer.enhance(2.5)
        
        # Save
        new_img.save(output_path, 'PNG', optimize=True)
        print(f"✅ Enhanced logo saved to: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing logo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    source_path = project_root / "static" / "images" / "Fellowship Intelligence for App.png"
    output_path = project_root / "static" / "images" / "logo.png"
    
    if not source_path.exists():
        print(f"❌ Source file not found: {source_path}")
        print("   Looking for: Fellowship Intelligence for App.png")
        sys.exit(1)
    
    # Create backup of current logo
    if output_path.exists():
        backup_path = output_path.with_suffix('.png.backup4')
        try:
            import shutil
            shutil.copy2(output_path, backup_path)
            print(f"📋 Backed up current logo to: {backup_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Recreate logo with Poppins text
    # You can customize these:
    text_lines = ["Fellowship", "Intelligence"]
    text_positions = None  # Will be auto-detected, or specify: [(x1, y1, size1), (x2, y2, size2)]
    
    success = recreate_logo_with_poppins(
        source_path, 
        output_path,
        text_lines=text_lines,
        text_positions=text_positions
    )
    
    if success:
        print()
        print("=" * 60)
        print("✅ Logo recreation complete!")
        print("=" * 60)
        print("Text has been rendered in Poppins font (stark white).")
        print("Background (gray) and icon have been preserved.")
        print("Restart your Streamlit app to see the changes.")
    else:
        print()
        print("=" * 60)
        print("❌ Logo recreation failed")
        print("=" * 60)
        sys.exit(1)

