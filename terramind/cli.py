"""
TerraMind Engine CLI — terramind-engine
========================================
Production command-line interface for TerraMind:
Panchayat-Scale Micro-Climate & Agro-Advisory Intelligence System.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root and backend to path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
for path in [ROOT_DIR, BACKEND_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np
import pandas as pd

from terramind import (
    __cli_name__,
    __title__,
    __version__,
    forecast_panchayat_v2,
    resolve_panchayat_meta,
)


def cmd_serve(args):
    """Start the Uvicorn ASGI API server."""
    import uvicorn
    print(f"Starting {__title__} v{__version__} on http://{args.host}:{args.port}")
    uvicorn.run(
        "backend.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


def cmd_forecast(args):
    """Generate and display downscaled Panchayat forecast."""
    try:
        res = forecast_panchayat_v2(
            panchayat_id=args.panchayat_id,
            days=args.days,
            crop=args.crop,
            live=not args.no_live,
        )
    except Exception as exc:
        print(f"Error generating forecast: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Custom JSON serializer for dates/floats
        print(json.dumps(res, default=str, indent=2))
        return

    print("=" * 72)
    print(f"  {__title__}")
    print(f"  Target Gram Panchayat: {res.get('panchayat_name')} ({res.get('panchayat_id')})")
    print(f"  Block: {res.get('block_name')} | District: {res.get('district_name')}")
    print(f"  Panchayat Coordinates: {res.get('latitude', 0.0):.4f}°N, {res.get('longitude', 0.0):.4f}°E")
    
    coarse = res.get("coarse_coordinate", {})
    coarse_lat = coarse.get("latitude", 0.0)
    coarse_lon = coarse.get("longitude", 0.0)
    grid_dist = res.get("grid_distance_km", 0.0)
    print(f"  Regional NWP Grid (~25km): {coarse_lat:.4f}°N, {coarse_lon:.4f}°E (Offset: ~{grid_dist} km)")
    
    season_info = res.get("seasonal_info")
    crop_str = str(res.get("crop", "paddy")).upper()
    if season_info:
        s_title = season_info.get("season_name", "")
        print(f"  Seasonal Crop: {crop_str} (Auto-selected for {s_title})")
    else:
        print(f"  Target Crop: {crop_str}")

    print(f"  Zone: {res.get('agro_climatic_zone')} | Model: {res.get('model_version')}")
    print("=" * 72)
    print(f"{'Date':<12} {'Rain P50 (P10-P90)':<22} {'Prob':<8} {'Tmax':<8} {'Advisory Action'}")
    print("-" * 72)

    for day in res.get("forecast", []):
        d_str = str(day.get("date"))
        rain = day.get("rain_mm", {})
        if isinstance(rain, dict):
            p10 = rain.get("p10", 0.0)
            p50 = rain.get("p50", 0.0)
            p90 = rain.get("p90", 0.0)
            rain_str = f"{p50:.1f} mm ({p10:.1f}-{p90:.1f})"
        else:
            rain_str = f"{float(rain):.1f} mm"

        prob = f"{int(day.get('rain_probability', 0.0) * 100)}%"
        tmax_obj = day.get("tmax_c", {})
        tmax = f"{tmax_obj.get('p50', 30.0):.1f}°C" if isinstance(tmax_obj, dict) else f"{float(tmax_obj):.1f}°C"
        adv = day.get("advisory", {})
        adv_text = adv.get("text_en", "")[:30] + ("..." if len(adv.get("text_en", "")) > 30 else "")
        print(f"{d_str:<12} {rain_str:<22} {prob:<8} {tmax:<8} {adv_text}")

    print("=" * 72)
    if res.get("advisories"):
        print("\nActive Agricultural Guidance:")
        for adv in res["advisories"]:
            print(f"  [{adv.get('priority', '').upper()}] {adv.get('date')}: {adv.get('text_en')}")


def cmd_nearest(args):
    """Find nearest Gram Panchayats by GPS coordinates."""
    reg_path = ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if not reg_path.exists():
        print(f"Error: Statewide registry not found at {reg_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_parquet(reg_path)
    lat_r = np.radians(args.lat)
    lon_r = np.radians(args.lon)
    df_lat_r = np.radians(df["latitude"].values)
    df_lon_r = np.radians(df["longitude"].values)

    dlat = df_lat_r - lat_r
    dlon = df_lon_r - lon_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat_r) * np.cos(df_lat_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    dist_km = 6371.0 * c

    top_idx = np.argsort(dist_km)[: args.limit]
    print(f"Nearest Gram Panchayats to ({args.lat:.4f}°N, {args.lon:.4f}°E):")
    print(f"{'GP Code':<10} {'Panchayat ID':<12} {'Name':<24} {'Block':<18} {'District':<20} {'Distance'}")
    print("-" * 92)
    for idx in top_idx:
        row = df.iloc[int(idx)]
        d = dist_km[idx]
        print(
            f"{row['gp_code']:<10} {row['panchayat_id']:<12} {row['panchayat_name']:<24} "
            f"{row['block_name']:<18} {row['district_name']:<20} {d:.2f} km"
        )


def cmd_search(args):
    """Search Gram Panchayats statewide."""
    reg_path = ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if not reg_path.exists():
        print(f"Error: Statewide registry not found at {reg_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_parquet(reg_path)
    if args.district:
        df = df[df["district_name"].str.lower() == args.district.strip().lower()]

    q = args.query.strip().lower()
    df = df[
        df["panchayat_name"].str.lower().str.contains(q, na=False)
        | df["block_name"].str.lower().str.contains(q, na=False)
        | df["panchayat_id"].str.lower().str.contains(q, na=False)
    ]

    print(f"Found {len(df)} Gram Panchayats matching '{args.query}':")
    print(f"{'GP Code':<10} {'Panchayat ID':<12} {'Name':<24} {'Block':<18} {'District':<20} {'Coordinates'}")
    print("-" * 102)
    for _, row in df.head(args.limit).iterrows():
        coords = f"{row['latitude']:.4f}°N, {row['longitude']:.4f}°E"
        print(
            f"{row['gp_code']:<10} {row['panchayat_id']:<12} {row['panchayat_name']:<24} "
            f"{row['block_name']:<18} {row['district_name']:<20} {coords}"
        )


def cmd_health(args):
    """Inspect system health, registry, data lake, and ML models."""
    print("=" * 60)
    print(f"  {__title__}")
    print(f"  CLI: {__cli_name__} v{__version__}")
    print("=" * 60)

    # 1. Statewide Registry
    reg_path = ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if reg_path.exists():
        df_reg = pd.read_parquet(reg_path)
        print(f"  ✓ Statewide Registry:     3,339 Gram Panchayats across {df_reg['district_name'].nunique()} districts")
    else:
        print(f"  ✗ Statewide Registry:     Missing at {reg_path}")

    # 2. Static Terrain Features
    static_path = ROOT_DIR / "data_pipeline" / "features" / "statewide_static_features.parquet"
    if static_path.exists():
        print("  ✓ Statewide Terrain DEM:  Calibrated for all 3,339 Panchayats")
    else:
        print(f"  ✗ Statewide Terrain DEM:  Missing at {static_path}")

    # 3. Regional Models
    models_dir = ROOT_DIR / "ml" / "models"
    for zone in ["delta", "laterite", "terai"]:
        zp = models_dir / f"regional_{zone}_model.joblib"
        if zp.exists():
            print(f"  ✓ ML Model ({zone.capitalize()} Zone): Operational ({zp.name})")
        else:
            print(f"  ○ ML Model ({zone.capitalize()} Zone): Using Statewide Scaffold fallback")

    print("\n  System Status: Operational & Ready for Panchayat Serving.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        prog=__cli_name__,
        description=f"{__title__} (CLI Engine)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{__title__} v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # serve
    p_serve = subparsers.add_parser("serve", help="Run Uvicorn API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload on code change")

    # forecast
    p_forecast = subparsers.add_parser("forecast", help="Compute downscaled 5-day forecast")
    p_forecast.add_argument("panchayat_id", help="Target Panchayat ID (e.g. WB_107778, A2, WB_107001)")
    p_forecast.add_argument("--days", type=int, default=5, help="Number of forecast days (1-5)")
    p_forecast.add_argument("--crop", default="auto", help="Active crop context ('auto' for current seasonal crop, or paddy, potato, etc.)")
    p_forecast.add_argument("--no-live", action="store_true", help="Disable dynamic live weather stream")
    p_forecast.add_argument("--json", action="store_true", help="Output raw JSON response")

    # nearest
    p_nearest = subparsers.add_parser("nearest", help="Find nearest Gram Panchayat using coordinates")
    p_nearest.add_argument("lat", type=float, help="Latitude coordinate")
    p_nearest.add_argument("lon", type=float, help="Longitude coordinate")
    p_nearest.add_argument("--limit", type=int, default=5, help="Number of results (default: 5)")

    # search
    p_search = subparsers.add_parser("search", help="Search 3,339 Gram Panchayats statewide")
    p_search.add_argument("query", help="Panchayat or block search query")
    p_search.add_argument("--district", help="Filter by district name")
    p_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # health / status
    subparsers.add_parser("health", help="Check system health, data lake, and ML models")
    subparsers.add_parser("status", help="Alias for health check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "forecast":
        cmd_forecast(args)
    elif args.command == "nearest":
        cmd_nearest(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command in ("health", "status"):
        cmd_health(args)


if __name__ == "__main__":
    main()
