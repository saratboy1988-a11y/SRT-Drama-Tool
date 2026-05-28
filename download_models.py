# -*- coding: utf-8 -*-
"""
RVC Model Downloader
Download RVC voice models from various sources
"""

import os
import sys
import urllib.request
import zipfile
import hashlib
import json
from pathlib import Path


# Default models directory
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rvc_models")


def create_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"✓ Models directory: {MODELS_DIR}")


def download_file(url, dest, show_progress=True):
    """
    Download a file from URL with progress bar.
    
    Args:
        url: Download URL
        dest: Destination file path
        show_progress: Show progress bar (default: True)
    """
    try:
        def progress_hook(count, block_size, total_size):
            if show_progress and total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                downloaded = count * block_size / (1024 * 1024)  # MB
                total = total_size / (1024 * 1024)  # MB
                bar_length = 40
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f'\r  Progress: [{bar}] {percent}% ({downloaded:.1f}/{total:.1f} MB)', end='', flush=True)
        
        urllib.request.urlretrieve(url, dest, progress_hook)
        if show_progress:
            print()  # New line after progress
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def extract_zip(zip_path, extract_to):
    """
    Extract a ZIP file.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Destination directory
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Extracted to: {extract_to}")
        return True
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return False


def calculate_md5(file_path):
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def download_model(name, url, expected_md5=None):
    """
    Download and extract an RVC model.
    
    Args:
        name: Model name
        url: Download URL
        expected_md5: Expected MD5 hash for verification (optional)
    """
    print(f"\n{'='*60}")
    print(f"Downloading: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    # Create model directory
    model_dir = os.path.join(MODELS_DIR, name.replace(" ", "_"))
    os.makedirs(model_dir, exist_ok=True)
    
    # Download ZIP
    zip_filename = os.path.basename(url)
    if not zip_filename.endswith('.zip'):
        zip_filename = f"{name.replace(' ', '_')}.zip"
    
    zip_path = os.path.join(MODELS_DIR, zip_filename)
    
    print("\nDownloading...")
    if not download_file(url, zip_path):
        return False
    
    # Verify MD5 if provided
    if expected_md5:
        print("Verifying file integrity...")
        actual_md5 = calculate_md5(zip_path)
        if actual_md5 != expected_md5:
            print(f"✗ MD5 mismatch! Expected: {expected_md5}, Got: {actual_md5}")
            return False
        print(f"✓ MD5 verified: {actual_md5}")
    
    # Extract ZIP
    print("\nExtracting...")
    if not extract_zip(zip_path, model_dir):
        return False
    
    # Clean up ZIP
    try:
        os.remove(zip_path)
        print("✓ Cleaned up ZIP file")
    except Exception:
        pass
    
    print(f"\n✓ Model '{name}' downloaded successfully!")
    print(f"  Location: {model_dir}")
    return True


def download_from_huggingface(repo_id, filename, token=None):
    """
    Download a model from Hugging Face.
    
    Args:
        repo_id: Hugging Face repository ID (e.g., "user/model-name")
        filename: Filename to download
        token: Hugging Face token (optional, for private repos)
    """
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    if token:
        # Add token to request header for private repos
        print(f"Downloading from private repo: {repo_id}")
    
    model_name = repo_id.split('/')[-1]
    return download_file_with_header(
        url, 
        model_name,
        headers={"Authorization": f"Bearer {token}"} if token else None
    )


def download_file_with_header(url, name, headers=None):
    """Download a file with custom headers."""
    model_dir = os.path.join(MODELS_DIR, name.replace(" ", "_"))
    os.makedirs(model_dir, exist_ok=True)
    
    zip_path = os.path.join(MODELS_DIR, f"{name.replace(' ', '_')}.zip")
    
    try:
        req = urllib.request.Request(url)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        print(f"\n{'='*60}")
        print(f"Downloading: {name}")
        print(f"{'='*60}\n")
        
        with urllib.request.urlopen(req) as response:
            total_size = int(response.getheader('Content-Length', 0))
            
            with open(zip_path, 'wb') as out_file:
                downloaded = 0
                block_size = 8192
                
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    out_file.write(buffer)
                    downloaded += len(buffer)
                    
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        bar_length = 40
                        filled = int(bar_length * percent / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f'\r  Progress: [{bar}] {percent}%', end='', flush=True)
                
                print()
        
        # Extract
        extract_zip(zip_path, model_dir)
        
        # Clean up
        try:
            os.remove(zip_path)
        except Exception:
            pass
        
        print(f"\n✓ Downloaded: {name}")
        return True
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def list_downloaded_models():
    """List all downloaded models."""
    print(f"\n{'='*60}")
    print("Downloaded Models:")
    print(f"{'='*60}")
    
    if not os.path.exists(MODELS_DIR):
        print("No models directory found.")
        return []
    
    models = []
    for item in os.listdir(MODELS_DIR):
        item_path = os.path.join(MODELS_DIR, item)
        if os.path.isdir(item_path):
            models.append(item)
            print(f"  ✓ {item}")
    
    if not models:
        print("  (No models downloaded yet)")
    
    return models


def save_models_list(models_list):
    """Save models list to JSON file."""
    models_file = os.path.join(MODELS_DIR, "models_list.json")
    with open(models_file, 'w', encoding='utf-8') as f:
        json.dump(models_list, f, indent=2, ensure_ascii=False)
    print(f"✓ Models list saved to: {models_file}")


def load_models_list():
    """Load models list from JSON file."""
    models_file = os.path.join(MODELS_DIR, "models_list.json")
    if os.path.exists(models_file):
        with open(models_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"models": []}


def main():
    """Main function with CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="RVC Model Downloader - Download voice models for RVC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a model from URL
  python download_models.py --url "https://example.com/model.zip" --name "My Voice Model"
  
  # Download from Hugging Face
  python download_models.py --huggingface "user/repo" --file "model.zip"
  
  # List downloaded models
  python download_models.py --list
  
  # Download with MD5 verification
  python download_models.py --url "https://example.com/model.zip" --name "Model" --md5 "abc123..."
        """
    )
    
    parser.add_argument('--url', type=str, help='Direct download URL for model ZIP file')
    parser.add_argument('--name', type=str, help='Name for the downloaded model')
    parser.add_argument('--md5', type=str, help='Expected MD5 hash for verification')
    parser.add_argument('--huggingface', type=str, help='Hugging Face repository ID (e.g., user/model-name)')
    parser.add_argument('--file', type=str, help='Filename to download from Hugging Face')
    parser.add_argument('--token', type=str, help='Hugging Face token (for private repos)')
    parser.add_argument('--list', action='store_true', help='List all downloaded models')
    
    args = parser.parse_args()

    # Create directories
    create_directories()
    
    # List models
    if args.list:
        list_downloaded_models()
        return
    
    # Download from direct URL
    if args.url:
        if not args.name:
            args.name = "Downloaded_Model_" + str(int(time.time()))
        success = download_model(args.name, args.url, args.md5)
        sys.exit(0 if success else 1)
    
    # Download from Hugging Face
    if args.huggingface:
        if not args.file:
            print("✗ Error: --file is required when using --huggingface")
            sys.exit(1)
        success = download_from_huggingface(args.huggingface, args.file, args.token)
        sys.exit(0 if success else 1)
    
    # If no arguments provided, show help
    if not any([args.url, args.huggingface, args.list]):
        parser.print_help()


if __name__ == "__main__":
    import time
    main()
