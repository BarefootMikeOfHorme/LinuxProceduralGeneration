#pragma once
#include <cstddef>

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef BUILDING_VMF_VALIDATOR_CPP
    #define VMF_API __declspec(dllexport)
  #else
    #define VMF_API __declspec(dllimport)
  #endif
#else
  #if __GNUC__ >= 4
    #define VMF_API __attribute__((visibility("default")))
  #else
    #define VMF_API
  #endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

VMF_API float cpp_color_fidelity_score(const float* h1, const float* h2, int n);

#ifdef __cplusplus
}
#endif