#!/usr/bin/env python
"""Test script to verify imports work"""
import sys

print("Testing imports...")

try:
    import google.generativeai
    print("✓ google.generativeai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google.generativeai: {e}")
    print("Please install it with: python -m pip install google-generativeai")
    sys.exit(1)

try:
    from python_app.types import InputData
    print("✓ python_app.types imported successfully")
except ImportError as e:
    print(f"✗ Failed to import python_app.types: {e}")
    sys.exit(1)

print("\nAll imports successful!")

