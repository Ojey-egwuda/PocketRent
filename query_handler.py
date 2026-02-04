"""
PocketRent - Query Handler
Parses natural language queries about UK rent prices
"""
import re
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from rent_data import get_database, RentInfo


class QueryType(Enum):
    COMPARE = "compare"           # Compare specific areas
    CHEAPEST_REGION = "cheapest_region"  # Cheapest in a region
    CHEAPEST_UK = "cheapest_uk"   # Cheapest overall
    EXPENSIVE = "expensive"       # Most expensive overall
    EXPENSIVE_REGION = "expensive_region"  # Most expensive in region
    UNDER_BUDGET = "under_budget" # Areas under budget
    AREA_INFO = "area_info"       # Info about specific area
    REGION_INFO = "region_info"   # Info about a region
    HELP = "help"                 # Help message
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    query_type: QueryType
    areas: List[str] = None
    region: str = None
    bedrooms: int = 1
    budget: int = None
    limit: int = 5
    original: str = ""
    is_studio: bool = False


def parse_query(user_input: str) -> ParsedQuery:
    """Parse natural language query into structured query"""
    text = user_input.lower().strip()
    original = user_input
    
    # Extract bedroom count
    bedrooms = 1
    is_studio = False
    
    # Check for studio first
    if 'studio' in text:
        bedrooms = 1
        is_studio = True
    else:
        bed_match = re.search(r'(\d)[- ]?bed', text)
        if bed_match:
            bedrooms = int(bed_match.group(1))
            if bedrooms > 4:
                bedrooms = 4
            if bedrooms < 1:
                bedrooms = 1
    
    # Extract budget
    budget = None
    budget_match = re.search(r'under\s*£?\s*(\d{3,4})', text)
    if budget_match:
        budget = int(budget_match.group(1))
    budget_match2 = re.search(r'£(\d{3,4})\s*(?:per month|/month|pm|pcm)?', text)
    if budget_match2 and not budget:
        budget = int(budget_match2.group(1))
    
    # Extract areas (for comparison)
    areas = []
    
    # First, try to extract the area portion of the query
    # Remove common suffixes that aren't area names
    area_text = text
    
    # Remove "for a X bed" type suffixes
    area_text = re.sub(r'\s+for\s+a?\s*\d*\s*-?\s*bed.*$', '', area_text)
    area_text = re.sub(r'\s+on\s+\d+\s*-?\s*bed.*$', '', area_text)
    area_text = re.sub(r'\s+(flat|apartment|house|rent|rental|property).*$', '', area_text)
    
    # Pattern: "compare X vs Y vs Z"
    compare_match = re.search(r'compare\s+(.+?)$', area_text)
    if compare_match:
        area_part = compare_match.group(1)
        areas = re.split(r'\s+vs\s+|\s+and\s+|\s*,\s*', area_part)
        areas = [a.strip() for a in areas if a.strip()]
    
    # Also check for "X vs Y" without "compare"
    if not areas and ' vs ' in area_text:
        # Find the vs portion
        vs_match = re.search(r'^(.+?\s+vs\s+.+?)$', area_text)
        if vs_match:
            area_part = vs_match.group(1)
            areas = re.split(r'\s+vs\s+|\s+and\s+|\s*,\s*', area_part)
            areas = [a.strip() for a in areas if a.strip()]
    
    # Check for "X and Y" comparisons
    if not areas and ' and ' in area_text:
        and_match = re.search(r'^(.+?\s+and\s+.+?)$', area_text)
        if and_match:
            area_part = and_match.group(1)
            # Only split if we have exactly 2-5 potential areas
            parts = re.split(r'\s+and\s+|\s*,\s*', area_part)
            parts = [p.strip() for p in parts if p.strip()]
            if 2 <= len(parts) <= 5:
                areas = parts
    
    # Extract region
    region = None
    regions = ['north west', 'north east', 'yorkshire', 'west midlands', 'east midlands',
               'south west', 'south east', 'east of england', 'east england', 'london', 
               'wales', 'scotland', 'uk', 'england']
    for r in regions:
        if r in text:
            region = r
            break
    
    # Check for "in [place]" pattern - could be region OR specific area
    in_place_match = re.search(r'(?:in|for)\s+([a-z][a-z\s]+?)(?:\?|$|\s+for\s|\s+on\s)', text + ' ')
    specific_area = None
    if in_place_match and not region:
        place = in_place_match.group(1).strip()
        # Check if it's a known area (not a region)
        db = get_database()
        if db.get_area(place):
            specific_area = place
    
    # Determine query type
    query_type = QueryType.UNKNOWN
    
    # Help
    if any(w in text for w in ['help', 'how do i', 'what can you', 'how to use']):
        query_type = QueryType.HELP
    
    # Compare areas
    elif areas and len(areas) >= 2:
        query_type = QueryType.COMPARE
    
    # Cheapest/expensive in a specific area (not region) -> show that area's info
    elif specific_area and any(w in text for w in ['cheapest', 'lowest', 'expensive', 'highest']):
        areas = [specific_area]
        query_type = QueryType.AREA_INFO
    
    # Cheapest in region
    elif any(w in text for w in ['cheapest', 'lowest', 'affordable', 'budget']) and region:
        query_type = QueryType.CHEAPEST_REGION
    
    # Cheapest overall
    elif any(w in text for w in ['cheapest', 'lowest', 'affordable']) and not region:
        query_type = QueryType.CHEAPEST_UK
    
    # Most expensive in region
    elif any(w in text for w in ['expensive', 'highest', 'priciest', 'most costly']) and region:
        query_type = QueryType.EXPENSIVE_REGION
    
    # Most expensive overall
    elif any(w in text for w in ['expensive', 'highest', 'priciest', 'most costly']):
        query_type = QueryType.EXPENSIVE
    
    # Under budget
    elif budget:
        query_type = QueryType.UNDER_BUDGET
    
    # Region info
    elif region and any(w in text for w in ['rent in', 'prices in', 'cost in', 'average']):
        query_type = QueryType.REGION_INFO
    
    # Single area info
    elif any(w in text for w in ['rent in', 'how much', 'price in', 'cost in']):
        # Try to extract area name
        area_match = re.search(r'(?:rent|price|cost)\s+(?:in|for)\s+(\w[\w\s]+?)(?:\?|$)', text)
        if area_match:
            areas = [area_match.group(1).strip()]
            query_type = QueryType.AREA_INFO
    
    # Single area mentioned
    if query_type == QueryType.UNKNOWN and not areas:
        # Check if any known area is mentioned
        db = get_database()
        words = text.split()
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words)+1)):
                potential = ' '.join(words[i:j])
                if db.get_area(potential):
                    areas = [potential]
                    query_type = QueryType.AREA_INFO
                    break
    
    return ParsedQuery(
        query_type=query_type,
        areas=areas,
        region=region,
        bedrooms=bedrooms,
        budget=budget,
        original=original,
        is_studio=is_studio
    )


def execute_query(parsed: ParsedQuery) -> str:
    """Execute a parsed query and return formatted response"""
    db = get_database()
    
    if parsed.query_type == QueryType.HELP:
        return get_help_message()
    
    if parsed.query_type == QueryType.COMPARE:
        return execute_compare(db, parsed)
    
    if parsed.query_type == QueryType.CHEAPEST_REGION:
        return execute_cheapest_region(db, parsed)
    
    if parsed.query_type == QueryType.CHEAPEST_UK:
        return execute_cheapest_uk(db, parsed)
    
    if parsed.query_type == QueryType.EXPENSIVE:
        return execute_expensive(db, parsed)
    
    if parsed.query_type == QueryType.EXPENSIVE_REGION:
        return execute_expensive_region(db, parsed)
    
    if parsed.query_type == QueryType.UNDER_BUDGET:
        return execute_under_budget(db, parsed)
    
    if parsed.query_type == QueryType.AREA_INFO:
        return execute_area_info(db, parsed)
    
    if parsed.query_type == QueryType.REGION_INFO:
        return execute_region_info(db, parsed)
    
    return get_unknown_response(parsed.original)


def execute_compare(db, parsed: ParsedQuery) -> str:
    """Compare multiple areas"""
    results = db.compare_areas(parsed.areas, parsed.bedrooms)
    
    if not results:
        return f"❌ Sorry, I couldn't find data for those areas."
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    
    lines = [f"## 🏠 {bed_str.title()} Rent Comparison\n"]
    
    # Add studio note if applicable
    if parsed.is_studio:
        lines.append("*Note: Studio data not available, showing 1-bed prices*\n")
    
    lines.append("| Rank | Area | Monthly Rent |")
    lines.append("|------|------|-------------|")
    
    for i, (area, rent, found) in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        note = "" if found else " *(UK avg)*"
        lines.append(f"| {medal} | {area} | £{rent:,}/month{note} |")
    
    # Add insight
    cheapest = results[0]
    most_exp = results[-1]
    diff = most_exp[1] - cheapest[1]
    
    lines.append(f"\n**💡 Insight:** {cheapest[0]} is cheapest at £{cheapest[1]:,}/month. ")
    if len(results) > 1:
        lines.append(f"You'd save £{diff:,}/month compared to {most_exp[0]}.")
    
    return "\n".join(lines)


def execute_cheapest_region(db, parsed: ParsedQuery) -> str:
    """Find cheapest in a region"""
    results = db.find_cheapest_in_region(parsed.region, parsed.bedrooms, limit=5)
    
    if not results:
        return f"❌ Sorry, I couldn't find rent data for {parsed.region}."
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    region_title = parsed.region.title()
    
    lines = [f"## 🏆 Cheapest {bed_str.title()} Rent in {region_title}\n"]
    lines.append("| Rank | Area | Monthly Rent |")
    lines.append("|------|------|-------------|")
    
    for i, info in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        rent = info.get_rent(beds)
        lines.append(f"| {medal} | {info.area} | £{rent:,}/month |")
    
    return "\n".join(lines)


def execute_cheapest_uk(db, parsed: ParsedQuery) -> str:
    """Find cheapest in UK"""
    results = db.find_cheapest_overall(parsed.bedrooms, limit=10)
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    
    lines = [f"## 🏆 Cheapest {bed_str.title()} Rent in UK\n"]
    lines.append("| Rank | Area | Monthly Rent |")
    lines.append("|------|------|-------------|")
    
    for i, info in enumerate(results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        rent = info.get_rent(beds)
        lines.append(f"| {medal} | {info.area} | £{rent:,}/month |")
    
    return "\n".join(lines)


def execute_expensive(db, parsed: ParsedQuery) -> str:
    """Find most expensive"""
    results = db.find_most_expensive(parsed.bedrooms, limit=10)
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    
    lines = [f"## 💰 Most Expensive {bed_str.title()} Rent in UK\n"]
    lines.append("| Rank | Area | Monthly Rent |")
    lines.append("|------|------|-------------|")
    
    for i, info in enumerate(results, 1):
        rent = info.get_rent(beds)
        lines.append(f"| {i}. | {info.area} | £{rent:,}/month |")
    
    return "\n".join(lines)


def execute_expensive_region(db, parsed: ParsedQuery) -> str:
    """Find most expensive in a region"""
    areas = db.get_areas_in_region(parsed.region)
    
    if not areas:
        return f"❌ Sorry, I couldn't find rent data for {parsed.region}."
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    region_title = parsed.region.title()
    
    # Sort by rent descending (most expensive first)
    sorted_areas = sorted(areas, key=lambda x: x.get_rent(beds), reverse=True)[:10]
    
    lines = [f"## 💰 Most Expensive {bed_str.title()} Rent in {region_title}\n"]
    lines.append("| Rank | Area | Monthly Rent |")
    lines.append("|------|------|-------------|")
    
    for i, info in enumerate(sorted_areas, 1):
        rent = info.get_rent(beds)
        lines.append(f"| {i}. | {info.area} | £{rent:,}/month |")
    
    return "\n".join(lines)


def execute_under_budget(db, parsed: ParsedQuery) -> str:
    """Find areas under budget"""
    results = db.find_areas_under_budget(
        parsed.budget, 
        parsed.bedrooms, 
        region=parsed.region,
        limit=10
    )
    
    beds = parsed.bedrooms
    bed_str = f"{beds}-bed"
    budget = parsed.budget
    
    region_str = f" in {parsed.region.title()}" if parsed.region else ""
    
    if not results:
        return f"❌ No {bed_str} properties found under £{budget}/month{region_str}."
    
    lines = [f"## 🏠 {bed_str.title()} Rent Under £{budget:,}/month{region_str}\n"]
    lines.append("| Area | Monthly Rent | Under Budget By |")
    lines.append("|------|-------------|-----------------|")
    
    for info in results:
        rent = info.get_rent(beds)
        savings = budget - rent
        lines.append(f"| {info.area} | £{rent:,}/month | £{savings:,} |")
    
    lines.append(f"\n*Found {len(results)} areas*")
    
    return "\n".join(lines)


def execute_area_info(db, parsed: ParsedQuery) -> str:
    """Get info about a specific area"""
    if not parsed.areas:
        return "❌ Please specify an area name."
    
    area_name = parsed.areas[0]
    info = db.get_area(area_name)
    
    if not info:
        return f"❌ Sorry, I couldn't find rent data for '{area_name}'."
    
    lines = [f"## 📍 Rent in {info.area}\n"]
    lines.append("| Bedrooms | Monthly Rent |")
    lines.append("|----------|-------------|")
    lines.append(f"| 1 Bed | £{info.rent_1bed:,}/month |")
    lines.append(f"| 2 Bed | £{info.rent_2bed:,}/month |")
    lines.append(f"| 3 Bed | £{info.rent_3bed:,}/month |")
    lines.append(f"| 4+ Bed | £{info.rent_4bed:,}/month |")
    
    # Compare to UK average
    uk = db.uk_average
    diff_1 = info.rent_1bed - uk.rent_1bed
    pct = (diff_1 / uk.rent_1bed) * 100
    
    if diff_1 > 0:
        lines.append(f"\n**📊 vs UK Average:** £{diff_1:,}/month more ({pct:+.0f}%)")
    else:
        lines.append(f"\n**📊 vs UK Average:** £{abs(diff_1):,}/month less ({pct:.0f}%)")
    
    return "\n".join(lines)


def execute_region_info(db, parsed: ParsedQuery) -> str:
    """Get info about a region"""
    if not parsed.region:
        return "❌ Please specify a region."
    
    result = db.get_region_average(parsed.region, parsed.bedrooms)
    
    if result:
        region_name, avg_rent = result
        beds = parsed.bedrooms
        
        lines = [f"## 📍 Average Rent in {region_name}\n"]
        lines.append(f"**{beds}-bed average:** £{avg_rent:,}/month\n")
        
        # Show cheapest in region
        cheapest = db.find_cheapest_in_region(parsed.region, beds, limit=3)
        if cheapest:
            lines.append("**Cheapest areas:**")
            for i, info in enumerate(cheapest, 1):
                lines.append(f"- {info.area}: £{info.get_rent(beds):,}/month")
        
        return "\n".join(lines)
    
    return f"❌ Sorry, I couldn't find data for {parsed.region}."


def get_help_message() -> str:
    """Return help message"""
    return """## 🏠 PocketRent - Help

I can help you explore UK rent prices! Try asking:

### Compare Areas
- "Compare Manchester vs Liverpool vs Leeds"
- "Manchester vs Oxford on 2-bed rent"

### Find Cheapest
- "Cheapest 1-bed rent in North West"
- "Where is rent lowest in UK?"
- "Most affordable 2-bed in Yorkshire"

### Budget Search
- "Areas under £700/month rent"
- "2-bed under £1000 in South East"

### Area Info
- "How much is rent in Manchester?"
- "Rent prices in Bristol"

### Regions Available
London, North West, North East, Yorkshire, West Midlands, East Midlands, South West, South East, East of England, Wales, Scotland

---
*Data: ONS Private Rental Market Statistics*
"""


def get_unknown_response(original: str) -> str:
    """Response for queries we don't understand"""
    return f"""❓ I'm not sure what you're asking about "{original}".

Try questions like:
- "Compare Manchester vs Liverpool"
- "Cheapest 2-bed in North West"
- "Areas under £800/month"
- "Rent in Birmingham"

Type **help** for more examples.
"""


def process_query(user_input: str) -> str:
    """Main entry point - process a user query"""
    if not user_input or not user_input.strip():
        return "Please enter a question about UK rent prices."
    
    parsed = parse_query(user_input)
    return execute_query(parsed)
