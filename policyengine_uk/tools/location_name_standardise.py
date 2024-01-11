def standardise_location_name(location_name: str) -> str:
    # e.g. PEAKS_DALES <- "Peaks & Dales"

    return (
        location_name.upper()
        .replace("&", "")
        .replace(",", "")
        .replace(".", "")
        .replace("  ", " ")
        .replace(" ", "_")
    )
