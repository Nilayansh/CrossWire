"""Threshold constants for tool evidence evaluation."""

# Rainfall thresholds in mm/hr
RAIN_HEAVY_THRESHOLD: float = 40.0      # >= 40 mm/hr -> RAIN_GT_40
RAIN_MODERATE_THRESHOLD: float = 25.0   # >= 25 mm/hr -> RAIN_GT_25
RAIN_LIGHT_THRESHOLD: float = 15.0      # < 15 mm/hr  -> RAIN_LT_15
RAIN_TRACE_THRESHOLD: float = 5.0       # < 5 mm/hr   -> RAIN_LT_5
RAIN_DRY_THRESHOLD: float = 1.0         # < 1 mm/hr   -> DRY_WEATHER

# Sustained 24h precipitation in mm
RAIN_SUSTAINED_24H_THRESHOLD: float = 50.0  # >= 50 mm/24h -> SUSTAINED_RAIN_24H

# Elevation bowl threshold (meters below surrounding neighbor median)
ELEVATION_BOWL_THRESHOLD_M: float = 2.0  # >= 2.0m depression -> LOW_LYING

# Proximity thresholds in meters
NEAR_LAKE_DIST_M: float = 600.0          # <= 600m to lake/water body -> NEAR_LAKE
LARGE_STP_DIST_M: float = 600.0          # <= 600m to STP / wastewater plant -> LARGE_STP_SITE_NEARBY
HOTSPOT_MAX_RADIUS_M: float = 800.0      # default maximum radius for chronic hotspots -> KNOWN_HOTSPOT

# Traffic slowdown threshold
TRAFFIC_SLOWDOWN_RATIO: float = 0.50     # current speed <= 50% freeflow speed -> TRAFFIC_SLOWDOWN
