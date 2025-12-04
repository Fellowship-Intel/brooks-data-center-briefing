"""
Script to download and set up a new logo from Google Drive or local file.
"""
from pathlib import Path
import requests
import shutil
import sys
from PIL import Image

def download_from_google_drive(download_url: str, output_path: Path) -> bool:
    """
    Download a file from Google Drive using a direct download link.
    
    To get a direct download link:
    1. Open the file in Google Drive
    2. Right-click and select "Get link" or "Share"
    3. Make sure it's set to "Anyone with the link can view"
    4. Copy the file ID from the URL (the long string between /d/ and /view)
    5. Use this format: https://drive.google.com/uc?export=download&id=FILE_ID
    """
    try:
        print(f"📥 Downloading logo from Google Drive...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        
        print(f"✅ Downloaded to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False

def process_logo(input_path: Path, output_path: Path, remove_background: bool = True) -> bool:
    """
    Process the logo: resize if needed and optionally remove white background.
    """
    try:
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Remove white background if requested
        if remove_background:
            print("🎨 Removing white background...")
            data = img.getdata()
            new_data = []
            threshold = 240
            for item in data:
                if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                    new_data.append((255, 255, 255, 0))  # Transparent
                else:
                    new_data.append(item)
            img.putdata(new_data)
        
        # Resize if too large (max width 400px, maintain aspect ratio)
        max_width = 400
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            print(f"📏 Resized to {max_width}x{new_height}px")
        
        # Save the processed logo
        img.save(output_path, 'PNG', optimize=True)
        print(f"✅ Processed logo saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing logo: {e}")
        return False

def setup_logo_from_local(local_path: str, remove_background: bool = True) -> bool:
    """
    Set up logo from a local file path.
    """
    project_root = Path(__file__).parent.parent
    logo_dir = project_root / "static" / "images"
    logo_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = Path(local_path)
    if not input_path.exists():
        print(f"❌ File not found: {local_path}")
        return False
    
    # Create backup of existing logo
    existing_logo = logo_dir / "logo.png"
    if existing_logo.exists():
        backup_path = logo_dir / "logo.png.backup"
        shutil.copy2(existing_logo, backup_path)
        print(f"📋 Backed up existing logo to: {backup_path}")
    
    # Process and save new logo
    output_path = logo_dir / "logo.png"
    return process_logo(input_path, output_path, remove_background)

def setup_logo_from_drive(download_url: str, remove_background: bool = True) -> bool:
    """
    Set up logo by downloading from Google Drive.
    """
    project_root = Path(__file__).parent.parent
    logo_dir = project_root / "static" / "images"
    logo_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backup of existing logo
    existing_logo = logo_dir / "logo.png"
    if existing_logo.exists():
        backup_path = logo_dir / "logo.png.backup"
        shutil.copy2(existing_logo, backup_path)
        print(f"📋 Backed up existing logo to: {backup_path}")
    
    # Download to temp file first
    temp_path = logo_dir / "logo_temp.png"
    if not download_from_google_drive(download_url, temp_path):
        return False
    
    # Process and save
    output_path = logo_dir / "logo.png"
    success = process_logo(temp_path, output_path, remove_background)
    
    # Clean up temp file
    if temp_path.exists():
        temp_path.unlink()
    
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("Logo Setup Script")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/download_and_setup_logo.py <local_file_path>")
        print("  OR")
        print("  python scripts/download_and_setup_logo.py --drive <google_drive_download_url>")
        print()
        print("To get a Google Drive download URL:")
        print("  1. Open the file in Google Drive")
        print("  2. Right-click and select 'Get link'")
        print("  3. Make sure sharing is set to 'Anyone with the link'")
        print("  4. Copy the file ID (the string between /d/ and /view)")
        print("  5. Use: https://drive.google.com/uc?export=download&id=FILE_ID")
        print()
        print("Example:")
        print("  python scripts/download_and_setup_logo.py 'C:\\Users\\You\\Downloads\\new_logo.png'")
        print("  python scripts/download_and_setup_logo.py --drive 'https://drive.google.com/uc?export=download&id=FILE_ID'")
        sys.exit(1)
    
    if sys.argv[1] == "--drive":
        if len(sys.argv) < 3:
            print("❌ Please provide a Google Drive download URL")
            sys.exit(1)
        download_url = sys.argv[2]
        success = setup_logo_from_drive(download_url)
    else:
        local_path = sys.argv[1]
        success = setup_logo_from_local(local_path)
    
    if success:
        print()
        print("=" * 60)
        print("✅ Logo setup complete!")
        print("=" * 60)
        print("The new logo will appear in your Streamlit app sidebar.")
        print("Restart your Streamlit app to see the changes.")
    else:
        print()
        print("=" * 60)
        print("❌ Logo setup failed")
        print("=" * 60)
        sys.exit(1)

