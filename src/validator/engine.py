from typing import List, Tuple, Set, Optional

# Constants for Subject Categories (Canonical Catalogue)
SCIENCES_PURE = {"Physics", "Chemistry", "Biology", "Combined Mathematics"}

BIO_BASKET = {"Chemistry", "Physics", "Agricultural Science"}
PHY_BASKET = {"Physics", "Chemistry", "ICT"}

TECH_BARRED = {"Physics", "Chemistry", "Biology", "Combined Mathematics"}
TECH_OPEN_BASKET = {"ICT", "Geography", "Economics", "Accounting", "Business Studies", "Agro Technology", "English", "Logic & Scientific Method"}

COMMERCE_CORE = {"Accounting", "Business Studies", "Economics"}
COMMERCE_EXTENDED = {"Combined Mathematics", "ICT", "Geography", "Logic & Scientific Method", "English"}

ARTS_BASKET = {"Political Science", "History", "Geography", "Economics", "Logic & Scientific Method", "English Literature", "Sinhala", "Tamil", "English", "French"}

ALL_SUBJECTS = SCIENCES_PURE | BIO_BASKET | PHY_BASKET | TECH_BARRED | TECH_OPEN_BASKET | COMMERCE_CORE | COMMERCE_EXTENDED | ARTS_BASKET | {"Engineering Technology", "Science for Technology", "Bio Systems Technology"}

def validateCombination(subjects: List[str], with_swaps: bool = True) -> Tuple[List[str], Optional[str], List[str]]:
    """
    Validates a combination of exactly 3 subjects against UGC rules.
    Returns:
        matching_streams (List[str]): List of valid streams.
        failure_reason (Optional[str]): Rule failure reason if invalid.
        suggested_swaps (List[str]): Suggested single-swap replacements if invalid.
    """
    if len(set(subjects)) != 3:
        return [], "Combination must contain exactly 3 distinct subjects.", []

    sub_set = set(subjects)
    
    # 1. Global Disallowed Pair
    if "Biology" in sub_set and "Combined Mathematics" in sub_set:
        reason = "disallowed pair: Biology and Combined Mathematics cannot sit in the same combination per the UGC stream-definition circular"
        return [], reason, generate_swaps(sub_set) if with_swaps else []

    matches = []
    closest_fail = None

    # Walk the streams in priority order
    
    # BIO
    if "Biology" in sub_set:
        if len(sub_set.intersection(BIO_BASKET)) >= 2:
            matches.append("Biological Science")
        else:
            closest_fail = "Bio stream basket requires exactly 2 from {Chemistry, Physics, Agricultural Science}"
            
    # PHY
    if "Combined Mathematics" in sub_set:
        if len(sub_set.intersection(PHY_BASKET)) >= 2:
            matches.append("Physical Science")
        elif not closest_fail:
            closest_fail = "Phys stream basket requires exactly 2 from {Physics, Chemistry, ICT}"
            
    # ENG-TECH
    if "Engineering Technology" in sub_set and "Science for Technology" in sub_set:
        third_subject = list(sub_set - {"Engineering Technology", "Science for Technology"})[0]
        if third_subject in TECH_BARRED:
            closest_fail = "third subject barred: must come from open basket (Phys/Chem/Bio/Combined Maths excluded)"
        else:
            matches.append("Engineering Technology")
            
    # BIO-TECH
    if "Bio Systems Technology" in sub_set and "Science for Technology" in sub_set:
        third_subject = list(sub_set - {"Bio Systems Technology", "Science for Technology"})[0]
        if third_subject in TECH_BARRED:
            closest_fail = "third subject barred: must come from open basket (Phys/Chem/Bio/Combined Maths excluded)"
        else:
            matches.append("Bio-systems Technology")
            
    # COM
    if len(sub_set.intersection(COMMERCE_CORE)) > 0:
        if len(sub_set.intersection(COMMERCE_CORE | COMMERCE_EXTENDED)) == 3:
            matches.append("Commerce")
        elif not closest_fail:
            closest_fail = "Commerce requires at least 1 core subject and remaining from Commerce basket"

    # ART
    if not matches and not closest_fail:
        if len(sub_set.intersection(ARTS_BASKET)) == 3:
            matches.append("Arts")
        else:
            closest_fail = "Does not match any UGC stream rule baskets"

    if matches:
        return matches, None, []
        
    return [], closest_fail, generate_swaps(sub_set) if with_swaps else []

def generate_swaps(sub_set: Set[str]) -> List[str]:
    """Generates 1-subject swaps to turn an invalid combination valid."""
    swaps = []
    for sub_to_remove in sub_set:
        for sub_to_add in ALL_SUBJECTS - sub_set:
            new_combo = list((sub_set - {sub_to_remove}) | {sub_to_add})
            streams, _, _ = validateCombination(new_combo, with_swaps=False)
            if streams:
                swaps.append(f"replace {sub_to_remove} with {sub_to_add} -> valid {streams[0]} combo")
                if len(swaps) >= 3:
                    return swaps
    return swaps

def classifyByPriorityWalk(subjects: List[str]) -> Optional[str]:
    """Strict cross-check returning the first matching stream."""
    streams, _, _ = validateCombination(subjects, with_swaps=False)
    if streams:
        return streams[0]
    return None
