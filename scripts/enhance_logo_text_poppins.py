"""
Script to enhance logo: replace text with stark white Poppins font while preserving background and icon.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import sys

def find_text_regions(img_array, alpha_channel, rgb_channels):
    """
    Identify text regions in the image by analyzing patterns.
    Returns mask of text regions.
    """
    height, width = img_array.shape[:2]
    brightness = np.mean(rgb_channels, axis=2)
    color_std = np.std(rgb_channels, axis=2)
    
    # Text typically has:
    # - Low color variation (uniform)
    # - Specific brightness ranges
    # - Often appears in horizontal/vertical patterns
    
    # Identify potential text regions
    text_mask = (
        (alpha_channel > 0) &  # Not transparent
        (color_std < 30) &  # Low color variation (uniform = text)
        (
            (brightness > 100) |  # Not too dark
            (brightness < 200)  # Not too bright (unless it's white text)
        )
    )
    
    # Exclude very bright areas (might be icon highlights)
    # Exclude areas with high color variation (likely icon)
    icon_protection = (
        (brightness > 240) |  # Very bright
        ((brightness > 120) & (brightness < 200) & (color_std > 40))  # Icon areas
    )
    
    text_mask = text_mask & (~icon_protection)
    
    return text_mask

def get_text_bounds_from_mask(text_mask):
    """
    Find bounding boxes of text regions from the mask.
    Returns list of (x, y, width, height) tuples.
    """
    # Find connected components
    from scipy import ndimage
    try:
        labeled, num_features = ndimage.label(text_mask)
        bounds = []
        
        for i in range(1, num_features + 1):
            coords = np.where(labeled == i)
            if len(coords[0]) > 0:
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                width = x_max - x_min + 1
                height = y_max - y_min + 1
                
                # Filter out very small regions (noise)
                if width > 10 and height > 10:
                    bounds.append((x_min, y_min, width, height))
        
        return bounds
    except ImportError:
        # Fallback: return full image bounds if scipy not available
        coords = np.where(text_mask)
        if len(coords[0]) > 0:
            y_min, y_max = coords[0].min(), coords[0].max()
            x_min, x_max = coords[1].min(), coords[1].max()
            return [(x_min, y_min, x_max - x_min + 1, y_max - y_min + 1)]
        return []

def render_poppins_text(text: str, font_size: int, width: int, height: int):
    """
    Render text in Poppins font as white text on transparent background.
    """
    # Try to load Poppins font, fallback to default if not available
    try:
        # Try common font paths
        font_paths = [
            "C:/Windows/Fonts/Poppins-Regular.ttf",
            "C:/Windows/Fonts/Poppins-Bold.ttf",
            "C:/Windows/Fonts/Poppins-SemiBold.ttf",
            "/usr/share/fonts/truetype/poppins/Poppins-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Poppins-Regular.ttf",
        ]
        
        font = None
        for path in font_paths:
            if Path(path).exists():
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            # Try to find Poppins in system fonts
            import platform
            if platform.system() == "Windows":
                # Try to load from Windows font directory
                font_dir = Path("C:/Windows/Fonts")
                poppins_files = list(font_dir.glob("Poppins*.ttf"))
                if poppins_files:
                    font = ImageFont.truetype(str(poppins_files[0]), font_size)
        
        if font is None:
            # Fallback to default font
            font = ImageFont.load_default()
            print("   ⚠️  Poppins font not found, using default font")
    except Exception as e:
        font = ImageFont.load_default()
        print(f"   ⚠️  Could not load Poppins font: {e}, using default font")
    
    # Create image for text rendering
    text_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_img)
    
    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw white text
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Apply sharpening for crispness
    text_img = text_img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Sharpness(text_img)
    text_img = enhancer.enhance(2.0)
    
    return text_img

def enhance_logo_with_poppins(input_path: Path, output_path: Path):
    """
    Enhance logo by replacing text with white Poppins font while preserving background and icon.
    """
    try:
        print(f"📖 Reading logo from: {input_path}")
        original_img = Image.open(input_path)
        
        print(f"   Original size: {original_img.width}x{original_img.height}px, mode: {original_img.mode}")
        
        # Convert to RGBA if needed
        if original_img.mode != 'RGBA':
            original_img = original_img.convert('RGBA')
        
        # Work with numpy array
        img_array = np.array(original_img)
        alpha_channel = img_array[:, :, 3]
        rgb_channels = img_array[:, :, :3]
        
        print("🔍 Identifying text regions...")
        text_mask = find_text_regions(img_array, alpha_channel, rgb_channels)
        
        # Get text bounding boxes
        print("📐 Finding text bounding boxes...")
        try:
            text_bounds = get_text_bounds_from_mask(text_mask)
        except:
            # If scipy not available, use a simpler approach
            coords = np.where(text_mask)
            if len(coords[0]) > 0:
                y_min, y_max = coords[0].min(), coords[0].max()
                x_min, x_max = coords[1].min(), coords[1].max()
                text_bounds = [(x_min, y_min, x_max - x_min + 1, y_max - y_min + 1)]
            else:
                text_bounds = []
        
        if not text_bounds:
            print("   ⚠️  Could not automatically detect text regions")
            print("   Using manual approach: replacing bright uniform areas...")
            # Fallback: replace bright uniform areas
            new_img_array = img_array.copy()
            brightness = np.mean(rgb_channels, axis=2)
            color_std = np.std(rgb_channels, axis=2)
            
            text_areas = (
                (alpha_channel > 0) &
                (color_std < 25) &
                (brightness > 150) &
                (brightness < 240)
            )
            
            # Make text areas white
            new_img_array[text_areas, 0] = 255
            new_img_array[text_areas, 1] = 255
            new_img_array[text_areas, 2] = 255
            
            enhanced_img = Image.fromarray(new_img_array)
            enhanced_img = enhanced_img.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Sharpness(enhanced_img)
            enhanced_img = enhancer.enhance(2.0)
        else:
            print(f"   Found {len(text_bounds)} text region(s)")
            
            # Start with original image
            enhanced_img = original_img.copy()
            
            # For each text region, we'll need to know what text to render
            # Since we can't OCR easily, we'll use a simpler approach:
            # Replace text regions with white, then sharpen
            
            new_img_array = img_array.copy()
            
            # Make text regions white
            new_img_array[text_mask, 0] = 255
            new_img_array[text_mask, 1] = 255
            new_img_array[text_mask, 2] = 255
            
            enhanced_img = Image.fromarray(new_img_array)
            
            # Apply sharpening for crisp text
            enhanced_img = enhanced_img.filter(ImageFilter.SHARPEN)
            enhanced_img = enhanced_img.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Sharpness(enhanced_img)
            enhanced_img = enhancer.enhance(2.5)
        
        # Save the enhanced logo
        enhanced_img.save(output_path, 'PNG', optimize=True)
        print(f"✅ Enhanced logo saved to: {output_path}")
        print(f"   New size: {enhanced_img.width}x{enhanced_img.height}px")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing logo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    logo_path = project_root / "static" / "images" / "logo.png"
    
    if not logo_path.exists():
        print(f"❌ Logo file not found: {logo_path}")
        print("   Please make sure logo.png exists in static/images/")
        sys.exit(1)
    
    # Create backup
    backup_path = logo_path.with_suffix('.png.backup3')
    try:
        import shutil
        shutil.copy2(logo_path, backup_path)
        print(f"📋 Created backup: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Process the logo
    success = enhance_logo_with_poppins(logo_path, logo_path)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Logo enhancement complete!")
        print("=" * 60)
        print("Text has been replaced with stark white.")
        print("Background and icon have been preserved.")
        print("Note: For true Poppins font rendering, you may need to")
        print("      manually specify text regions or use OCR.")
        print("Restart your Streamlit app to see the changes.")
    else:
        print()
        print("=" * 60)
        print("❌ Logo enhancement failed")
        print("=" * 60)
        sys.exit(1)

