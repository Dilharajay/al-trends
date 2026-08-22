from typing import List, Tuple, Set, Optional

# Constants for Subject Categories (Canonical Catalogue)
SCIENCES_PURE = {"Physics", "Chemistry", "Biology", "Combined Mathematics"}

BIO_BASKET = {"Chemistry", "Physics", "Agricultural Science"}
PHY_BASKET = {"Physics", "Chemistry", "ICT"}

# Tech streams open basket allows many, but explicitly bars pure sciences
TECH_BARRED = {"Physics", "Chemistry", "Biology", "Combined Mathematics"}
TECH_OPEN_BASKET = {"ICT", "Geography", "Economics", "Accounting", "Business Studies", "Agro Technology", "English", "Logic & Scientific Method"} # Simplified for now

COMMERCE_CORE = {"Accounting", "Business Studies", "Economics"}
COMMERCE_EXTENDED = {"Combined Mathematics", "ICT", "Geography", "Logic & Scientific Method", "English"} # Languages etc.

ARTS_BASKET = {"Political Science", "History", "Geography", "Economics", "Logic & Scientific Method", "English Literature", "Sinhala", "Tamil", "English", "French"} # Subset for stubbing


def validate_combination(subjects: List[str]) -> Tuple[List[str], Optional[str], List[str]]:
    """
    Validates a combination of exactly 3 subjects against the UGC stream rules.
    Returns:
        matching_streams (List[str]): List of valid streams (usually 1).
        failure_reason (Optional[str]): Why it failed if matching_streams is empty.
        suggested_swaps (List[str]): Up to 3 suggested swaps if invalid.
    """
    if len(set(subjects)) != 3:
        return [], "Combination must contain exactly 3 distinct subjects", []

    sub_set = set(subjects)
    
    # Global Disallowed Pair
    if "Biology" in sub_set and "Combined Mathematics" in sub_set:
        return [], "Disallowed pair: Biology and Combined Mathematics cannot sit in the same combination", []

    matches = []
    closest_fail = None

    # 1. Biological Science
    if "Biology" in sub_set:
        basket_count = len(sub_set.intersection(BIO_BASKET))
        if basket_count == 2:
            matches.append("Biological Science")
        else:
            closest_fail = "Bio stream basket requires exactly 2 from {Chemistry, Physics, Agricultural Science}"
    
    # 2. Physical Science
    if "Combined Mathematics" in sub_set:
        basket_count = len(sub_set.intersection(PHY_BASKET))
        if basket_count == 2:
            matches.append("Physical Science")
        elif not closest_fail:
            closest_fail = "Phys stream basket requires exactly 2 from {Physics, Chemistry, ICT}"
            
    # 3. Engineering Technology
    if "Engineering Technology" in sub_set and "Science for Technology" in sub_set:
        third_subject = list(sub_set - {"Engineering Technology", "Science for Technology"})[0]
        if third_subject in TECH_BARRED:
            closest_fail = f"Engineering Technology third subject cannot be {third_subject}"
        elif third_subject in TECH_OPEN_BASKET: # Relaxed in reality, but we check barred first
            matches.append("Engineering Technology")
        else:
             matches.append("Engineering Technology") # Default fallback if not barred
             
    # 4. Bio-systems Technology
    if "Bio Systems Technology" in sub_set and "Science for Technology" in sub_set:
        third_subject = list(sub_set - {"Bio Systems Technology", "Science for Technology"})[0]
        if third_subject in TECH_BARRED:
            closest_fail = f"Bio-systems Technology third subject cannot be {third_subject}"
        else:
             matches.append("Technology") # Normalized to Technology for DB compatibility
             
    # 5. Commerce
    com_core_count = len(sub_set.intersection(COMMERCE_CORE))
    if com_core_count > 0:
        com_total_count = len(sub_set.intersection(COMMERCE_CORE.union(COMMERCE_EXTENDED)))
        if com_total_count == 3:
            matches.append("Commerce")
        elif not closest_fail and len(matches) == 0:
            closest_fail = "Commerce stream requires at least 1 core (Accounting/Business/Economics) and rest from extended basket"

    # 6. Arts
    # If it fails everything else and contains Arts subjects, it's Arts.
    if len(matches) == 0 and not closest_fail:
         arts_count = len(sub_set.intersection(ARTS_BASKET))
         if arts_count == 3:
             matches.append("Arts")
         else:
             closest_fail = "Subjects do not form a valid UGC combination for any stream"

    if matches:
        return matches, None, []
        
    return [], closest_fail, []
