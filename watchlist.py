"""
Maritime company watchlist - daily digest script.
Searches for direct signals (hires, promotions, funding, jobs)
and general news for a list of Tier 1 and Tier 2 maritime tech companies.
"""

TIER_1 = [
    "SEDNA Systems",
    "Ripple Operations",
    "Deep Wave Maritime Technologies Group",
    "Windward",
    "ZeroNorth",
    "Nautilus Labs",
    "Concirrus",
    "Portchain",
    "Lloyd's Register OneOcean",
]

TIER_2 = [
    "Maersk", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO Shipping", "Stena",
    "DFDS", "Carnival Corporation",
    "V.Group", "Anglo-Eastern", "OSM Thome", "Bernhard Schulte Shipmanagement",
    "Synergy Marine", "Wallem", "Fleet Management Limited", "Columbia Shipmanagement",
    "Seagull Maritime", "Elvictor Group", "VSTEP Simulation", "Maritime Trainer",
    "SafeBridge", "MarTID",
    "IMPAC Systems", "Marine C", "Promena", "MariApps Mantra",
    "DNV ShipManager", "Veson IMOS", "AMOS", "ABS Nautical Systems",
    "Veslink HardHat", "IFS Ultima",
    "Cydome Security", "Maritime Cyber Solutions", "Nettitude", "Otorio",
    "Port-IT", "Marlink",
    "Inmarsat", "Iridium", "KVH Industries", "Speedcast", "NSSLGLOBAL",
    "Navarino", "Cobham SATCOM", "Intellian",
    "Lloyd's Register", "DNV", "ABS", "Bureau Veritas",
    "Navis", "TBA Group", "Envision", "Awake.AI", "CyberLogitec",
    "StormGeo", "Wartsila Voyage", "Kongsberg Digital",
    "Signal Ocean", "DTN",
    "MarineTraffic", "Spire Maritime", "Pole Star",
    "Vanguard", "Otonomi", "Breeze",
    "CargoSmart", "Freightos", "INTTRA", "Kale Logistics",
    "Clarksons",
]


def build_company_list():
    """Return the combined watchlist with tier labels."""
    watchlist = [{"name": c, "tier": 1} for c in TIER_1]
    watchlist += [{"name": c, "tier": 2} for c in TIER_2]
    return watchlist


if __name__ == "__main__":
    wl = build_company_list()
    print(f"Total companies on watchlist: {len(wl)}")
    print(f"Tier 1: {len(TIER_1)}")
    print(f"Tier 2: {len(TIER_2)}")
