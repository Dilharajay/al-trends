import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.validator.engine import validateCombination, classifyByPriorityWalk

def test_valid_bio():
    combo = ["Biology", "Chemistry", "Physics"]
    streams, reason, swaps = validateCombination(combo)
    assert streams == ["Biological Science"]
    assert reason is None
    assert classifyByPriorityWalk(combo) == "Biological Science"

def test_valid_eng_tech():
    combo = ["Engineering Technology", "Science for Technology", "ICT"]
    streams, reason, swaps = validateCombination(combo)
    assert streams == ["Engineering Technology"]
    assert reason is None

def test_invalid_disallowed_pair():
    combo = ["Combined Mathematics", "Biology", "Chemistry"]
    streams, reason, swaps = validateCombination(combo)
    assert streams == []
    assert "disallowed pair: Biology and Combined Mathematics" in reason
    # Should suggest replacing Combined Maths or Biology
    assert any("replace Combined Mathematics with Physics" in s or "replace Biology with Physics" in s for s in swaps)

def test_valid_commerce():
    combo = ["Accounting", "Economics", "Combined Mathematics"]
    streams, reason, swaps = validateCombination(combo)
    assert streams == ["Commerce"]
    assert reason is None

def test_invalid_tech_barred():
    combo = ["Engineering Technology", "Science for Technology", "Biology"]
    streams, reason, swaps = validateCombination(combo)
    assert streams == []
    assert "third subject barred" in reason
    assert any("replace Biology with" in s for s in swaps)
