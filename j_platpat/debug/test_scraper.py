#!/usr/bin/env python3
"""
Local testing script for j-platpat scraper

Usage:
    python test_scraper.py
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lambda_function import scrape_j_platpat, detect_new_patents


async def main():
    """Test the scraper locally"""
    print("=" * 60)
    print("j-platpat Scraper - Local Test")
    print("=" * 60)

    # Scrape current data
    print("\n[1/3] Scraping j-platpat...")
    print("-" * 60)

    try:
        patents = await scrape_j_platpat()
        print(f"✓ Scraping successful: {len(patents)} patents found")

        if patents:
            print("\nSample data (first 3 patents):")
            for i, patent in enumerate(patents[:3], 1):
                print(f"\n  Patent {i}:")
                print(f"    出願番号: {patent.get('app_num', 'N/A')}")
                print(f"    発明の名称: {patent.get('inven_name', 'N/A')}")
                print(f"    出願人: {patent.get('applicant', 'N/A')}")
                print(f"    ステータス: {patent.get('status', 'N/A')}")

    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test difference detection
    print("\n[2/3] Testing difference detection...")
    print("-" * 60)

    # Simulate previous state (remove first patent)
    if len(patents) > 1:
        previous_patents = patents[1:]
        new_patents = detect_new_patents(previous_patents, patents)
        print(f"✓ Difference detection successful")
        print(f"  Previous: {len(previous_patents)} patents")
        print(f"  Current: {len(patents)} patents")
        print(f"  New: {len(new_patents)} patent(s)")

        if new_patents:
            print(f"\n  Detected new patent:")
            for patent in new_patents:
                print(f"    出願番号: {patent.get('app_num')}")
                print(f"    発明の名称: {patent.get('inven_name')}")
    else:
        print("⚠ Not enough patents to test difference detection")

    # Save data to JSON for inspection
    print("\n[3/3] Saving data to file...")
    print("-" * 60)

    output_file = Path(__file__).parent / "scraped_patents.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(patents, f, ensure_ascii=False, indent=2)
        print(f"✓ Data saved to {output_file}")
    except Exception as e:
        print(f"✗ Failed to save data: {e}")
        return False

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
