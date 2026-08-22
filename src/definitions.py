import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dagster import Definitions, load_assets_from_modules

from src import assets

# Load all assets from the assets module
all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)
