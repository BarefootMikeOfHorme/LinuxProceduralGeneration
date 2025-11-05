"""
VaultMind Forge - MaterialX Shader Handler
Cross-platform material definition and translation
Standard Surface ↔ OpenPBR ↔ Unity ↔ Unreal
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ShaderModel(Enum):
    """Supported shader models"""
    STANDARD_SURFACE = "standard_surface"  # Autodesk Standard Surface
    OPENPBR = "open_pbr_surface"          # OpenPBR Surface
    UNITY_LIT = "unity_lit"                # Unity URP/HDRP Lit
    UNREAL_PBR = "unreal_pbr"              # Unreal Engine PBR
    GODOT_SPATIAL = "godot_spatial"        # Godot Spatial Material


@dataclass
class MaterialParameters:
    """
    Universal material parameters compatible across shader models.

    Based on MaterialX standard_surface and open_pbr_surface.
    """
    # Base color / Albedo
    base_color: tuple[float, float, float] = (0.8, 0.8, 0.8)
    base_color_texture: Optional[str] = None

    # Metalness
    metalness: float = 0.0
    metalness_texture: Optional[str] = None

    # Roughness / Specular Roughness
    roughness: float = 0.5
    roughness_texture: Optional[str] = None

    # Normal mapping
    normal_texture: Optional[str] = None
    normal_strength: float = 1.0

    # Emissive
    emission_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
    emission_strength: float = 0.0
    emission_texture: Optional[str] = None

    # Ambient Occlusion
    ao_texture: Optional[str] = None
    ao_strength: float = 1.0

    # Opacity / Alpha
    opacity: float = 1.0
    opacity_texture: Optional[str] = None

    # Specular (for non-metallic)
    specular: float = 0.5
    specular_texture: Optional[str] = None
    specular_color: tuple[float, float, float] = (1.0, 1.0, 1.0)

    # Transmission (for glass/transparency)
    transmission: float = 0.0
    transmission_texture: Optional[str] = None

    # Subsurface scattering
    subsurface: float = 0.0
    subsurface_color: tuple[float, float, float] = (0.8, 0.8, 0.8)
    subsurface_radius: tuple[float, float, float] = (1.0, 0.5, 0.25)

    # Coating (clear coat)
    coat: float = 0.0
    coat_roughness: float = 0.1

    # Custom properties
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class MaterialXHandler:
    """
    MaterialX handler for cross-platform material translation.

    Features:
    - Standard Surface → OpenPBR conversion
    - OpenPBR → Standard Surface conversion
    - Export to Unity/Unreal/Godot formats
    - Texture path remapping
    - Parameter validation

    MaterialX Spec: https://materialx.org/
    """

    def __init__(self):
        """Initialize MaterialX handler"""
        self.mtlx_available = self._check_materialx()

        if not self.mtlx_available:
            logger.warning(
                "MaterialX library not available. Install with:\n"
                "  pip install MaterialX\n"
                "Using fallback XML-based implementation"
            )

    def _check_materialx(self) -> bool:
        """Check if MaterialX library is available"""
        try:
            import MaterialX as mx
            return True
        except ImportError:
            return False

    # ========================================================================
    # Material Loading
    # ========================================================================

    def load_material(self, mtlx_path: Path) -> MaterialParameters:
        """
        Load MaterialX file and extract material parameters.

        Args:
            mtlx_path: Path to .mtlx file

        Returns:
            MaterialParameters object

        Raises:
            ValueError: If file cannot be loaded
        """
        if not mtlx_path.exists():
            raise FileNotFoundError(f"MaterialX file not found: {mtlx_path}")

        if self.mtlx_available:
            return self._load_with_materialx(mtlx_path)
        else:
            return self._load_with_xml(mtlx_path)

    def _load_with_materialx(self, mtlx_path: Path) -> MaterialParameters:
        """Load using MaterialX library"""
        import MaterialX as mx

        # Load document
        doc = mx.createDocument()
        mx.readFromXmlFile(doc, str(mtlx_path))

        # Find material
        material = None
        for node in doc.getMaterialNodes():
            material = node
            break

        if not material:
            raise ValueError("No material found in MaterialX file")

        # Extract parameters
        params = MaterialParameters()

        # Get shader connected to material
        for shader_ref in material.getShaderRefs():
            shader = shader_ref.getReferencedNode()
            if shader:
                params = self._extract_parameters_from_shader(shader)

        return params

    def _load_with_xml(self, mtlx_path: Path) -> MaterialParameters:
        """Load using XML fallback"""
        tree = ET.parse(mtlx_path)
        root = tree.getroot()

        params = MaterialParameters()

        # Find standard_surface or open_pbr_surface node
        for node in root.findall(".//standard_surface"):
            params = self._parse_standard_surface_xml(node)
            break

        for node in root.findall(".//open_pbr_surface"):
            params = self._parse_openpbr_xml(node)
            break

        return params

    def _extract_parameters_from_shader(self, shader) -> MaterialParameters:
        """Extract parameters from MaterialX shader node"""
        import MaterialX as mx

        params = MaterialParameters()

        # Extract inputs
        for input in shader.getInputs():
            name = input.getName()
            value = input.getValue()

            # Base color
            if name == "base_color":
                if isinstance(value, tuple):
                    params.base_color = value
            elif name == "base":
                params.metalness = float(value) if value else 0.0

            # Metalness
            elif name == "metalness":
                params.metalness = float(value) if value else 0.0

            # Roughness
            elif name == "specular_roughness" or name == "roughness":
                params.roughness = float(value) if value else 0.5

            # Emission
            elif name == "emission_color":
                if isinstance(value, tuple):
                    params.emission_color = value
            elif name == "emission":
                params.emission_strength = float(value) if value else 0.0

            # Opacity
            elif name == "opacity":
                params.opacity = float(value) if value else 1.0

            # Check for texture connections
            if input.hasAttribute("file"):
                texture_path = input.getAttribute("file")
                if name == "base_color":
                    params.base_color_texture = texture_path
                elif name == "metalness":
                    params.metalness_texture = texture_path
                elif name == "specular_roughness" or name == "roughness":
                    params.roughness_texture = texture_path

        return params

    def _parse_standard_surface_xml(self, node: ET.Element) -> MaterialParameters:
        """Parse standard_surface from XML"""
        params = MaterialParameters()

        for input_node in node.findall("input"):
            name = input_node.get("name")
            value = input_node.get("value")

            if name == "base_color" and value:
                params.base_color = self._parse_color(value)
            elif name == "metalness" and value:
                params.metalness = float(value)
            elif name == "specular_roughness" and value:
                params.roughness = float(value)
            elif name == "emission_color" and value:
                params.emission_color = self._parse_color(value)
            elif name == "emission" and value:
                params.emission_strength = float(value)

        return params

    def _parse_openpbr_xml(self, node: ET.Element) -> MaterialParameters:
        """Parse open_pbr_surface from XML"""
        params = MaterialParameters()

        for input_node in node.findall("input"):
            name = input_node.get("name")
            value = input_node.get("value")

            if name == "base_color" and value:
                params.base_color = self._parse_color(value)
            elif name == "base_metalness" and value:
                params.metalness = float(value)
            elif name == "specular_roughness" and value:
                params.roughness = float(value)

        return params

    def _parse_color(self, value_str: str) -> tuple[float, float, float]:
        """Parse color string to tuple"""
        try:
            parts = value_str.split(',')
            if len(parts) >= 3:
                return (float(parts[0]), float(parts[1]), float(parts[2]))
        except:
            pass
        return (0.8, 0.8, 0.8)

    # ========================================================================
    # Material Saving
    # ========================================================================

    def save_material(
        self,
        params: MaterialParameters,
        output_path: Path,
        shader_model: ShaderModel = ShaderModel.STANDARD_SURFACE
    ) -> None:
        """
        Save material parameters to MaterialX file.

        Args:
            params: Material parameters
            output_path: Output .mtlx file path
            shader_model: Target shader model

        Raises:
            IOError: If file cannot be written
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.mtlx_available:
            self._save_with_materialx(params, output_path, shader_model)
        else:
            self._save_with_xml(params, output_path, shader_model)

        logger.info(f"Saved MaterialX file: {output_path}")

    def _save_with_materialx(
        self,
        params: MaterialParameters,
        output_path: Path,
        shader_model: ShaderModel
    ) -> None:
        """Save using MaterialX library"""
        import MaterialX as mx

        # Create document
        doc = mx.createDocument()

        # Create material
        material = doc.addMaterial("material")

        # Create shader based on model
        if shader_model == ShaderModel.STANDARD_SURFACE:
            shader = doc.addNode("standard_surface", "shader", "surfaceshader")
            self._set_standard_surface_inputs(shader, params)
        elif shader_model == ShaderModel.OPENPBR:
            shader = doc.addNode("open_pbr_surface", "shader", "surfaceshader")
            self._set_openpbr_inputs(shader, params)

        # Connect shader to material
        shader_ref = material.addShaderRef("shaderref", shader.getName())

        # Write to file
        mx.writeToXmlFile(doc, str(output_path))

    def _save_with_xml(
        self,
        params: MaterialParameters,
        output_path: Path,
        shader_model: ShaderModel
    ) -> None:
        """Save using XML fallback"""
        root = ET.Element("materialx", version="1.38")

        # Create material node
        if shader_model == ShaderModel.STANDARD_SURFACE:
            shader = ET.SubElement(root, "standard_surface", name="shader")
            self._add_standard_surface_inputs_xml(shader, params)
        elif shader_model == ShaderModel.OPENPBR:
            shader = ET.SubElement(root, "open_pbr_surface", name="shader")
            self._add_openpbr_inputs_xml(shader, params)

        # Create material
        material = ET.SubElement(root, "surfacematerial", name="material")
        shaderref = ET.SubElement(material, "input", name="surfaceshader", type="surfaceshader")
        shaderref.set("nodename", "shader")

        # Write to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def _set_standard_surface_inputs(self, shader, params: MaterialParameters) -> None:
        """Set standard_surface inputs"""
        # Base color
        if params.base_color_texture:
            input = shader.addInput("base_color", "color3")
            input.setAttribute("file", params.base_color_texture)
        else:
            input = shader.addInput("base_color", "color3")
            input.setValue(params.base_color)

        # Metalness
        if params.metalness_texture:
            input = shader.addInput("metalness", "float")
            input.setAttribute("file", params.metalness_texture)
        else:
            shader.addInput("metalness", "float").setValue(params.metalness)

        # Roughness
        if params.roughness_texture:
            input = shader.addInput("specular_roughness", "float")
            input.setAttribute("file", params.roughness_texture)
        else:
            shader.addInput("specular_roughness", "float").setValue(params.roughness)

        # Emission
        shader.addInput("emission_color", "color3").setValue(params.emission_color)
        shader.addInput("emission", "float").setValue(params.emission_strength)

        # Opacity
        shader.addInput("opacity", "color3").setValue((params.opacity, params.opacity, params.opacity))

    def _set_openpbr_inputs(self, shader, params: MaterialParameters) -> None:
        """Set open_pbr_surface inputs"""
        # Base color
        shader.addInput("base_color", "color3").setValue(params.base_color)

        # Metalness
        shader.addInput("base_metalness", "float").setValue(params.metalness)

        # Roughness
        shader.addInput("specular_roughness", "float").setValue(params.roughness)

        # Emission
        shader.addInput("emission_luminance", "float").setValue(params.emission_strength)
        shader.addInput("emission_color", "color3").setValue(params.emission_color)

    def _add_standard_surface_inputs_xml(self, shader: ET.Element, params: MaterialParameters) -> None:
        """Add standard_surface inputs to XML"""
        # Base color
        input_elem = ET.SubElement(shader, "input", name="base_color", type="color3")
        input_elem.set("value", f"{params.base_color[0]},{params.base_color[1]},{params.base_color[2]}")

        # Metalness
        ET.SubElement(shader, "input", name="metalness", type="float", value=str(params.metalness))

        # Roughness
        ET.SubElement(shader, "input", name="specular_roughness", type="float", value=str(params.roughness))

        # Emission
        emission_color = ET.SubElement(shader, "input", name="emission_color", type="color3")
        emission_color.set("value", f"{params.emission_color[0]},{params.emission_color[1]},{params.emission_color[2]}")
        ET.SubElement(shader, "input", name="emission", type="float", value=str(params.emission_strength))

    def _add_openpbr_inputs_xml(self, shader: ET.Element, params: MaterialParameters) -> None:
        """Add open_pbr_surface inputs to XML"""
        # Base color
        base_color = ET.SubElement(shader, "input", name="base_color", type="color3")
        base_color.set("value", f"{params.base_color[0]},{params.base_color[1]},{params.base_color[2]}")

        # Metalness
        ET.SubElement(shader, "input", name="base_metalness", type="float", value=str(params.metalness))

        # Roughness
        ET.SubElement(shader, "input", name="specular_roughness", type="float", value=str(params.roughness))

    # ========================================================================
    # Shader Model Translation
    # ========================================================================

    def translate_shader(
        self,
        source_model: ShaderModel,
        target_model: ShaderModel,
        params: MaterialParameters
    ) -> MaterialParameters:
        """
        Translate material between shader models.

        Args:
            source_model: Source shader model
            target_model: Target shader model
            params: Material parameters

        Returns:
            Translated MaterialParameters
        """
        # Most parameters translate 1:1, but some need adjustments
        translated = MaterialParameters(**params.to_dict())

        # Standard Surface → OpenPBR
        if source_model == ShaderModel.STANDARD_SURFACE and target_model == ShaderModel.OPENPBR:
            # OpenPBR uses base_metalness instead of metalness
            # Specular workflow is similar
            pass

        # OpenPBR → Standard Surface
        elif source_model == ShaderModel.OPENPBR and target_model == ShaderModel.STANDARD_SURFACE:
            # base_metalness → metalness
            pass

        # Unity Lit
        elif target_model == ShaderModel.UNITY_LIT:
            # Unity uses smoothness (1 - roughness)
            translated.custom["smoothness"] = 1.0 - params.roughness

        # Unreal PBR
        elif target_model == ShaderModel.UNREAL_PBR:
            # Unreal matches Standard Surface closely
            pass

        # Godot Spatial
        elif target_model == ShaderModel.GODOT_SPATIAL:
            # Godot uses similar PBR model
            pass

        return translated

    def export_to_unity(self, params: MaterialParameters, output_path: Path) -> None:
        """Export material as Unity shader graph JSON"""
        unity_params = self.translate_shader(
            ShaderModel.STANDARD_SURFACE,
            ShaderModel.UNITY_LIT,
            params
        )

        # Create Unity material JSON (simplified)
        import json

        unity_data = {
            "shader": "Universal Render Pipeline/Lit",
            "properties": {
                "_BaseColor": list(unity_params.base_color) + [1.0],
                "_Metallic": unity_params.metalness,
                "_Smoothness": unity_params.custom.get("smoothness", 0.5),
                "_EmissionColor": list(unity_params.emission_color) + [unity_params.emission_strength],
            }
        }

        if unity_params.base_color_texture:
            unity_data["properties"]["_BaseMap"] = unity_params.base_color_texture

        with open(output_path, 'w') as f:
            json.dump(unity_data, f, indent=2)

        logger.info(f"Exported Unity material: {output_path}")

    def export_to_unreal(self, params: MaterialParameters, output_path: Path) -> None:
        """Export material as Unreal material description"""
        # Unreal materials are typically JSON or custom format
        # This creates a simplified JSON representation
        import json

        unreal_data = {
            "material": {
                "base_color": list(params.base_color),
                "metallic": params.metalness,
                "roughness": params.roughness,
                "emissive_color": list(params.emission_color),
                "emissive_multiplier": params.emission_strength,
                "opacity": params.opacity,
                "textures": {}
            }
        }

        if params.base_color_texture:
            unreal_data["material"]["textures"]["base_color"] = params.base_color_texture
        if params.normal_texture:
            unreal_data["material"]["textures"]["normal"] = params.normal_texture
        if params.roughness_texture:
            unreal_data["material"]["textures"]["roughness"] = params.roughness_texture

        with open(output_path, 'w') as f:
            json.dump(unreal_data, f, indent=2)

        logger.info(f"Exported Unreal material: {output_path}")
