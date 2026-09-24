"""
VaultMind Forge - OpenSCAD Import
=================================

Import .scad files by rendering them to meshes using OpenSCAD command-line.

Features:
    - Render .scad files to validated OBJ meshes
    - Batch rendering of multiple .scad files
    - Parameter override for parametric designs
    - Automatic detection of OpenSCAD executable
    - Progress tracking for long renders

Usage:
    >>> from vaultmind_forge.forge_3d.openscad_import import OpenSCADImporter
    >>> from vaultmind_forge.forge_3d.mesh import Mesh
    >>>
    >>> importer = OpenSCADImporter()
    >>> mesh = importer.scad_to_mesh("my_design.scad")
    >>> mesh.stats()
    >>> mesh.to_unity("exports/unity/my_design.obj")
"""

from pathlib import Path
from typing import Optional, Dict, List, Union
import os
import platform
import shutil
import subprocess
import tempfile
import time


def _find_openscad() -> Optional[Path]:
    """Find OpenSCAD using explicit configuration, PATH, or common locations."""
    configured = os.getenv("OPENSCAD_PATH")
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())

    for command in ("openscad", "openscad.exe"):
        discovered = shutil.which(command)
        if discovered:
            candidates.append(Path(discovered))

    system = platform.system()
    if system == "Windows":
        for root in (os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)")):
            if root:
                candidates.append(Path(root) / "OpenSCAD" / "openscad.exe")
    elif system == "Darwin":
        candidates.append(
            Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
        )
    else:
        candidates.extend(
            [
                Path("/usr/bin/openscad"),
                Path("/usr/local/bin/openscad"),
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


class OpenSCADImporter:
    """
    Import .scad files by rendering them using OpenSCAD command-line.

    Converts parametric CAD designs to meshes for game engines.
    """

    def __init__(self, openscad_path: Optional[str] = None):
        """
        Initialize importer.

        Args:
            openscad_path: Path to OpenSCAD executable (auto-detected if None)
        """
        if openscad_path is None:
            discovered = _find_openscad()
            self.openscad_path = str(discovered) if discovered is not None else ""
        else:
            self.openscad_path = str(Path(openscad_path).expanduser())

        self.openscad_available = bool(self.openscad_path) and Path(self.openscad_path).is_file()

        if not self.openscad_available:
            location = self.openscad_path or "PATH/common locations"
            print(f"[WARNING] OpenSCAD not found at: {location}")
            print("[INFO] Set OPENSCAD_PATH or pass openscad_path explicitly")

    def scad_to_mesh(self, scad_file: str,
                     output_format: str = "obj",
                     output_path: Optional[str] = None,
                     parameters: Optional[Dict[str, Union[int, float, str]]] = None,
                     timeout: int = 60) -> 'Mesh':
        """
        Render .scad file to mesh using OpenSCAD.

        Args:
            scad_file: Path to .scad file
            output_format: Output format. Only ``obj`` is currently validated.
            output_path: Output file path (auto-generated if None)
            parameters: Dict of parameter overrides (e.g., {"radius": 2.0})
            timeout: Render timeout in seconds

        Returns:
            Mesh object from rendered geometry
        """
        if not self.openscad_available:
            location = self.openscad_path or "PATH/common locations"
            raise RuntimeError(f"OpenSCAD not found at: {location}")

        normalized_format = output_format.lower().lstrip(".")
        if normalized_format != "obj":
            raise ValueError(
                f"Unsupported OpenSCAD output format '{output_format}'; "
                "only OBJ is currently validated"
            )
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        scad_path = Path(scad_file)
        if not scad_path.exists():
            raise FileNotFoundError(f"SCAD file not found: {scad_file}")

        # Generate output path
        if output_path is None:
            output_path = scad_path.with_suffix(f".{normalized_format}")
        else:
            output_path = Path(output_path)
            if output_path.suffix and output_path.suffix.lower() != f".{normalized_format}":
                raise ValueError(
                    f"Output path extension must match .{normalized_format}: {output_path}"
                )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [self.openscad_path]

        # Add parameter overrides
        if parameters:
            for key, value in parameters.items():
                # Format parameter based on type
                if isinstance(value, str):
                    param_str = f'{key}="{value}"'
                else:
                    param_str = f"{key}={value}"
                cmd.extend(["-D", param_str])

        # Add output and input
        cmd.extend(["-o", str(output_path), str(scad_path)])

        # Render
        print(f"[INFO] Rendering: {scad_path.name}")
        if parameters:
            print(f"[INFO] Parameters: {parameters}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                print(f"[ERROR] OpenSCAD render failed:")
                print(result.stderr)
                raise RuntimeError("OpenSCAD rendering failed")

            print(f"[OK] Rendered to: {output_path}")

            # Load the rendered mesh through the explicit native loader.
            from ._native import load_native
            from .mesh import Mesh
            vfc = load_native()

            # Load the rendered mesh
            rust_mesh = vfc.load_obj(str(output_path))
            mesh = Mesh(rust_mesh)

            return mesh

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Rendering timed out after {timeout}s")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to render: {e}")
            raise

    def batch_render(self, scad_files: List[str],
                    output_dir: str,
                    output_format: str = "obj",
                    timeout_per_file: int = 60) -> List['Mesh']:
        """
        Render multiple .scad files in batch.

        Args:
            scad_files: List of .scad file paths
            output_dir: Output directory for rendered meshes
            output_format: Output format. Only ``obj`` is currently validated.
            timeout_per_file: Timeout per file in seconds

        Returns:
            List of Mesh objects
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        meshes = []
        total = len(scad_files)

        print(f"\n[INFO] Batch rendering {total} files...")

        for i, scad_file in enumerate(scad_files, 1):
            print(f"\n[{i}/{total}] Processing: {Path(scad_file).name}")

            try:
                # Generate output path
                output_file = output_path / f"{Path(scad_file).stem}.{output_format}"

                # Render
                mesh = self.scad_to_mesh(
                    scad_file,
                    output_format=output_format,
                    output_path=str(output_file),
                    timeout=timeout_per_file
                )

                meshes.append(mesh)
                print(f"[OK] {i}/{total} complete")

            except Exception as e:
                print(f"[ERROR] Failed to render {scad_file}: {e}")
                continue

        print(f"\n[OK] Batch render complete: {len(meshes)}/{total} succeeded")
        return meshes

    def render_with_variations(self, scad_file: str,
                              parameter_variations: List[Dict],
                              output_dir: str,
                              output_format: str = "obj") -> List['Mesh']:
        """
        Render same .scad file with different parameter sets.

        Useful for generating variations of parametric designs.

        Args:
            scad_file: Path to .scad file
            parameter_variations: List of parameter dicts
            output_dir: Output directory
            output_format: Output format. Only ``obj`` is currently validated.

        Returns:
            List of Mesh objects

        Example:
            >>> variations = [
            ...     {"radius": 1.0, "height": 2.0},
            ...     {"radius": 1.5, "height": 2.5},
            ...     {"radius": 2.0, "height": 3.0},
            ... ]
            >>> meshes = importer.render_with_variations(
            ...     "cone.scad", variations, "outputs/variations"
            ... )
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        scad_path = Path(scad_file)
        meshes = []
        total = len(parameter_variations)

        print(f"\n[INFO] Rendering {total} variations of: {scad_path.name}")

        for i, params in enumerate(parameter_variations, 1):
            print(f"\n[{i}/{total}] Variation: {params}")

            # Generate unique output name
            param_str = "_".join(f"{k}{v}" for k, v in params.items())
            output_file = output_path / f"{scad_path.stem}_{param_str}.{output_format}"

            try:
                mesh = self.scad_to_mesh(
                    scad_file,
                    output_format=output_format,
                    output_path=str(output_file),
                    parameters=params
                )

                meshes.append(mesh)
                print(f"[OK] {i}/{total} complete")

            except Exception as e:
                print(f"[ERROR] Failed variation {i}: {e}")
                continue

        print(f"\n[OK] Variations complete: {len(meshes)}/{total} succeeded")
        return meshes

    def scad_to_obj(self, scad_file: str, output_path: Optional[str] = None,
                   parameters: Optional[Dict] = None) -> str:
        """
        Convenience method: Render .scad to OBJ file.

        Args:
            scad_file: Path to .scad file
            output_path: Output OBJ path
            parameters: Parameter overrides

        Returns:
            Path to rendered OBJ file
        """
        mesh = self.scad_to_mesh(
            scad_file,
            output_format="obj",
            output_path=output_path,
            parameters=parameters
        )

        # Return the output path
        if output_path:
            return output_path
        else:
            return str(Path(scad_file).with_suffix(".obj"))

    def scad_to_stl(self, scad_file: str, output_path: Optional[str] = None,
                   parameters: Optional[Dict] = None) -> str:
        """
        Convenience method: Render .scad to STL file.

        Args:
            scad_file: Path to .scad file
            output_path: Output STL path
            parameters: Parameter overrides

        Returns:
            Path to rendered STL file
        """
        mesh = self.scad_to_mesh(
            scad_file,
            output_format="stl",
            output_path=output_path,
            parameters=parameters
        )

        # Return the output path
        if output_path:
            return output_path
        else:
            return str(Path(scad_file).with_suffix(".stl"))

    def preview_render(self, scad_file: str, parameters: Optional[Dict] = None) -> bool:
        """
        Open OpenSCAD for interactive preview (no rendering).

        Args:
            scad_file: Path to .scad file
            parameters: Parameter overrides to apply

        Returns:
            True if opened successfully
        """
        if not self.openscad_available:
            print(f"[WARNING] OpenSCAD not found at: {self.openscad_path}")
            return False

        scad_path = Path(scad_file)
        if not scad_path.exists():
            print(f"[ERROR] File not found: {scad_file}")
            return False

        try:
            # If parameters provided, create temp file with overrides
            if parameters:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as temp_file:
                    # Write parameter overrides
                    for key, value in parameters.items():
                        if isinstance(value, str):
                            temp_file.write(f'{key} = "{value}";\n')
                        else:
                            temp_file.write(f"{key} = {value};\n")

                    # Include original file
                    temp_file.write(f'\ninclude <{scad_path.absolute()}>\n')
                    temp_path = temp_file.name

                subprocess.Popen([self.openscad_path, temp_path])
                print(f"[OK] Opened preview with parameters: {parameters}")
            else:
                subprocess.Popen([self.openscad_path, str(scad_path)])
                print(f"[OK] Opened preview: {scad_path.name}")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to open preview: {e}")
            return False


class OpenSCADRoundTrip:
    """
    Helper class for round-trip editing workflow.

    VaultMind Forge --> .scad --> OpenSCAD (edit) --> .obj --> VaultMind Forge
    """

    def __init__(self):
        from .openscad_export import OpenSCADExporter
        self.exporter = OpenSCADExporter()
        self.importer = OpenSCADImporter()

    def export_edit_import(self, primitive, name: str,
                          working_dir: str = "temp/openscad",
                          auto_open: bool = True) -> 'Mesh':
        """
        Complete round-trip workflow.

        1. Export primitive to .scad
        2. Open in OpenSCAD for editing
        3. Wait for user to save changes
        4. Re-import modified geometry

        Args:
            primitive: VaultMind primitive
            name: Object name
            working_dir: Temporary working directory
            auto_open: Automatically open OpenSCAD

        Returns:
            Modified mesh
        """
        working_path = Path(working_dir)
        working_path.mkdir(parents=True, exist_ok=True)

        # Export to .scad
        scad_path = working_path / f"{name}.scad"
        self.exporter.export_primitive(primitive, str(scad_path), name=name, parametric=True)

        if auto_open:
            print("\n[INFO] Opening in OpenSCAD...")
            print("[ACTION] Edit parameters, preview (F5), render (F6)")
            print("[ACTION] When done, SAVE and press Enter here to continue...")

            self.exporter.open_in_openscad(str(scad_path))

            # Wait for user
            input("\n[WAITING] Press Enter when finished editing in OpenSCAD... ")

        # Re-import
        print("\n[INFO] Re-importing modified geometry...")
        mesh = self.importer.scad_to_mesh(str(scad_path))

        print("[OK] Round-trip complete!")
        return mesh


__all__ = ["OpenSCADImporter", "OpenSCADRoundTrip"]
