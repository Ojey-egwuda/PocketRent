"""
PocketRent - Rent Data Module
Loads and queries ONS rent data from Excel file
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RentInfo:
    """Rent information for an area"""
    area: str
    rent_1bed: int
    rent_2bed: int
    rent_3bed: int
    rent_4bed: int
    
    def get_rent(self, bedrooms: int) -> int:
        """Get rent for specific bedroom count"""
        return {1: self.rent_1bed, 2: self.rent_2bed, 
                3: self.rent_3bed, 4: self.rent_4bed}.get(bedrooms, self.rent_1bed)
    
    def to_dict(self) -> dict:
        return {
            "area": self.area,
            "1_bed": self.rent_1bed,
            "2_bed": self.rent_2bed,
            "3_bed": self.rent_3bed,
            "4_bed": self.rent_4bed,
        }


# UK Regions mapping
REGIONS = {
    "london": [
        "barking and dagenham", "barnet", "bexley", "brent", "bromley", "camden",
        "croydon", "ealing", "enfield", "greenwich", "hackney", "hammersmith and fulham",
        "haringey", "harrow", "havering", "hillingdon", "hounslow", "islington",
        "kensington and chelsea", "kingston upon thames", "lambeth", "lewisham",
        "merton", "newham", "redbridge", "richmond upon thames", "southwark", "sutton",
        "tower hamlets", "waltham forest", "wandsworth", "westminster", "city of london"
    ],
    "north west": [
        "manchester", "liverpool", "bolton", "bury", "oldham", "rochdale", "salford",
        "stockport", "tameside", "trafford", "wigan", "blackburn with darwen", "blackpool",
        "cheshire east", "cheshire west and chester", "halton", "knowsley", "lancaster",
        "preston", "sefton", "st helens", "warrington", "wirral"
    ],
    "north east": [
        "newcastle upon tyne", "sunderland", "gateshead", "south tyneside", "north tyneside",
        "county durham", "darlington", "hartlepool", "middlesbrough", "redcar and cleveland",
        "stockton-on-tees", "northumberland"
    ],
    "yorkshire": [
        "leeds", "sheffield", "bradford", "york", "hull", "barnsley", "calderdale",
        "doncaster", "kirklees", "rotherham", "wakefield", "east riding of yorkshire",
        "north lincolnshire", "north east lincolnshire"
    ],
    "west midlands": [
        "birmingham", "coventry", "wolverhampton", "dudley", "sandwell", "solihull",
        "walsall", "herefordshire", "shropshire", "stoke-on-trent", "telford and wrekin",
        "warwickshire", "worcestershire"
    ],
    "east midlands": [
        "nottingham", "derby", "leicester", "northampton", "lincoln", "chesterfield",
        "derbyshire dales", "high peak", "north east derbyshire", "south derbyshire",
        "rutland", "peterborough"
    ],
    "south west": [
        "bristol", "bath", "plymouth", "exeter", "bournemouth", "swindon", "gloucester",
        "cheltenham", "torbay", "cornwall", "devon", "dorset", "somerset", "wiltshire"
    ],
    "south east": [
        "reading", "oxford", "brighton and hove", "southampton", "portsmouth", "milton keynes",
        "slough", "guildford", "woking", "luton", "watford", "st albans", "crawley",
        "maidstone", "canterbury", "tunbridge wells", "hastings", "eastbourne", "worthing",
        "basingstoke", "bracknell forest", "windsor and maidenhead", "wokingham",
        "buckinghamshire", "hampshire", "kent", "surrey", "east sussex", "west sussex"
    ],
    "east of england": [
        "cambridge", "norwich", "ipswich", "colchester", "chelmsford", "peterborough",
        "southend-on-sea", "luton", "bedford", "hertfordshire", "essex", "suffolk", "norfolk"
    ],
    "wales": [
        "cardiff", "swansea", "newport", "wrexham", "barry", "neath", "cwmbran"
    ],
    "scotland": [
        "edinburgh", "glasgow", "aberdeen", "dundee", "stirling", "perth", "inverness",
        "greater glasgow", "lothian", "aberdeen and shire", "dundee and angus"
    ],
}


class RentDatabase:
    """Database of UK rent prices from ONS data"""
    
    def __init__(self, excel_path: str = None):
        if excel_path is None:
            excel_path = Path(__file__).parent / "data" / "rent_data.xlsx"
        
        self.data: Dict[str, RentInfo] = {}
        self.uk_average: RentInfo = None
        self.period: str = "Unknown"
        self._load_data(excel_path)
    
    def _load_data(self, excel_path: str):
        """Load rent data from ONS Excel file"""
        try:
            df = pd.read_excel(excel_path, sheet_name='Table 1', header=2)
            
            # Get latest time period
            latest_period = df['Time period'].max()
            latest_df = df[df['Time period'] == latest_period].copy()
            
            self.period = latest_period.strftime('%B %Y') if hasattr(latest_period, 'strftime') else str(latest_period)
            
            for _, row in latest_df.iterrows():
                area_name = str(row['Area name']).strip()
                
                r1 = self._safe_int(row.get('Rental price one bed'))
                r2 = self._safe_int(row.get('Rental price two bed'))
                r3 = self._safe_int(row.get('Rental price three bed'))
                r4 = self._safe_int(row.get('Rental price four or more bed'))
                
                if r1 is None or r2 is None:
                    continue
                
                rent_info = RentInfo(
                    area=area_name,
                    rent_1bed=r1,
                    rent_2bed=r2,
                    rent_3bed=r3 or r2,
                    rent_4bed=r4 or r3 or r2
                )
                
                # Store with lowercase key for easy lookup
                self.data[area_name.lower()] = rent_info
                
                # Store UK average separately
                if area_name == "United Kingdom":
                    self.uk_average = rent_info
            
            # Data loaded successfully
            
        except Exception as e:
            print(f"Error loading rent data: {e}")
            self.data = {}
            self.uk_average = RentInfo("UK Average", 1109, 1250, 1396, 2039)
    
    def _safe_int(self, val) -> Optional[int]:
        """Convert value to int safely"""
        try:
            if pd.isna(val) or str(val) == '[x]':
                return None
            return int(float(val))
        except:
            return None
    
    def get_area(self, name: str) -> Optional[RentInfo]:
        """Get rent data for a specific area"""
        name_lower = name.lower().strip()
        
        # Direct match
        if name_lower in self.data:
            return self.data[name_lower]
        
        # Common aliases (check before partial match to avoid wrong matches)
        aliases = {
            "newcastle": "newcastle upon tyne",
            "hull": "kingston upon hull, city of",
            "stoke": "stoke-on-trent",
            "edinburgh": "lothian",
            "glasgow": "greater glasgow",
            "york": "york",  # Prevent matching Yorkshire
        }
        if name_lower in aliases:
            return self.data.get(aliases[name_lower])
        
        # Partial match (only if no alias found)
        for key, info in self.data.items():
            if name_lower in key or key in name_lower:
                return info
        
        return None
    
    def compare_areas(self, areas: List[str], bedrooms: int = 1) -> List[Tuple[str, int, bool]]:
        """Compare rent across multiple areas
        Returns: List of (area_name, rent, found) tuples sorted by rent
        """
        results = []
        for area in areas:
            info = self.get_area(area)
            if info:
                results.append((info.area, info.get_rent(bedrooms), True))
            else:
                results.append((area, self.uk_average.get_rent(bedrooms), False))
        
        return sorted(results, key=lambda x: x[1])
    
    def get_areas_in_region(self, region: str) -> List[RentInfo]:
        """Get all areas in a region"""
        region_lower = region.lower().strip()
        
        # Find region
        region_areas = None
        for reg_name, areas in REGIONS.items():
            if region_lower in reg_name or reg_name in region_lower:
                region_areas = areas
                break
        
        if not region_areas:
            return []
        
        # Get data for each area in region
        results = []
        for area in region_areas:
            info = self.get_area(area)
            if info:
                results.append(info)
        
        return results
    
    def find_cheapest_in_region(self, region: str, bedrooms: int = 1, limit: int = 5) -> List[RentInfo]:
        """Find cheapest areas in a region"""
        areas = self.get_areas_in_region(region)
        if not areas:
            return []
        
        sorted_areas = sorted(areas, key=lambda x: x.get_rent(bedrooms))
        return sorted_areas[:limit]
    
    def find_areas_under_budget(self, max_rent: int, bedrooms: int = 1, 
                                 region: str = None, limit: int = 10) -> List[RentInfo]:
        """Find areas under a budget"""
        if region:
            areas = self.get_areas_in_region(region)
        else:
            areas = list(self.data.values())
        
        filtered = [a for a in areas if a.get_rent(bedrooms) <= max_rent]
        sorted_areas = sorted(filtered, key=lambda x: x.get_rent(bedrooms))
        return sorted_areas[:limit]
    
    def find_cheapest_overall(self, bedrooms: int = 1, limit: int = 10) -> List[RentInfo]:
        """Find cheapest areas in UK"""
        # Exclude aggregate regions
        exclude = ['united kingdom', 'great britain', 'england', 'wales', 'scotland', 
                   'northern ireland', 'north east', 'north west', 'yorkshire and the humber',
                   'east midlands', 'west midlands', 'east of england', 'london', 
                   'south east', 'south west']
        
        areas = [a for k, a in self.data.items() if k not in exclude]
        sorted_areas = sorted(areas, key=lambda x: x.get_rent(bedrooms))
        return sorted_areas[:limit]
    
    def find_most_expensive(self, bedrooms: int = 1, limit: int = 10) -> List[RentInfo]:
        """Find most expensive areas in UK"""
        exclude = ['united kingdom', 'great britain', 'england', 'wales', 'scotland', 
                   'northern ireland', 'north east', 'north west', 'yorkshire and the humber',
                   'east midlands', 'west midlands', 'east of england', 'london', 
                   'south east', 'south west']
        
        areas = [a for k, a in self.data.items() if k not in exclude]
        sorted_areas = sorted(areas, key=lambda x: x.get_rent(bedrooms), reverse=True)
        return sorted_areas[:limit]
    
    def search_areas(self, query: str) -> List[RentInfo]:
        """Search for areas matching a query"""
        query_lower = query.lower().strip()
        results = []
        
        for key, info in self.data.items():
            if query_lower in key:
                results.append(info)
        
        return results
    
    def get_region_average(self, region: str, bedrooms: int = 1) -> Optional[Tuple[str, int]]:
        """Get average rent for a region"""
        # Try to find the region itself in data
        region_lower = region.lower().strip()
        
        for key, info in self.data.items():
            if region_lower in key or key in region_lower:
                if key in ['north east', 'north west', 'london', 'south east', 'south west',
                          'east midlands', 'west midlands', 'east of england', 
                          'yorkshire and the humber', 'wales', 'scotland']:
                    return (info.area, info.get_rent(bedrooms))
        
        return None
    
    def get_all_regions(self) -> List[str]:
        """Get list of all regions"""
        return list(REGIONS.keys())


# Singleton instance
_db = None

def get_database() -> RentDatabase:
    """Get the rent database singleton"""
    global _db
    if _db is None:
        _db = RentDatabase()
    return _db
