#!/usr/bin/env python
"""Test Flask installation"""
try:
    import flask
    print("✓ Flask is installed")
    print(f"  Version: {flask.__version__}")
except ImportError as e:
    print(f"✗ Flask is NOT installed: {e}")
    print("\nTo install, run:")
    print("  python -m pip install Flask")

