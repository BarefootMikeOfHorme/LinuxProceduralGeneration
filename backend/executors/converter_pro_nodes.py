"""
VaultMind Forge - ConverterPro Integration
Nodes that use ConverterPro for advanced asset conversion
"""

import sys
from typing import Dict, List, Any
from pathlib import Path
import uuid
import logging
import subprocess

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


logger = logging.getLogger(__name__)

# Path to ConverterPro
CONVERTER_PRO_PATH = Path("C:/Users/Administrator/Desktop/ConverterProv1")
CONVERTER_PRO_CLI = CONVERTER_PRO_PATH / "cli.py"


class ConverterProScanExecutor(NodeExecutor):
    """
    ConverterPro Scan Node - Scan and catalog assets using ConverterPro
    """

    @property
    def node_type(self) -> str:
        return "converterProScan"

    @property
    def display_name(self) -> str:
        return "ConverterPro Scan"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="path",
                type=DataType.TEXT,
                required=True,
                description="Path to scan for assets"
            ),
            InputSpec(
                name="recursive",
                type=DataType.BOOLEAN,
                required=False,
                default=True,
                description="Scan recursively"
            ),
            InputSpec(
                name="database",
                type=DataType.TEXT,
                required=False,
                default="assets.db",
                description="Database file for catalog"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="database",
                type=DataType.TEXT,
                description="Path to asset database"
            ),
            OutputSpec(
                name="summary",
                type=DataType.DICT,
                description="Scan summary"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Scan assets using ConverterPro"""
        # Get inputs
        scan_path = self.get_input_value(inputs, "path")
        recursive = self.get_input_value(inputs, "recursive", True)
        database = self.get_input_value(inputs, "database", "assets.db")

        logger.info(f"ConverterPro Scan:")
        logger.info(f"  Path: {scan_path}")
        logger.info(f"  Database: {database}")

        # Build command
        cmd = [
            sys.executable,
            str(CONVERTER_PRO_CLI),
            "scan",
            scan_path,
            "--database", database
        ]

        if recursive:
            cmd.append("--recursive")

        # Execute ConverterPro
        try:
            result = subprocess.run(
                cmd,
                cwd=str(CONVERTER_PRO_PATH),
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"  ✓ Scan completed")
            logger.info(result.stdout)

            return {
                "database": database,
                "summary": {
                    "path": scan_path,
                    "database": database,
                    "output": result.stdout
                }
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"ConverterPro scan failed: {e.stderr}")
            raise RuntimeError(f"ConverterPro scan failed: {e.stderr}")


class ConverterProConvertExecutor(NodeExecutor):
    """
    ConverterPro Convert Node - Convert assets between formats/engines
    """

    @property
    def node_type(self) -> str:
        return "converterProConvert"

    @property
    def display_name(self) -> str:
        return "ConverterPro Convert"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="source",
                type=DataType.TEXT,
                required=True,
                description="Source asset or directory"
            ),
            InputSpec(
                name="engine",
                type=DataType.TEXT,
                required=False,
                default="generic",
                description="Target engine (unity, unreal, godot, generic)"
            ),
            InputSpec(
                name="format",
                type=DataType.TEXT,
                required=False,
                default=None,
                description="Target format (optional, auto-detect)"
            ),
            InputSpec(
                name="recursive",
                type=DataType.BOOLEAN,
                required=False,
                default=False,
                description="Process directories recursively"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="output_path",
                type=DataType.TEXT,
                description="Path to converted assets"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Conversion metadata"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert assets using ConverterPro"""
        # Get inputs
        source = self.get_input_value(inputs, "source")
        engine = self.get_input_value(inputs, "engine", "generic")
        format_type = self.get_input_value(inputs, "format", None)
        recursive = self.get_input_value(inputs, "recursive", False)

        # Create output directory
        output_dir = Path("backend/outputs") / f"converted_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ConverterPro Convert:")
        logger.info(f"  Source: {source}")
        logger.info(f"  Engine: {engine}")
        logger.info(f"  Output: {output_dir}")

        # Build command
        cmd = [
            sys.executable,
            str(CONVERTER_PRO_CLI),
            "convert",
            source,
            str(output_dir),
            "--engine", engine
        ]

        if format_type:
            cmd.extend(["--format", format_type])

        if recursive:
            cmd.append("--recursive")

        # Execute ConverterPro
        try:
            result = subprocess.run(
                cmd,
                cwd=str(CONVERTER_PRO_PATH),
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"  ✓ Conversion completed")
            logger.info(result.stdout)

            return {
                "output_path": str(output_dir),
                "metadata": {
                    "source": source,
                    "engine": engine,
                    "format": format_type,
                    "output": result.stdout
                }
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"ConverterPro conversion failed: {e.stderr}")
            raise RuntimeError(f"ConverterPro conversion failed: {e.stderr}")


class ConverterProExportExecutor(NodeExecutor):
    """
    ConverterPro Export Node - Export assets to specific formats
    """

    @property
    def node_type(self) -> str:
        return "converterProExport"

    @property
    def display_name(self) -> str:
        return "ConverterPro Export"

    @property
    def category(self) -> str:
        return "processing"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="source",
                type=DataType.TEXT,
                required=True,
                description="Source asset directory"
            ),
            InputSpec(
                name="format",
                type=DataType.TEXT,
                required=False,
                default="vaf",
                description="Export format (vaf, zip, etc.)"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="output_path",
                type=DataType.TEXT,
                description="Path to exported package"
            ),
            OutputSpec(
                name="metadata",
                type=DataType.DICT,
                description="Export metadata"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Export assets using ConverterPro"""
        # Get inputs
        source = self.get_input_value(inputs, "source")
        export_format = self.get_input_value(inputs, "format", "vaf")

        # Create output directory
        output_dir = Path("backend/outputs") / f"exported_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ConverterPro Export:")
        logger.info(f"  Source: {source}")
        logger.info(f"  Format: {export_format}")
        logger.info(f"  Output: {output_dir}")

        # Build command
        cmd = [
            sys.executable,
            str(CONVERTER_PRO_CLI),
            "export",
            source,
            str(output_dir),
            "--format", export_format
        ]

        # Execute ConverterPro
        try:
            result = subprocess.run(
                cmd,
                cwd=str(CONVERTER_PRO_PATH),
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"  ✓ Export completed")
            logger.info(result.stdout)

            return {
                "output_path": str(output_dir),
                "metadata": {
                    "source": source,
                    "format": export_format,
                    "output": result.stdout
                }
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"ConverterPro export failed: {e.stderr}")
            raise RuntimeError(f"ConverterPro export failed: {e.stderr}")


if __name__ == "__main__":
    # Test executors
    scan_executor = ConverterProScanExecutor()
    print(f"ConverterPro Scan: {scan_executor.node_type}")
    print(f"  Inputs: {[s.name for s in scan_executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in scan_executor.output_spec]}")

    convert_executor = ConverterProConvertExecutor()
    print(f"\nConverterPro Convert: {convert_executor.node_type}")
    print(f"  Inputs: {[s.name for s in convert_executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in convert_executor.output_spec]}")

    export_executor = ConverterProExportExecutor()
    print(f"\nConverterPro Export: {export_executor.node_type}")
    print(f"  Inputs: {[s.name for s in export_executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in export_executor.output_spec]}")
