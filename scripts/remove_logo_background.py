"""
Script to remove white background from logo.png
Converts white and near-white pixels to transparent.
"""
from pathlib import Path
from PIL import Image
import sys

def remove_white_background(input_path: Path, output_path: Path, threshold: int = 240):
    """
    Remove white background from an image by making white pixels transparent.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        threshold: RGB threshold (0-255). Pixels with all RGB values above this will be made transparent.
    """
    try:
        # Open the image
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get image data
        data = img.getdata()
        
        # Create new image data with transparency
        new_data = []
        for item in data:
            # If pixel is white or near-white (all RGB values above threshold), make it transparent
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((255, 255, 255, 0))  # Transparent
            else:
                new_data.append(item)  # Keep original pixel
        
        # Update image with new data
        img.putdata(new_data)
        
        # Save the image
        img.save(output_path, 'PNG')
        print(f"✅ Successfully processed logo: {output_path}")
        print(f"   White background removed (threshold: {threshold})")
        return True
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return False

if __name__ == "__main__":
    # Get the project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    logo_path = project_root / "static" / "images" / "logo.png"
    
    if not logo_path.exists():
        print(f"❌ Logo file not found: {logo_path}")
        sys.exit(1)
    
    # Process the logo in place (backup first)
    backup_path = logo_path.with_suffix('.png.backup')
    
    # Create backup
    try:
        import shutil
        shutil.copy2(logo_path, backup_path)
        print(f"📋 Created backup: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Process the logo
    success = remove_white_background(logo_path, logo_path, threshold=240)
    
    if success:
        print(f"\n✅ Logo processed successfully!")
        print(f"   Original backed up to: {backup_path}")
        print(f"   You can delete the backup if you're happy with the result.")
    else:
        print(f"\n❌ Failed to process logo")
        sys.exit(1)

