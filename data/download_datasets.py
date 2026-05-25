"""
Download DOSM datasets for Theme 3 — Smart Government: Malaysian Cost of Living.
Datasets: CPI Inflation by Division, CPI by State, Fuel Prices, Household Income by State.
"""

import os
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = [
    {
        "name": "CPI Inflation by Division (National)",
        "url": "https://storage.dosm.gov.my/cpi/cpi_2d_inflation.csv",
        "filename": "cpi_2d_inflation.csv",
        "description": "Monthly national CPI inflation YoY and MoM by division (1980-present)",
    },
    {
        "name": "CPI Index by State and Division",
        "url": "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv",
        "filename": "cpi_2d_state.csv",
        "description": "Monthly CPI index by state and division (2010-present)",
    },
    {
        "name": "Retail Fuel Prices",
        "url": "https://storage.data.gov.my/commodities/fuelprice.csv",
        "filename": "fuelprice.csv",
        "description": "Weekly retail prices for RON95, RON97, and Diesel (2017-present)",
    },
    {
        "name": "Household Income by State",
        "url": "https://storage.dosm.gov.my/hies/hh_income_state.csv",
        "filename": "hh_income_state.csv",
        "description": "Survey-based mean and median household income by state (1970-2022)",
    },
]


def download(dataset):
    dest = os.path.join(OUTPUT_DIR, dataset["filename"])
    print(f"Downloading: {dataset['name']}")
    print(f"  {dataset['description']}")
    try:
        urllib.request.urlretrieve(dataset["url"], dest)
        size_kb = os.path.getsize(dest) / 1024
        print(f"  Saved: {dest}  ({size_kb:.1f} KB)\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("DOSM Dataset Downloader — Theme 3: Smart Government")
    print("=" * 60 + "\n")
    for ds in DATASETS:
        download(ds)
    print("Done. Files saved to:", OUTPUT_DIR)
