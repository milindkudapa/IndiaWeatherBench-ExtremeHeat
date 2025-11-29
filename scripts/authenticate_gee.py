#!/usr/bin/env python3
"""
Interactive authentication for Google Earth Engine.
Run this script interactively to authenticate.
"""

import ee

print("=" * 80)
print("Google Earth Engine Authentication")
print("=" * 80)
print()
print("This script will help you authenticate with Google Earth Engine.")
print("You'll need to:")
print("  1. Open a URL in your web browser")
print("  2. Sign in with your Google account")
print("  3. Copy the authorization code")
print("  4. Paste it here")
print()
print("=" * 80)
print()

try:
    # Try to authenticate
    ee.Authenticate(auth_mode='notebook')
    print()
    print("✓ Authentication successful!")
    print()
    
    # Test initialization
    print("Testing Earth Engine access...")
    ee.Initialize()
    print("✓ Earth Engine initialized successfully!")
    print()
    
    # Test ERA5-Land access
    print("Testing ERA5-Land dataset access...")
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    test = dataset.filterDate('2000-01-01', '2000-01-02').first()
    bands = test.bandNames().getInfo()
    print(f"✓ ERA5-Land accessible! ({len(bands)} bands available)")
    print()
    
    print("=" * 80)
    print("SUCCESS! You're ready to download ERA5-Land data.")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Authentication failed: {e}")
    print()
    print("Troubleshooting:")
    print("  - Make sure you're signed in with the correct Google account")
    print("  - Ensure you have access to Google Earth Engine")
    print("  - Try signing up at: https://earthengine.google.com/signup")
    print()

