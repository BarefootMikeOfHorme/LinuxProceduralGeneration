"""Inspect and render a mesh from the native LPG geometry core.

Renders an actual triangle mesh, not an idealised solid, so tessellation
defects are visible: pole fans, UV seams, winding, and non-manifold edges all
show up as what they are.

The mesh is obtained through the native extension and re-exported as OBJ, so
what gets drawn is exactly the geometry the Rust core produced.

Usage:
    python scripts/view_mesh.py sphere
    python scripts/view_mesh.py sphere --view wire --out temp
    python scripts/view_mesh.py box --width 100
    python scripts/view_mesh.py sphere --stats

Views:
    shaded   filled triangles with depth-buffered lighting (default)
    wire     triangle edges only, which exposes the tessellation
    points   vertices only, which exposes duplicates and the seam
    both     shaded with wireframe overlaid
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vaultmind_forge.forge_3d._native import NativeGeometryUnavailable, load_native  # noqa: E402

Point3 = tuple[float, float, float]
Face = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Mesh acquisition
# ---------------------------------------------------------------------------


def build_native(shape: str, size: float):
    """The native ``Mesh`` object itself, for callers that need its attributes."""
    try:
        native = load_native()
    except NativeGeometryUnavailable as exc:
        raise SystemExit(f"native geometry extension unavailable: {exc}") from exc

    if shape == "sphere":
        return native.create_sphere(size)
    if shape == "box":
        return native.create_box((size, size, size))
    if shape == "cylinder":
        return native.create_cylinder(size, size * 2.0)
    if shape == "cone":
        return native.create_cone(size, size * 2.0)
    if shape == "torus":
        return native.create_torus(size * 2.0, size * 0.5)
    raise SystemExit(f"unknown shape: {shape}")


def _triangles(flat: Sequence[int], label: str) -> list[Face]:
    if len(flat) % 3 != 0:
        raise SystemExit(f"{label}: index buffer is not a whole number of triangles")
    return [(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)]


def build_mesh(shape: str, size: float) -> tuple[list[Point3], list[Face]]:
    """Build a mesh with the native core and read its *topology* back.

    Read through the binding's ``vertices`` and ``indices`` accessors rather than
    by exporting OBJ and re-parsing it. The OBJ writer emits the render form,
    which splits positions at every crease and UV seam, so a round trip through
    it reports a cube as 36 vertices with 36 boundary edges and not one shared
    edge. Those numbers are artefacts of reading a render mesh rather than
    defects, and they are actively misleading in a tool whose whole job is
    showing whether a mesh is sound.
    """
    mesh = build_native(shape, size)
    vertices: list[Point3] = [tuple(v) for v in mesh.vertices]
    return vertices, _triangles(list(mesh.indices), shape)


def build_render_mesh(
    shape: str, size: float, smooth_angle: float = 180.0
) -> tuple[list[Point3], list[Face], list[Point3], list[tuple[float, float]]]:
    """Return ``(positions, faces, normals, uvs)`` for the render form.

    This is what a renderer actually uploads, so it answers "how big is this on
    the GPU" and "does this have usable UVs". The topology form answers "is this
    a sound solid". Both are worth seeing, and conflating them is exactly what
    made the old OBJ round trip misleading.
    """
    render = build_native(shape, size).split_for_render(smooth_angle)
    positions: list[Point3] = [tuple(v) for v in render.vertices]
    faces = _triangles(list(render.indices), f"{shape} render mesh")
    normals: list[Point3] = [tuple(n) for n in render.normals]
    uvs: list[tuple[float, float]] = [(float(u), float(v)) for u, v in render.uvs]
    return positions, faces, normals, uvs


def parse_obj(text: str) -> tuple[list[Point3], list[Face]]:
    """Minimal OBJ reader for the v and f lines a writer emits.

    Kept for reading OBJ files produced elsewhere. ``build_mesh`` no longer uses
    it, because the extension's own writer emits the render form, and reading a
    topology report back out of a render mesh is what produced misleading
    boundary-edge counts.
    """
    vertices: list[Point3] = []
    faces: list[Face] = []
    for line in text.splitlines():
        if line.startswith("v "):
            _, x, y, z = line.split()[:4]
            vertices.append((float(x), float(y), float(z)))
        elif line.startswith("f "):
            indices = []
            for token in line.split()[1:]:
                # Faces are written as v/vt/vn; only the position matters here.
                indices.append(int(token.split("/")[0]) - 1)
            if len(indices) == 3:
                faces.append((indices[0], indices[1], indices[2]))
    return vertices, faces


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def face_normal(a: Point3, b: Point3, c: Point3) -> Point3:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / length, ny / length, nz / length)


def signed_volume(vertices: Sequence[Point3], faces: Sequence[Face]) -> float:
    """Signed volume. Positive means outward-facing winding."""
    total = 0.0
    for i0, i1, i2 in faces:
        ax, ay, az = vertices[i0]
        bx, by, bz = vertices[i1]
        cx, cy, cz = vertices[i2]
        total += ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) + az * (bx * cy - by * cx)
    return total / 6.0


def edge_histogram(faces: Sequence[Face]) -> dict[tuple[int, int], int]:
    counts: dict[tuple[int, int], int] = {}
    for i0, i1, i2 in faces:
        for a, b in ((i0, i1), (i1, i2), (i2, i0)):
            key = (min(a, b), max(a, b))
            counts[key] = counts.get(key, 0) + 1
    return counts


def mesh_stats(vertices: Sequence[Point3], faces: Sequence[Face]) -> str:
    counts = edge_histogram(faces)
    used_once = sum(1 for n in counts.values() if n == 1)
    used_thrice = sum(1 for n in counts.values() if n > 2)
    degenerate = sum(
        1 for i0, i1, i2 in faces if len({vertices[i0], vertices[i1], vertices[i2]}) < 3
    )
    volume = signed_volume(vertices, faces)

    lines = [
        f"vertices        {len(vertices)}",
        f"triangles       {len(faces)}",
        f"unique edges    {len(counts)}",
        f"boundary edges  {used_once}",
        f"non-manifold    {used_thrice}",
        f"degenerate      {degenerate}",
        f"signed volume   {volume:.4f}  ({'outward' if volume > 0 else 'INWARD'} winding)",
    ]
    return "\n".join(lines)


def render_stats(shape: str, size: float, smooth_angle: float = 180.0) -> str:
    """Report the render form alongside the topology form.

    Kept separate because the two answer different questions. Topology answers "is
    this a sound solid": boundary and non-manifold edge counts mean something
    there and only there. The render form answers "what does a GPU upload",
    where the interesting numbers are the post-split vertex count, what that
    costs against the welded topology, and whether the UVs are usable at all.
    """
    mesh = build_native(shape, size)
    render = mesh.split_for_render(smooth_angle)
    uvs = {(round(u, 4), round(v, 4)) for u, v in render.uvs}
    topology = mesh.vertex_count
    rendered = render.vertex_count

    lines = [
        f"sharp edges     {mesh.sharp_edge_count}",
        f"face uv tri     {len(mesh.face_uvs)}",
        f"render verts    {rendered}"
        + (f"  ({rendered - topology:+d} vs topology)" if rendered != topology else ""),
        f"render uniq pos {render.unique_position_count}",
        f"render uvs      {len(uvs)} distinct" + ("  (DEGENERATE)" if len(uvs) == 1 else ""),
        f"smooth angle    {smooth_angle}",
    ]
    return "\n".join(lines)


def _uv_extent(uvs: Sequence[tuple[float, float]]) -> float:
    """Largest coordinate magnitude, so the layout is framed sensibly."""
    if not uvs:
        return 1.0
    return max(max(abs(u), abs(v)) for u, v in uvs) or 1.0


def uv_layout_svg(shape: str, size: float, smooth_angle: float = 180.0) -> str:
    """An SVG of how the render mesh's triangles land in UV space.

    The numbers say a cube has four distinct UV coordinates; they do not show
    *where* those land, or whether an island turned inside out, collapsed onto a
    line, or overlaps another one. Only drawing the layout catches a mapping that
    is numerically present and visually useless.
    """
    _positions, faces, _normals, uvs = build_render_mesh(shape, size, smooth_angle)
    if not faces or not uvs:
        return ""

    width = height = 320
    pad = 12
    scale = (min(width, height) - 2 * pad) / _uv_extent(uvs)

    def to_px(uv: tuple[float, float]) -> str:
        # SVG y grows downward while UV v grows upward, so v is flipped.
        return f"{pad + uv[0] * scale:.2f},{pad + (1.0 - uv[1]) * scale:.2f}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#0e1016"/>',
    ]
    for i0, i1, i2 in faces:
        points = f"{to_px(uvs[i0])} {to_px(uvs[i1])} {to_px(uvs[i2])}"
        parts.append(
            f'<polygon points="{points}" fill="none" stroke="#7fd1ff" '
            f'stroke-width="0.6" stroke-opacity="0.85"/>'
        )
    for uv in uvs:
        x, y = to_px(uv).split(",")
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.3" fill="#ffd479"/>')
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Light direction, pointing from the surface toward the camera. The camera looks
# down -Z in the rotated frame, so the light needs a positive Z component to
# illuminate what we can see. Chosen off-axis so shading shows form rather than a
# flat disc, and above-left so the terminator falls where it reads best.
_LIGHT = (-0.42, 0.55, 0.72)

# Brightest last. The ramp deliberately does not start with a space, so the
# shadowed side of a solid stays visible against the background instead of
# disappearing into it.
_RAMP = ".:-=+*#%@"


def light_direction() -> Point3:
    """The normalised light vector, in the same rotated space as the projection."""
    lx, ly, lz = _LIGHT
    length = math.sqrt(lx * lx + ly * ly + lz * lz)
    return (lx / length, ly / length, lz / length)


def project(
    points: Iterable[Point3], width: int, height: int
) -> dict[int, tuple[float, float, float]]:
    """Orthographic projection with a fixed rotation, fitted to the bounds.

    Returns (screen_x, screen_y, view_z) per vertex. The third component is the
    depth along the view axis and is what the z-buffer must test. Using screen
    coordinates for depth silently produces a sparse, mostly-blank image, which
    is what an earlier version of this script did.
    """
    pts = list(points)
    if not pts:
        return {}
    cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
    cz = (min(p[2] for p in pts) + max(p[2] for p in pts)) / 2
    span = (
        max(
            max(p[0] for p in pts) - min(p[0] for p in pts),
            max(p[1] for p in pts) - min(p[1] for p in pts),
            max(p[2] for p in pts) - min(p[2] for p in pts),
        )
        or 1.0
    )

    # Yaw about Y, then pitch about X, so the result reads as a 3/4 view. The
    # camera looks down -Z in the rotated frame, so larger view_z is nearer.
    yaw = math.radians(35.0)
    pitch = math.radians(-20.0)
    cy_, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    scale = min(width - 1, height - 1) * 0.44 / (span / 2)
    out: dict[int, tuple[float, float, float]] = {}
    for idx, (x, y, z) in enumerate(pts):
        dx, dy, dz = x - cx, y - cy, z - cz
        # yaw about Y
        rx = dx * cy_ + dz * sy
        rz = -dx * sy + dz * cy_
        # pitch about X
        ry = dy * cp - rz * sp
        view_z = dy * sp + rz * cp
        out[idx] = (width / 2 + rx * scale, height / 2 - ry * scale, view_z)
    return out


def render_ascii(
    vertices: Sequence[Point3],
    faces: Sequence[Face],
    width: int,
    height: int,
    view: str,
) -> str:
    """Depth-buffered ASCII render. Returns the finished frame."""
    projected = project(vertices, width, height)
    lx, ly, light_z = light_direction()

    # Depth buffer on view-space z. The camera looks down -Z in the rotated
    # frame, so a larger view_z is nearer and wins the test.
    depth = [-1e30] * (width * height)
    shade = [" "] * (width * height)
    ramp = _RAMP

    for i0, i1, i2 in faces:
        p0, p1, p2 = projected[i0], projected[i1], projected[i2]
        a, b, c = vertices[i0], vertices[i1], vertices[i2]
        n = face_normal(a, b, c)
        lambert = max(0.0, n[0] * lx + n[1] * ly + n[2] * light_z)

        min_x = max(0, int(min(p0[0], p1[0], p2[0])))
        max_x = min(width - 1, int(max(p0[0], p1[0], p2[0])) + 1)
        min_y = max(0, int(min(p0[1], p1[1], p2[1])))
        max_y = min(height - 1, int(max(p0[1], p1[1], p2[1])) + 1)
        if min_x > max_x or min_y > max_y:
            continue

        # Barycentric fill in screen space.
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-9:
            continue
        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                l1 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / d
                l2 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / d
                l3 = 1.0 - l1 - l2
                if l1 < 0 or l2 < 0 or l3 < 0:
                    continue
                z = l1 * p0[2] + l2 * p1[2] + l3 * p2[2]
                idx = py * width + px
                if z > depth[idx]:
                    depth[idx] = z
                    shade[idx] = ramp[min(len(ramp) - 1, int(lambert * (len(ramp) - 1)))]

    if view in ("wire", "both"):
        _overlay_wire(vertices, faces, projected, width, height, shade)

    if view == "points":
        for idx, (sx, sy, _z) in projected.items():
            xi, yi = int(sx), int(sy)
            if 0 <= xi < width and 0 <= yi < height:
                shade[yi * width + xi] = "o"

    return "\n".join("".join(shade[r * width : (r + 1) * width]) for r in range(height))


def _overlay_wire(
    vertices: Sequence[Point3],
    faces: Sequence[Face],
    projected: dict,
    width: int,
    height: int,
    shade: list[str],
) -> None:
    """Draw triangle edges over an existing frame."""
    for i0, i1, i2 in faces:
        for a, b in ((i0, i1), (i1, i2), (i2, i0)):
            pa, pb = projected[a][:2], projected[b][:2]
            steps = int(max(abs(pb[0] - pa[0]), abs(pb[1] - pa[1]))) + 1
            for s in range(steps + 1):
                t = s / steps if steps else 0.0
                x = pa[0] + (pb[0] - pa[0]) * t
                y = pa[1] + (pb[1] - pa[1]) * t
                xi, yi = int(x), int(y)
                if 0 <= xi < width and 0 <= yi < height:
                    idx = yi * width + xi
                    if shade[idx] == " ":
                        shade[idx] = "."


def render_png(
    vertices: Sequence[Point3],
    faces: Sequence[Face],
    size: int,
    view: str,
    out_path: Path,
) -> Path:
    """Rasterise with a z-buffer and write a PNG via Pillow."""
    from PIL import Image, ImageDraw

    width = height = size
    projected = project(vertices, width, height)
    lx, ly, light_z = light_direction()

    image = Image.new("RGB", (width, height), (14, 16, 22))
    draw = ImageDraw.Draw(image)
    depth = [-1e30] * (width * height)

    for i0, i1, i2 in faces:
        p0, p1, p2 = projected[i0], projected[i1], projected[i2]
        a, b, c = vertices[i0], vertices[i1], vertices[i2]
        n = face_normal(a, b, c)
        lambert = max(0.0, n[0] * lx + n[1] * ly + n[2] * light_z)
        intensity = 0.18 + 0.82 * lambert
        base = (int(120 * intensity), int(190 * intensity), int(235 * intensity))

        min_x = max(0, int(min(p0[0], p1[0], p2[0])))
        max_x = min(width - 1, int(max(p0[0], p1[0], p2[0])) + 1)
        min_y = max(0, int(min(p0[1], p1[1], p2[1])))
        max_y = min(height - 1, int(max(p0[1], p1[1], p2[1])) + 1)
        if min_x > max_x or min_y > max_y:
            continue

        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-9:
            continue

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                l1 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / d
                l2 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / d
                l3 = 1.0 - l1 - l2
                if l1 < 0 or l2 < 0 or l3 < 0:
                    continue
                z = l1 * p0[2] + l2 * p1[2] + l3 * p2[2]
                idx = py * width + px
                if z > depth[idx]:
                    depth[idx] = z
                    image.putpixel((px, py), base)

    if view in ("wire", "both"):
        for i0, i1, i2 in faces:
            a2 = projected[i0][:2]
            b2 = projected[i1][:2]
            c2 = projected[i2][:2]
            draw.line([a2, b2], fill=(255, 255, 255), width=1)
            draw.line([b2, c2], fill=(255, 255, 255), width=1)
            draw.line([c2, a2], fill=(255, 255, 255), width=1)

    if view == "points":
        for idx, (sx, sy, _z) in projected.items():
            draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], outline=(255, 220, 120))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "shape",
        nargs="?",
        default="sphere",
        choices=["sphere", "box", "cylinder", "cone", "torus"],
    )
    parser.add_argument("--size", type=float, default=1.0)
    parser.add_argument("--view", default="shaded", choices=["shaded", "wire", "points", "both"])
    parser.add_argument("--width", type=int, default=96)
    parser.add_argument("--height", type=int, default=40)
    parser.add_argument("--png", type=int, default=0, help="also write a PNG of this size")
    parser.add_argument("--out", default="", help="PNG output path, else a temp file")
    parser.add_argument("--stats", action="store_true", help="print mesh statistics")
    parser.add_argument(
        "--smooth",
        type=float,
        default=180.0,
        help="auto-smooth angle in degrees for the render form (default 180)",
    )
    parser.add_argument(
        "--uv-svg",
        default="",
        help="write an SVG of the render mesh's UV layout to this path",
    )
    args = parser.parse_args()

    vertices, faces = build_mesh(args.shape, args.size)

    if args.stats:
        print(f"{args.shape} mesh - topology (welded)")
        print(mesh_stats(vertices, faces))
        print()
        print(f"{args.shape} mesh - render form")
        print(render_stats(args.shape, args.size, args.smooth))
        print()

    print(render_ascii(vertices, faces, args.width, args.height, args.view))

    if args.uv_svg:
        svg = uv_layout_svg(args.shape, args.size, args.smooth)
        if not svg:
            raise SystemExit(f"{args.shape}: no render mesh to map into UV space")
        target = Path(args.uv_svg)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg, encoding="utf-8")
        print(f"\nUV layout written to {target}")

    if args.png:
        target = (
            Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"lpg_{args.shape}.png"
        )
        written = render_png(vertices, faces, args.png, args.view, target)
        print(f"PNG written to {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
