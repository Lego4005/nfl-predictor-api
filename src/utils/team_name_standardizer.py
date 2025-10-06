#!/usr/bin/env python3
"""
Team Name Standardization Utility

Handles team name variations and provides consistent naming across the system.
"""

from typing import Dict, Optional, List
import re

class TeamNameStandardizer:
    """Standardizes NFL team names across different formats"""

    def __init__(self):
        """Initialize with comprehensivame mappings"""

        # Primary mapping: various formats -> standardized name
        self.team_mappings = {
            # Arizona Cardinals
            'ARI': 'arizona_cardinals',
            'ARIZONA': 'arizona_cardinals',
            'CARDINALS': 'arizona_cardinals',
            'arizona_cardinals': 'arizona_cardinals',

            # Atlanta Falcons
            'ATL': 'atlanta_falcons',
            'ATLANTA': 'atlanta_falcons',
            'FALCONS': 'atlanta_falcons',
            'atlanta_falcons': 'atlanta_falcons',

            # Baltimore Ravens
            'BAL': 'baltimore_ravens',
            'BALTIMORE': 'baltimore_ravens',
            'RAVENS': 'baltimore_ravens',
            'baltimore_ravens': 'baltimore_ravens',

            # Buffalo Bills
            'BUF': 'buffalo_bills',
            'BUFFALO': 'buffalo_bills',
            'BILLS': 'buffalo_bills',
            'buffalo_bills': 'buffalo_bills',

            # Carolina Panthers
            'CAR': 'carolina_panthers',
            'CAROLINA': 'carolina_panthers',
            'PANTHERS': 'carolina_panthers',
            'carolina_panthers': 'carolina_panthers',

            # Chicago Bears
            'CHI': 'chicago_bears',
            'CHICAGO': 'chicago_bears',
            'BEARS': 'chicago_bears',
            'chicago_bears': 'chicago_bears',

            # Cincinnati Bengals
            'CIN': 'cincinnati_bengals',
            'CINCINNATI': 'cincinnati_bengals',
            'BENGALS': 'cincinnati_bengals',
            'cincinnati_bengals': 'cincinnati_bengals',

            # Cleveland Browns
            'CLE': 'cleveland_browns',
            'CLEVELAND': 'cleveland_browns',
            'BROWNS': 'cleveland_browns',
            'cleveland_browns': 'cleveland_browns',

            # Dallas Cowboys
            'DAL': 'dallas_cowboys',
            'DALLAS': 'dallas_cowboys',
            'COWBOYS': 'dallas_cowboys',
            'dallas_cowboys': 'dallas_cowboys',

            # Denver Broncos
            'DEN': 'denver_broncos',
            'DENVER': 'denver_broncos',
            'BRONCOS': 'denver_broncos',
            'denver_broncos': 'denver_broncos',

            # Detroit Lions
            'DET': 'detroit_lions',
            'DETROIT': 'detroit_lions',
            'LIONS': 'detroit_lions',
            'detroit_lions': 'detroit_lions',

            # Green Bay Packers
            'GB': 'green_bay_packers',
            'GNB': 'green_bay_packers',
            'GREEN BAY': 'green_bay_packers',
            'PACKERS': 'green_bay_packers',
            'green_bay_packers': 'green_bay_packers',

            # Houston Texans
            'HOU': 'houston_texans',
            'HOUSTON': 'houston_texans',
            'TEXANS': 'houston_texans',
            'houston_texans': 'houston_texans',

            # Indianapolis Colts
            'IND': 'indianapolis_colts',
            'INDIANAPOLIS': 'indianapolis_colts',
            'COLTS': 'indianapolis_colts',
            'indianapolis_colts': 'indianapolis_colts',

            # Jacksonville Jaguars
            'JAX': 'jacksonville_jaguars',
            'JAC': 'jacksonville_jaguars',
            'JACKSONVILLE': 'jacksonville_jaguars',
            'JAGUARS': 'jacksonville_jaguars',
            'jacksonville_jaguars': 'jacksonville_jaguars',

            # Kansas City Chiefs
            'KC': 'kansas_city_chiefs',
            'KAN': 'kansas_city_chiefs',
            'KANSAS CITY': 'kansas_city_chiefs',
            'CHIEFS': 'kansas_city_chiefs',
            'kansas_city_chiefs': 'kansas_city_chiefs',

            # Las Vegas Raiders
            'LV': 'las_vegas_raiders',
            'LAS': 'las_vegas_raiders',
            'OAK': 'las_vegas_raiders',  # Historical Oakland
            'LAS VEGAS': 'las_vegas_raiders',
            'OAKLAND': 'las_vegas_raiders',
            'RAIDERS': 'las_vegas_raiders',
            'las_vegas_raiders': 'las_vegas_raiders',
            'oakland_raiders': 'las_vegas_raiders',  # Historical

            # Los Angeles Chargers
            'LAC': 'los_angeles_chargers',
            'SD': 'los_angeles_chargers',  # Historical San Diego
            'LOS ANGELES CHARGERS': 'los_angeles_chargers',
            'SAN DIEGO': 'los_angeles_chargers',
            'CHARGERS': 'los_angeles_chargers',
            'los_angeles_chargers': 'los_angeles_chargers',
            'san_diego_chargers': 'los_angeles_chargers',  # Historical

            # Los Angeles Rams
            'LAR': 'los_angeles_rams',
            'LA': 'los_angeles_rams',
            'STL': 'los_angeles_rams',  # Historical St. Louis
            'LOS ANGELES RAMS': 'los_angeles_rams',
            'ST LOUIS': 'los_angeles_rams',
            'RAMS': 'los_angeles_rams',
            'los_angeles_rams': 'los_angeles_rams',
            'st_louis_rams': 'los_angeles_rams',  # Historical

            # Miami Dolphins
            'MIA': 'miami_dolphins',
            'MIAMI': 'miami_dolphins',
            'DOLPHINS': 'miami_dolphins',
            'miami_dolphins': 'miami_dolphins',

            # Minnesota Vikings
            'MIN': 'minnesota_vikings',
            'MINNESOTA': 'minnesota_vikings',
            'VIKINGS': 'minnesota_vikings',
            'minnesota_vikings': 'minnesota_vikings',

            # New England Patriots
            'NE': 'new_england_patriots',
            'NEW ENGLAND': 'new_england_patriots',
            'PATRIOTS': 'new_england_patriots',
            'new_england_patriots': 'new_england_patriots',

            # New Orleans Saints
            'NO': 'new_orleans_saints',
            'NEW ORLEANS': 'new_orleans_saints',
            'SAINTS': 'new_orleans_saints',
            'new_orleans_saints': 'new_orleans_saints',

            # New York Giants
            'NYG': 'new_york_giants',
            'NEW YORK GIANTS': 'new_york_giants',
            'GIANTS': 'new_york_giants',
            'new_york_giants': 'new_york_giants',

            # New York Jets
            'NYJ': 'new_york_jets',
            'NEW YORK JETS': 'new_york_jets',
            'JETS': 'new_york_jets',
            'new_york_jets': 'new_york_jets',

            # Philadelphia Eagles
            'PHI': 'philadelphia_eagles',
            'PHILADELPHIA': 'philadelphia_eagles',
            'EAGLES': 'philadelphia_eagles',
            'philadelphia_eagles': 'philadelphia_eagles',

            # Pittsburgh Steelers
            'PIT': 'pittsburgh_steelers',
            'PITTSBURGH': 'pittsburgh_steelers',
            'STEELERS': 'pittsburgh_steelers',
            'pittsburgh_steelers': 'pittsburgh_steelers',

            # San Francisco 49ers
            'SF': 'san_francisco_49ers',
            'SFO': 'san_francisco_49ers',
            'SAN FRANCISCO': 'san_francisco_49ers',
            '49ERS': 'san_francisco_49ers',
            'NINERS': 'san_francisco_49ers',
            'san_francisco_49ers': 'san_francisco_49ers',

            # Seattle Seahawks
            'SEA': 'seattle_seahawks',
            'SEATTLE': 'seattle_seahawks',
            'SEAHAWKS': 'seattle_seahawks',
            'seattle_seahawks': 'seattle_seahawks',

            # Tampa Bay Buccaneers
            'TB': 'tampa_bay_buccaneers',
            'TAM': 'tampa_bay_buccaneers',
            'TAMPA BAY': 'tampa_bay_buccaneers',
            'BUCCANEERS': 'tampa_bay_buccaneers',
            'BUCS': 'tampa_bay_buccaneers',
            'tampa_bay_buccaneers': 'tampa_bay_buccaneers',

            # Tennessee Titans
            'TEN': 'tennessee_titans',
            'TENNESSEE': 'tennessee_titans',
            'TITANS': 'tennessee_titans',
            'tennessee_titans': 'tennessee_titans',

            # Washington Commanders
            'WAS': 'washington_commanders',
            'WSH': 'washington_commanders',
            'WASHINGTON': 'washington_commanders',
            'COMMANDERS': 'washington_commanders',
            'washington_commanders': 'washington_commanders',
            'washington_redskins': 'washington_commanders',  # Historical
            'washington_football_team': 'washington_commanders',  # Historical
        }

        # Reverse mapping for display names
        self.display_names = {
            'arizona_cardinals': 'Arizona Cardinals',
            'atlanta_falcons': 'Atlanta Falcons',
            'baltimore_ravens': 'Baltimore Ravens',
            'buffalo_bills': 'Buffalo Bills',
            'carolina_panthers': 'Carolina Panthers',
            'chicago_bears': 'Chicago Bears',
            'cincinnati_bengals': 'Cincinnati Bengals',
            'cleveland_browns': 'Cleveland Browns',
            'dallas_cowboys': 'Dallas Cowboys',
            'denver_broncos': 'Denver Broncos',
            'detroit_lions': 'Detroit Lions',
            'green_bay_packers': 'Green Bay Packers',
            'houston_texans': 'Houston Texans',
            'indianapolis_colts': 'Indianapolis Colts',
            'jacksonville_jaguars': 'Jacksonville Jaguars',
            'kansas_city_chiefs': 'Kansas City Chiefs',
            'las_vegas_raiders': 'Las Vegas Raiders',
            'los_angeles_chargers': 'Los Angeles Chargers',
            'los_angeles_rams': 'Los Angeles Rams',
            'miami_dolphins': 'Miami Dolphins',
            'minnesota_vikings': 'Minnesota Vikings',
            'new_england_patriots': 'New England Patriots',
            'new_orleans_saints': 'New Orleans Saints',
            'new_york_giants': 'New York Giants',
            'new_york_jets': 'New York Jets',
            'philadelphia_eagles': 'Philadelphia Eagles',
            'pittsburgh_steelers': 'Pittsburgh Steelers',
            'san_francisco_49ers': 'San Francisco 49ers',
            'seattle_seahawks': 'Seattle Seahawks',
            'tampa_bay_buccaneers': 'Tampa Bay Buccaneers',
            'tennessee_titans': 'Tennessee Titans',
            'washington_commanders': 'Washington Commanders'
        }

        # Common abbreviations for quick lookup
        self.abbreviations = {
            'arizona_cardinals': 'ARI',
            'atlanta_falcons': 'ATL',
            'baltimore_ravens': 'BAL',
            'buffalo_bills': 'BUF',
            'carolina_panthers': 'CAR',
            'chicago_bears': 'CHI',
            'cincinnati_bengals': 'CIN',
            'cleveland_browns': 'CLE',
            'dallas_cowboys': 'DAL',
            'denver_broncos': 'DEN',
            'detroit_lions': 'DET',
            'green_bay_packers': 'GB',
            'houston_texans': 'HOU',
            'indianapolis_colts': 'IND',
            'jacksonville_jaguars': 'JAX',
            'kansas_city_chiefs': 'KC',
            'las_vegas_raiders': 'LV',
            'los_angeles_chargers': 'LAC',
            'los_angeles_rams': 'LAR',
            'miami_dolphins': 'MIA',
            'minnesota_vikings': 'MIN',
            'new_england_patriots': 'NE',
            'new_orleans_saints': 'NO',
            'new_york_giants': 'NYG',
            'new_york_jets': 'NYJ',
            'philadelphia_eagles': 'PHI',
            'pittsburgh_steelers': 'PIT',
            'san_francisco_49ers': 'SF',
            'seattle_seahawks': 'SEA',
            'tampa_bay_buccaneers': 'TB',
            'tennessee_titans': 'TEN',
            'washington_commanders': 'WAS'
        }

    def standardize(self, team_name: str) -> Optional[str]:
        """
        Standardize a team name to the canonical format

        Args:
            team_name: Team name in any format

        Returns:
            Standardized team name or None if not found
        """
        if not team_name:
            return None

        # Clean the input
        cleaned = self._clean_team_name(team_name)

        # Direct lookup
        if cleaned in self.team_mappings:
            return self.team_mappings[cleaned]

        # Try fuzzy matching
        return self._fuzzy_match(cleaned)

    def get_display_name(self, standardized_name: str) -> str:
        """Get the display name for a standardized team name"""
        return self.display_names.get(standardized_name, standardized_name)

    def get_abbreviation(self, standardized_name: str) -> str:
        """Get the abbreviation for a standardized team name"""
        return self.abbreviations.get(standardized_name, standardized_name.upper()[:3])

    def _clean_team_name(self, team_name: str) -> str:
        """Clean team name for lookup"""
        if not team_name:
            return ""

        # Convert to uppercase and strip whitespace
        cleaned = team_name.strip().upper()

        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^(THE\s+)', '', cleaned)
        cleaned = re.sub(r'\s+(NFL|FOOTBALL)$', '', cleaned)

        return cleaned

    def _fuzzy_match(self, team_name: str) -> Optional[str]:
        """Attempt fuzzy matching for team names"""

        # Try partial matches
        for key, value in self.team_mappings.items():
            if team_name in key or key in team_name:
                return value

        # Try matching against city or team name parts
        words = team_name.split()
        for word in words:
            if len(word) >= 3:  # Avoid matching very short words
                for key, value in self.team_mappings.items():
                    if word in key:
                        return value

        return None

    def validate_team_names(self, team_names: List[str]) -> Dict[str, str]:
        """
        Validate and standardize a list of team names

        Args:
            team_names: List of team names to validate

        Returns:
            Dictionary mapping original -> standardized names
        """
        results = {}

        for team_name in team_names:
            standardized = self.standardize(team_name)
            results[team_name] = standardized

        return results

    def get_all_variations(self, standardized_name: str) -> List[str]:
        """Get all known variations of a standardized team name"""
        variations = []

        for key, value in self.team_mappings.items():
            if value == standardized_name:
                variations.append(key)

        return variations

    def create_matchup_key(self, team1: str, team2: str) -> str:
        """
        Create a consistent matchup key for two teams

        Args:
            team1: First team name (any format)
            team2: Second team name (any format)

        Returns:
            Standardized matchup key (alphabetically sorted)
        """
        std_team1 = self.standardize(team1)
        std_team2 = self.standardize(team2)

        if not std_team1 or not std_team2:
            # Fallback to original names if standardization fails
            std_team1 = team1 or "unknown"
            std_team2 = team2 or "unknown"

        # Sort alphabetically for consistency
        teams = sorted([std_team1, std_team2])
        return f"{teams[0]}_vs_{teams[1]}"


# Global instance for easy access
team_standardizer = TeamNameStandardizer()


def standardize_team_name(team_name: str) -> Optional[str]:
    """Convenience function for standardizing team names"""
    return team_standardizer.standardize(team_name)


def create_matchup_key(team1: str, team2: str) -> str:
    """Convenience function for creating matchup keys"""
    return team_standardizer.create_matchup_key(team1, team2)


if __name__ == "__main__":
    # Test the standardizer
    standardizer = TeamNameStandardizer()

    test_names = [
        "LV", "Raiders", "Las Vegas Raiders",
        "KC", "Chiefs", "Kansas City",
        "SF", "49ers", "San Francisco",
        "NE", "Patriots", "New England"
    ]

    print("🏈 Team Name Standardization Test")
    print("=" * 40)

    for name in test_names:
        standardized = standardizer.standardize(name)
        display = standardizer.get_display_name(standardized) if standardized else "Not Found"
        abbrev = standardizer.get_abbreviation(standardized) if standardized else "N/A"

        print(f"{name:20} -> {standardized:25} ({display}) [{abbrev}]")

    print(f"\n🔗 Matchup Key Examples:")
    print(f"LV vs KC: {standardizer.create_matchup_key('LV', 'KC')}")
    print(f"49ers vs Patriots: {standardizer.create_matchup_key('49ers', 'Patriots')}")
