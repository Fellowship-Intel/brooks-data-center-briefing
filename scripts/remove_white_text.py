"""
Script to remove large white text from the foreground of the logo image.
Preserves the background and icon.
"""
from pathlib import Path
from PIL import Image
import numpy as np
import sys

def remove_white_text(input_path: Path, output_path: Path):
    """
    Remove white text from the logo by replacing it with background color.
    """
    try:
        print(f"📖 Reading logo from: {input_path}")
        img = Image.open(input_path)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"   Image size: {img.width}x{img.height}px")
        
        # Convert to numpy array
        img_array = np.array(img)
        alpha_channel = img_array[:, :, 3]
        rgb_channels = img_array[:, :, :3]
        
        # Calculate brightness and identify white/very bright pixels
        brightness = np.mean(rgb_channels, axis=2)
        color_std = np.std(rgb_channels, axis=2)
        
        # Identify white text regions:
        # - Very bright (close to white)
        # - Low color variation (uniform white)
        # - Not transparent
        white_text_mask = (
            (alpha_channel > 0) &  # Not transparent
            (brightness > 240) &  # Very bright (white)
            (color_std < 15)  # Low color variation (uniform white)
        )
        
        # Also identify bright text that might be slightly off-white
        bright_text_mask = (
            (alpha_channel > 0) &
            (brightness > 220) &
            (brightness < 250) &
            (color_std < 20)
        )
        
        # Combine masks
        text_mask = white_text_mask | bright_text_mask
        
        if not np.any(text_mask):
            print("   ⚠️  No white text detected. Checking for other bright text patterns...")
            # Try a more aggressive approach for large text
            text_mask = (
                (alpha_channel > 0) &
                (brightness > 200) &
                (color_std < 25)
            )
        
        text_pixel_count = np.sum(text_mask)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        text_percentage = (text_pixel_count / total_pixels) * 100
        
        print(f"   Found {text_pixel_count} text pixels ({text_percentage:.1f}% of image)")
        
        if text_pixel_count == 0:
            print("   ⚠️  No text pixels found to remove")
            return False
        
        # Find background color to replace text with
        # Look for the most common non-text, non-icon color
        non_text_mask = (alpha_channel > 0) & (~text_mask)
        
        if np.any(non_text_mask):
            # Get background pixels (low color variation, medium brightness)
            bg_candidates = non_text_mask & (color_std < 25) & (brightness > 80) & (brightness < 200)
            
            if np.any(bg_candidates):
                bg_pixels = rgb_channels[bg_candidates]
                # Use median color as background
                bg_color = np.median(bg_pixels, axis=0).astype(int)
            else:
                # Fallback: use average of non-text areas
                bg_pixels = rgb_channels[non_text_mask]
                if len(bg_pixels) > 0:
                    bg_color = np.median(bg_pixels, axis=0).astype(int)
                else:
                    # Default gray background
                    bg_color = np.array([128, 128, 128])
        else:
            # Default gray background
            bg_color = np.array([128, 128, 128])
        
        print(f"   Using background color: RGB({bg_color[0]}, {bg_color[1]}, {bg_color[2]})")
        
        # Create new image array
        new_img_array = img_array.copy()
        
        # Replace white text with background color
        new_img_array[text_mask, 0] = bg_color[0]  # R
        new_img_array[text_mask, 1] = bg_color[1]  # G
        new_img_array[text_mask, 2] = bg_color[2]  # B
        # Keep alpha channel as is
        
        # Convert back to PIL Image
        new_img = Image.fromarray(new_img_array)
        
        # Save
        new_img.save(output_path, 'PNG', optimize=True)
        print(f"✅ White text removed. Saved to: {output_path}")
        
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
        sys.exit(1)
    
    # Create backup
    backup_path = logo_path.with_suffix('.png.backup5')
    try:
        import shutil
        shutil.copy2(logo_path, backup_path)
        print(f"📋 Created backup: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Remove white text
    success = remove_white_text(logo_path, logo_path)
    
    if success:
        print()
        print("=" * 60)
        print("✅ White text removal complete!")
        print("=" * 60)
        print("Large white text has been removed from the foreground.")
        print("Background and icon have been preserved.")
        print("Restart your Streamlit app to see the changes.")
    else:
        print()
        print("=" * 60)
        print("❌ White text removal failed")
        print("=" * 60)
        sys.exit(1)

