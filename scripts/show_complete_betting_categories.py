#!/usr/bin/env python3
"""
Display complete breakdown of all 60+ betting categories
Shows the comprehensive coverage for a popular NFL betting site
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ml.prediction_engine.complete_betting_categories import get_complete_betting_categories, AccessTier

def display_complete_categories():
    """Display all betting categories organized by group and tier"""
    categories = get_complete_betting_categories()
    summary = categories.get_category_summary()

    print("🏈 COMPLETE NFL BETTING CATEGORIES SYSTEM")
    print("=" * 60)
    print(f"Total Categories: {summary['total_categories']}")
    print(f"Popular Categories (7+ rating): {summary['popular_categories']}")
    print(f"Live Data Categories: {summary['live_data_categories']}")
    print()

    # Monetization Breakdown
    print("💰 MONETIZATION TIERS:")
    print("-" * 30)
    for tier, count in summary['monetization_split'].items():
        percentage = (count / summary['total_categories']) * 100
        print(f"{tier.upper()}: {count} categories ({percentage:.1f}%)")
    print()

    # Categories by Group
    print("📊 CATEGORIES BY GROUP:")
    print("-" * 30)

    for group_name, count in summary['categories_by_group'].items():
        print(f"\n{group_name.upper().replace('_', ' ')} ({count} categories):")
        group_categories = [cat for cat in categories.categories.values()
                          if cat.group.value == group_name]

        # Sort by popularity score
        group_categories.sort(key=lambda x: x.popularity_score, reverse=True)

        for cat in group_categories:
            tier_icon = "🆓" if cat.access_tier == AccessTier.FREE else "💎" if cat.access_tier == AccessTier.PRO else "👑"
            popularity = "⭐" * min(cat.popularity_score, 5)  # Max 5 stars for display
            print(f"  {tier_icon} {cat.category_name} {popularity} ({cat.popularity_score}/10)")

    print("\n" + "=" * 60)
    print("🎯 COVERAGE ANALYSIS:")
    print("-" * 30)

    # Popular betting lines coverage
    popular_cats = categories.get_popular_categories(7)
    free_popular = len([cat for cat in popular_cats if cat.access_tier == AccessTier.FREE])

    print(f"✅ Covers ALL major betting lines")
    print(f"✅ {free_popular} popular categories are FREE")
    print(f"✅ {len(categories.get_pro_categories())} PRO categories for monetization")
    print(f"✅ {len(categories.get_premium_categories())} PREMIUM live betting features")
    print(f"✅ Suitable for both casual and professional bettors")

    print("\n🚀 RECOMMENDED IMPLEMENTATION:")
    print("-" * 30)
    print("1. Launch with FREE tier (core betting lines)")
    print("2. PRO tier ($9.99/month) - Advanced props & analysis")
    print("3. PREMIUM tier ($19.99/month) - Live betting + all features")
    print("4. Focus on high-popularity categories first")
    print("5. Add live data integration for real-time props")

if __name__ == "__main__":
    display_complete_categories()
