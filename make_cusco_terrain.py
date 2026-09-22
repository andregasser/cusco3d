#!/usr/bin/env python3
"""Create a watertight STL terrain relief from an SRTM HGT tile.

Default: a 20 x 20 km area centred on Cusco, scaled to 150 x 150 mm.
"""
from __future__ import annotations

import argparse
import gzip
import math
import struct
import re
from pathlib import Path


CITY_LAT = -13.53195
CITY_LON = -71.96746
TILE_SIZE = 3601


def read_hgt(path: Path):
    raw = gzip.open(path, "rb").read() if path.suffix == ".gz" else path.read_bytes()
    expected = TILE_SIZE * TILE_SIZE * 2
    if len(raw) != expected:
        raise ValueError(f"Expected {expected} bytes, got {len(raw)}")
    vals = struct.unpack(f">{TILE_SIZE * TILE_SIZE}h", raw)
    return vals

def read_mosaic(folder: Path):
    tiles={}
    for path in folder.glob('[NS]*W*.hgt.gz'):
        m=re.match(r'([NS])(\d+)([EW])(\d+)\.hgt\.gz$',path.name)
        if not m: continue
        lat0=(-1 if m.group(1)=='S' else 1)*int(m.group(2))
        lon0=(-1 if m.group(3)=='W' else 1)*int(m.group(4))
        tiles[(lat0,lon0)]=read_hgt(path)
    return tiles

def sample_mosaic(tiles, lat, lon):
    lat0=math.floor(lat); lon0=math.floor(lon)
    data=tiles[(lat0,lon0)]
    x=(lon-lon0)*(TILE_SIZE-1); y=(lat0+1-lat)*(TILE_SIZE-1)
    x=max(0.0,min(TILE_SIZE-1.001,x)); y=max(0.0,min(TILE_SIZE-1.001,y))
    x0,y0=int(x),int(y); tx,ty=x-x0,y-y0
    a=data[y0*TILE_SIZE+x0]; b=data[y0*TILE_SIZE+x0+1]
    c=data[(y0+1)*TILE_SIZE+x0]; d=data[(y0+1)*TILE_SIZE+x0+1]
    return (a*(1-tx)+b*tx)*(1-ty)+(c*(1-tx)+d*tx)*ty


def bilinear(data, lat: float, lon: float) -> float:
    """SRTM rows run north-to-south, columns west-to-east."""
    x = (lon - math.floor(lon)) * (TILE_SIZE - 1)
    y = (math.ceil(lat) - lat) * (TILE_SIZE - 1)
    x = max(0.0, min(TILE_SIZE - 1.001, x))
    y = max(0.0, min(TILE_SIZE - 1.001, y))
    x0, y0 = int(x), int(y)
    tx, ty = x - x0, y - y0
    a = data[y0 * TILE_SIZE + x0]
    b = data[y0 * TILE_SIZE + x0 + 1]
    c = data[(y0 + 1) * TILE_SIZE + x0]
    d = data[(y0 + 1) * TILE_SIZE + x0 + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def write_triangle(f, a, b, c):
    f.write(struct.pack("<3f", *normal(a, b, c)))
    f.write(struct.pack("<9f", *(a + b + c)))
    f.write(struct.pack("<H", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hgt", type=Path, default=Path("data/S14W072.hgt.gz"))
    ap.add_argument("--out", type=Path, default=Path("output/cusco_terrain_150mm.stl"))
    ap.add_argument("--size-mm", type=float, default=150.0)
    ap.add_argument("--area-km", type=float, default=20.0)
    ap.add_argument("--grid", type=int, default=240, help="top-surface samples per side")
    ap.add_argument("--height-scale", type=float, default=0.018, help="mm of relief per metre")
    ap.add_argument("--base-mm", type=float, default=4.0)
    args = ap.parse_args()
    if args.grid < 2:
        ap.error("--grid must be at least 2")

    tiles = read_mosaic(args.hgt.parent)
    half_lat = args.area_km / 2 / 111.32
    half_lon = args.area_km / 2 / (111.32 * math.cos(math.radians(CITY_LAT)))
    south, north = CITY_LAT - half_lat, CITY_LAT + half_lat
    west, east = CITY_LON - half_lon, CITY_LON + half_lon

    heights = []
    for j in range(args.grid):
        lat = south + (north - south) * j / (args.grid - 1)
        for i in range(args.grid):
            lon = west + (east - west) * i / (args.grid - 1)
            heights.append(sample_mosaic(tiles, lat, lon))
    low = min(heights)
    verts = []
    for j in range(args.grid):
        for i in range(args.grid):
            x = args.size_mm * i / (args.grid - 1)
            y = args.size_mm * j / (args.grid - 1)
            z = args.base_mm + (heights[j * args.grid + i] - low) * args.height_scale
            verts.append((x, y, z))
    bottom = [(x, y, 0.0) for x, y, _ in verts]
    args.out.parent.mkdir(parents=True, exist_ok=True)

    triangles = []
    n = args.grid
    for j in range(n - 1):
        for i in range(n - 1):
            k = j * n + i
            triangles += [(verts[k], verts[k + 1], verts[k + n]),
                          (verts[k + 1], verts[k + n + 1], verts[k + n])]
    # Four vertical perimeter walls, with outward-facing winding.
    for i in range(n - 1):
        triangles += [(verts[i], bottom[i], bottom[i + 1]), (verts[i], bottom[i + 1], verts[i + 1])]
        k = (n - 1) * n + i
        triangles += [(verts[k], verts[k + 1], bottom[k + 1]), (verts[k], bottom[k + 1], bottom[k])]
    for j in range(n - 1):
        k = j * n
        triangles += [(verts[k], verts[k + n], bottom[k + n]), (verts[k], bottom[k + n], bottom[k])]
        k = j * n + n - 1
        triangles += [(verts[k], bottom[k], bottom[k + n]), (verts[k], bottom[k + n], verts[k + n])]
    # Bottom, viewed from underneath.
    for j in range(n - 1):
        for i in range(n - 1):
            k = j * n + i
            triangles += [(bottom[k], bottom[k + n], bottom[k + 1]),
                          (bottom[k + 1], bottom[k + n], bottom[k + n + 1])]

    with args.out.open("wb") as f:
        header = b"Cusco Peru terrain relief - SRTM".ljust(80, b" ")
        f.write(header[:80])
        f.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            write_triangle(f, *tri)
    print(f"Wrote {args.out} ({len(triangles):,} triangles)")
    print(f"Elevation: {low:.0f}-{max(heights):.0f} m | overall height: {args.base_mm + (max(heights)-low)*args.height_scale:.1f} mm")


if __name__ == "__main__":
    main()
