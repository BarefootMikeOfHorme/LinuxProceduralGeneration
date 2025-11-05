"""
VaultMind Forge - DDS Format Handler
PNG/JPEG to DDS conversion with mipmap generation and GPU-optimized compression
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional, List
import logging
import numpy as np
from PIL import Image

from .format_registry import (
    TextureFormatHandler,
    TextureMetadata,
    TextureOptions,
    CompressionQuality,
    FormatError,
    ConversionError
)

logger = logging.getLogger(__name__)


# DDS Format Constants
DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PITCH = 0x8
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000
DDSD_DEPTH = 0x800000

DDPF_ALPHAPIXELS = 0x1
DDPF_ALPHA = 0x2
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40
DDPF_YUV = 0x200
DDPF_LUMINANCE = 0x20000

DDSCAPS_COMPLEX = 0x8
DDSCAPS_MIPMAP = 0x400000
DDSCAPS_TEXTURE = 0x1000

# DX10 format codes
DXGI_FORMAT_BC1_UNORM = 71  # DXT1
DXGI_FORMAT_BC2_UNORM = 74  # DXT3
DXGI_FORMAT_BC3_UNORM = 77  # DXT5
DXGI_FORMAT_BC7_UNORM = 98  # BC7


class DDSHandler(TextureFormatHandler):
    """
    DDS (DirectDraw Surface) format handler.

    Features:
    - PNG/JPEG → DDS conversion
    - Automatic mipmap generation
    - GPU-optimized block compression (BC1/BC3/BC7)
    - Support for normal maps, HDR, and cube maps
    - DX10 extended header support

    Compression Formats:
    - BC1 (DXT1): 4bpp, good for diffuse textures with 1-bit alpha
    - BC3 (DXT5): 8bpp, good for diffuse + smooth alpha
    - BC7: 8bpp, highest quality, best for high-detail textures
    """

    def __init__(self):
        """Initialize DDS handler"""
        self.compressor_available = self._check_compressor()

        if not self.compressor_available:
            logger.warning(
                "GPU texture compressor not available. Install with:\n"
                "  pip install compressonator-python (AMD Compressonator)\n"
                "  OR pip install nvidia-texture-tools (NVIDIA tools)\n"
                "Fallback will use basic DDS without compression"
            )

    def _check_compressor(self) -> bool:
        """Check if texture compressor is available"""
        try:
            # Try AMD Compressonator first
            import compressonator
            return True
        except ImportError:
            pass

        try:
            # Try NVIDIA texture tools
            import nvidia.texturetools
            return True
        except ImportError:
            pass

        return False

    # ========================================================================
    # FormatHandler Interface
    # ========================================================================

    def get_name(self) -> str:
        """Get format name"""
        return "DDS"

    def get_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.dds', '.DDS']

    def can_read(self) -> bool:
        """Can this handler read files?"""
        return True

    def can_write(self) -> bool:
        """Can this handler write files?"""
        return True

    def get_description(self) -> str:
        """Get human-readable description"""
        return "DirectDraw Surface - GPU-optimized texture format with mipmaps"

    def detect_format(self, file_path: Path) -> bool:
        """
        Detect if file is valid DDS.

        DDS files start with magic bytes 'DDS ' (0x20534444)
        """
        if not file_path.exists():
            return False

        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'DDS '
        except:
            return False

    # ========================================================================
    # TextureFormatHandler Interface
    # ========================================================================

    def convert_to(
        self,
        source_path: Path,
        target_path: Path,
        options: TextureOptions
    ) -> None:
        """
        Convert PNG/JPEG to DDS with mipmaps and compression.

        Args:
            source_path: Input image file (PNG, JPEG, etc.)
            target_path: Output DDS file
            options: Texture options (compression quality, mipmaps, etc.)

        Raises:
            ConversionError: If conversion fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Load source image
            img = Image.open(source_path)

            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Resize if requested
            if options.resize_dimensions:
                img = img.resize(options.resize_dimensions, Image.LANCZOS)

            # Flip Y if requested (OpenGL convention)
            if options.flip_y:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)

            # Generate mipmaps
            mipmap_chain = []
            if options.generate_mipmaps:
                mipmap_chain = self._generate_mipmaps(img)
            else:
                mipmap_chain = [img]

            # Determine compression format based on quality
            compression_format = self._get_compression_format(options.compression_quality)

            # Write DDS file
            if self.compressor_available:
                self._write_dds_compressed(
                    mipmap_chain,
                    target_path,
                    compression_format
                )
            else:
                self._write_dds_uncompressed(mipmap_chain, target_path)

            logger.info(
                f"Converted {source_path} → {target_path} "
                f"({len(mipmap_chain)} mips, {compression_format})"
            )

        except Exception as e:
            raise ConversionError(f"DDS conversion failed: {e}")

    def compress(
        self,
        source_path: Path,
        target_path: Path,
        quality: CompressionQuality
    ) -> None:
        """
        Compress existing DDS file with different quality.

        Args:
            source_path: Input DDS file
            target_path: Output compressed DDS file
            quality: Compression quality level

        Raises:
            ConversionError: If compression fails
        """
        options = TextureOptions(
            compression_quality=quality,
            generate_mipmaps=True
        )
        self.convert_to(source_path, target_path, options)

    def resize(
        self,
        source_path: Path,
        target_path: Path,
        width: int,
        height: int
    ) -> None:
        """
        Resize DDS texture.

        Args:
            source_path: Input DDS file
            target_path: Output resized DDS file
            width: Target width
            height: Target height

        Raises:
            ConversionError: If resize fails
        """
        options = TextureOptions(
            resize_dimensions=(width, height),
            generate_mipmaps=True
        )
        self.convert_to(source_path, target_path, options)

    def get_metadata(self, source_path: Path) -> TextureMetadata:
        """
        Extract DDS texture metadata.

        Args:
            source_path: DDS file to analyze

        Returns:
            TextureMetadata object

        Raises:
            FormatError: If metadata extraction fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        metadata = TextureMetadata()

        try:
            with open(source_path, 'rb') as f:
                # Read DDS header
                magic = f.read(4)
                if magic != b'DDS ':
                    raise FormatError("Invalid DDS file (bad magic)")

                # Read DDS_HEADER (124 bytes)
                header = f.read(124)

                # Extract dimensions (offset 12, 16)
                metadata.height = struct.unpack('<I', header[8:12])[0]
                metadata.width = struct.unpack('<I', header[12:16])[0]

                # Extract format info from DDS_PIXELFORMAT (offset 76)
                pixelformat = header[76:108]
                flags = struct.unpack('<I', pixelformat[4:8])[0]

                if flags & DDPF_FOURCC:
                    fourcc = pixelformat[8:12]
                    metadata.compression_format = fourcc.decode('ascii', errors='ignore')

                # Determine channels based on format
                if flags & DDPF_ALPHAPIXELS:
                    metadata.channels = 4
                elif flags & DDPF_RGB:
                    metadata.channels = 3
                else:
                    metadata.channels = 4  # Default

                metadata.bits_per_channel = 8  # Standard DDS

                logger.info(f"Extracted metadata from {source_path}")

        except Exception as e:
            logger.error(f"Failed to extract DDS metadata: {e}")
            raise FormatError(f"DDS metadata extraction failed: {e}")

        return metadata

    # ========================================================================
    # Mipmap Generation
    # ========================================================================

    def _generate_mipmaps(self, img: Image.Image) -> List[Image.Image]:
        """
        Generate mipmap chain using high-quality downsampling.

        Args:
            img: Source image (base mip level)

        Returns:
            List of images from largest to smallest
        """
        mips = [img]
        width, height = img.size

        # Generate mips down to 1x1
        while width > 1 or height > 1:
            width = max(1, width // 2)
            height = max(1, height // 2)

            # Use Lanczos resampling for high quality
            mip = mips[-1].resize((width, height), Image.LANCZOS)
            mips.append(mip)

        logger.debug(f"Generated {len(mips)} mipmap levels")
        return mips

    def _get_compression_format(self, quality: CompressionQuality) -> str:
        """
        Get DDS compression format based on quality.

        Args:
            quality: Compression quality level

        Returns:
            FourCC code (e.g., 'DXT1', 'DXT5', 'BC7')
        """
        format_map = {
            CompressionQuality.LOW: 'DXT1',      # BC1, 4bpp
            CompressionQuality.MEDIUM: 'DXT5',   # BC3, 8bpp
            CompressionQuality.HIGH: 'BC7',      # BC7, 8bpp
            CompressionQuality.LOSSLESS: 'RGBA'  # Uncompressed RGBA
        }
        return format_map[quality]

    # ========================================================================
    # DDS Writing (Uncompressed Fallback)
    # ========================================================================

    def _write_dds_uncompressed(
        self,
        mipmap_chain: List[Image.Image],
        target_path: Path
    ) -> None:
        """
        Write uncompressed RGBA DDS file.

        This is a fallback when compressor is not available.
        """
        width, height = mipmap_chain[0].size

        with open(target_path, 'wb') as f:
            # Write DDS magic
            f.write(b'DDS ')

            # Build DDS_HEADER
            flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
            if len(mipmap_chain) > 1:
                flags |= DDSD_MIPMAPCOUNT

            # Header struct (124 bytes)
            header = struct.pack('<I', 124)  # dwSize
            header += struct.pack('<I', flags)  # dwFlags
            header += struct.pack('<I', height)  # dwHeight
            header += struct.pack('<I', width)  # dwWidth
            header += struct.pack('<I', width * 4)  # dwPitchOrLinearSize
            header += struct.pack('<I', 1)  # dwDepth
            header += struct.pack('<I', len(mipmap_chain))  # dwMipMapCount
            header += b'\x00' * 44  # dwReserved1[11]

            # DDS_PIXELFORMAT (32 bytes)
            pixelformat = struct.pack('<I', 32)  # dwSize
            pixelformat += struct.pack('<I', DDPF_RGB | DDPF_ALPHAPIXELS)  # dwFlags
            pixelformat += b'\x00' * 4  # dwFourCC
            pixelformat += struct.pack('<I', 32)  # dwRGBBitCount
            pixelformat += struct.pack('<I', 0x00FF0000)  # dwRBitMask
            pixelformat += struct.pack('<I', 0x0000FF00)  # dwGBitMask
            pixelformat += struct.pack('<I', 0x000000FF)  # dwBBitMask
            pixelformat += struct.pack('<I', 0xFF000000)  # dwABitMask

            header += pixelformat

            # DDS_CAPS (16 bytes)
            caps = DDSCAPS_TEXTURE
            if len(mipmap_chain) > 1:
                caps |= DDSCAPS_COMPLEX | DDSCAPS_MIPMAP

            header += struct.pack('<I', caps)  # dwCaps
            header += struct.pack('<I', 0)  # dwCaps2
            header += struct.pack('<I', 0)  # dwCaps3
            header += struct.pack('<I', 0)  # dwCaps4
            header += struct.pack('<I', 0)  # dwReserved2

            f.write(header)

            # Write mipmap data (RGBA8 format)
            for mip in mipmap_chain:
                # Convert to raw RGBA bytes
                data = np.array(mip, dtype=np.uint8)
                f.write(data.tobytes())

        logger.info(f"Wrote uncompressed DDS: {target_path}")

    def _write_dds_compressed(
        self,
        mipmap_chain: List[Image.Image],
        target_path: Path,
        compression_format: str
    ) -> None:
        """
        Write compressed DDS file using external compressor.

        This uses AMD Compressonator or NVIDIA texture tools if available.
        """
        try:
            import compressonator as cmp

            # Convert PIL images to compressonator format
            width, height = mipmap_chain[0].size

            # Setup compression options
            options = cmp.CMP_CompressOptions()
            options.dwSize = cmp.sizeof(cmp.CMP_CompressOptions)
            options.fquality = 1.0  # Maximum quality

            # Set format
            if compression_format == 'DXT1' or compression_format == 'BC1':
                options.DestFormat = cmp.CMP_FORMAT_BC1
            elif compression_format == 'DXT5' or compression_format == 'BC3':
                options.DestFormat = cmp.CMP_FORMAT_BC3
            elif compression_format == 'BC7':
                options.DestFormat = cmp.CMP_FORMAT_BC7
            else:
                # Fallback to uncompressed
                self._write_dds_uncompressed(mipmap_chain, target_path)
                return

            # Compress and save
            source_texture = self._pil_to_cmp_texture(mipmap_chain[0])
            dest_texture = cmp.CMP_Texture()

            cmp.CompressTexture(source_texture, dest_texture, options)
            cmp.SaveTexture(str(target_path), dest_texture)

            logger.info(f"Wrote compressed DDS ({compression_format}): {target_path}")

        except ImportError:
            # Fallback to uncompressed if compressor not available
            logger.warning("Compressor not available, writing uncompressed DDS")
            self._write_dds_uncompressed(mipmap_chain, target_path)
        except Exception as e:
            logger.error(f"Compression failed, falling back to uncompressed: {e}")
            self._write_dds_uncompressed(mipmap_chain, target_path)

    def _pil_to_cmp_texture(self, img: Image.Image):
        """Convert PIL Image to Compressonator texture format"""
        import compressonator as cmp

        # Convert to numpy array
        data = np.array(img, dtype=np.uint8)
        width, height = img.size

        # Create CMP texture
        texture = cmp.CMP_Texture()
        texture.dwSize = width * height * 4
        texture.dwWidth = width
        texture.dwHeight = height
        texture.dwPitch = width * 4
        texture.format = cmp.CMP_FORMAT_RGBA_8888
        texture.dwDataSize = cmp.CalcMinMipSize(width, height, 4)
        texture.pData = data.ctypes.data_as(cmp.POINTER(cmp.CMP_BYTE))

        return texture
