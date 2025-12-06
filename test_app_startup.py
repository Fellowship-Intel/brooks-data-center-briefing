#!/usr/bin/env python
"""Test script to diagnose app startup issues."""
import sys
import os
import traceback

# Set environment
os.environ["ENVIRONMENT"] = "development"

print("Testing app imports and startup...")
print("=" * 60)

try:
    print("1. Testing basic imports...")
    import streamlit as st
    print("   ✓ Streamlit imported")
    
    import pandas as pd
    print("   ✓ Pandas imported")
    
    from config import get_config
    print("   ✓ Config imported")
    
    config = get_config()
    print(f"   ✓ Config loaded: port={config.port}, env={config.environment}")
    
except Exception as e:
    print(f"   ✗ Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing app.py imports...")
    import app
    print("   ✓ app.py imported successfully")
except Exception as e:
    print(f"   ✗ app.py import error: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing main() function...")
    # Don't actually call main() as it requires Streamlit runtime
    print("   ✓ main() function exists")
    print(f"   ✓ main function: {app.main}")
except Exception as e:
    print(f"   ✗ Error checking main(): {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("All checks passed! App should start successfully.")
print("=" * 60)


