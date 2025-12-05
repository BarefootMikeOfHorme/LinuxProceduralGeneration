import pytest
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vaultmind_forge.forge_validator.backends import RustBackend, CppBackend, PythonFallbackBackend
from vaultmind_forge.forge_validator.validator import Validator

def test_rust_backend_loading():
    """Test that Rust backend loads and runs"""
    try:
        backend = RustBackend()
        print("\n✅ RustBackend loaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to load RustBackend: {e}")

    # Create a dummy image for testing
    from PIL import Image
    import numpy as np
    
    img_path = Path("test_rust_image.png")
    img = Image.fromarray(np.random.randint(0, 255, (100, 100), dtype=np.uint8))
    img.save(img_path)
    
    try:
        result = backend.validate(img_path)
        print(f"✅ Rust validation result: {result}")
        assert "sharpness" in result
        assert "color_fidelity" in result
        assert "contrast" in result
        assert isinstance(result["sharpness"], float)
    finally:
        if img_path.exists():
            img_path.unlink()

def test_cpp_backend_loading():
    """Test that C++ backend loads and runs"""
    try:
        backend = CppBackend()
        print("\n✅ CppBackend loaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to load CppBackend: {e}")

    # Create a dummy image for testing
    from PIL import Image
    import numpy as np
    
    img_path = Path("test_cpp_image.png")
    img = Image.fromarray(np.random.randint(0, 255, (100, 100), dtype=np.uint8))
    img.save(img_path)
    
    try:
        result = backend.validate(img_path)
        print(f"✅ C++ validation result: {result}")
        assert "color_fidelity" in result
        assert isinstance(result["color_fidelity"], float)
    finally:
        if img_path.exists():
            img_path.unlink()

if __name__ == "__main__":
    # Manual run
    try:
        test_rust_backend_loading()
        test_cpp_backend_loading()
        print("\n✨ All integration tests passed!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)
