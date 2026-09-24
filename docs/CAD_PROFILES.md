# LPG CAD Profiles

LPG is provider-neutral and backend-neutral. CAD engines are selected per task;
none is embedded as the creative authority.

## Recommended starter

### build123d default runtime

build123d is the default Python B-rep/CAD-as-code runtime for LPG and is
included in the base package dependencies. It is the first backend LPG will
exercise because it gives the Python core a programmable, precise B-rep
kernel while remaining separate from the Rust mesh engine.

The setup wizard may later offer a dedicated CAD worker profile, but the
default LPG environment includes build123d.

### FreeCAD secondary application

FreeCAD is the recommended secondary application for users who want a
graphical CAD experience and a headless automation path. The wizard can detect
or add it later.

- GUI: interactive parametric modeling and document editing
- Headless: `FreeCADCmd`
- Typical interchange: STEP, IGES, FCStd, STL, OBJ
- LPG role: external worker, not a core Python dependency
- Recommended boundary: isolated process/container with explicit job files

FreeCAD is useful for users who want to inspect and edit a complete CAD
 document, including assemblies and document history.

## Default build123d profile

`build123d` is appropriate for:

- AI-generated Python B-rep models
- STEP/STL generation
- Reproducible geometry programs
- Headless Python workers
- Comparing build123d with other OCCT-backed adapters

It is installed with the base LPG package. LPG should still run untrusted
build123d jobs in a dedicated worker until packaging and resource behavior are
validated across supported platforms.

## Other backends

- CadQuery: alternative Python B-rep adapter
- OpenSCAD: lightweight procedural CSG and `.scad` generation
- Blender: scene composition, rendering, animation, and visual assets
- LPG Rust/PyO3: native mesh primitives, OBJ, validation, and geometry tools

## Worker contract

Every CAD backend must provide:

- Backend name and version
- Input/output capability declaration
- Source and target formats
- Resource limits and timeout
- Output path and digest
- Conversion loss status
- Independent output validation
- Provenance and source asset identity

The canonical result is the LPG `ConversionEnvelope`. A successful process exit
alone is not proof of a valid conversion.

## Licensing

LPG currently has a proprietary distribution profile. CAD workers should remain
separate processes or containers until license review is complete.

- OpenSCAD: GPL-2.0 with its stated CGAL linking exception; review bundled
  binaries and libraries separately.
- FreeCAD: LGPL-2.1-or-later; preserve notices and satisfy redistribution
  obligations when distributing it.
- build123d: Apache-2.0; its OpenCascade/OCP dependencies have their own
  LGPL and notice obligations.
- Third-party CAD libraries and imported models must be audited independently.

This document is an engineering guide, not legal advice.
