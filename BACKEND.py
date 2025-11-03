def load_rust_validator():
    import forge_validator_rust as fvr
    return fvr

def load_cpp_validator(dll_path=None):
    import ctypes
    return ctypes.CDLL(dll_path or "vmf_validator")