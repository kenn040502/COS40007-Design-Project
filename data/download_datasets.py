"""
Download DOSM datasets for Theme 3 - Smart Government
Datasets: HIES by District, HIES by State, Poverty by District, Gini by State
"""

import os
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = [
    {
        "name": "HIES by District",
        "url": "https://storage.dosm.gov.my/hies/hies_district.csv",
        "filename": "hies_district.csv",
        "description": "Income, expenditure, poverty & inequality at district level (2022)",
    },
    {
        "name": "HIES by State",
        "url": "https://storage.dosm.gov.my/hies/hies_state.csv",
        "filename": "hies_state.csv",
        "description": "Income, expenditure, poverty & inequality at state level (1970-2022)",
    },
    {
        "name": "Poverty by District",
        "url": "https://storage.dosm.gov.my/hies/hh_poverty_district.csv",
        "filename": "hh_poverty_district.csv",
        "description": "Absolute & relative poverty rates by district (2019-2022)",
    },
    {
        "name": "Gini Coefficient by State",
        "url": "https://storage.dosm.gov.my/hies/hh_inequality_state.csv",
        "filename": "hh_inequality_state.csv",
        "description": "Gini coefficient (income inequality) by state (1974-2022)",
    },
]


def download(dataset):
    dest = os.path.join(OUTPUT_DIR, dataset["filename"])
    print(f"Downloading: {dataset['name']}")
    print(f"  {dataset['description']}")
    try:
        urllib.request.urlretrieve(dataset["url"], dest)
        size_kb = os.path.getsize(dest) / 1024
        print(f"  Saved to: {dest}  ({size_kb:.1f} KB)\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("DOSM Dataset Downloader - Theme 3: Smart Government")
    print("=" * 60 + "\n")
    for ds in DATASETS:
        download(ds)
    print("Done. Files saved to:", OUTPUT_DIR)
