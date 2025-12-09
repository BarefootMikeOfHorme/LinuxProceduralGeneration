#include <cmath>
#include <cstdlib>
#include <cstdio>

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef BUILDING_VMF_VALIDATOR_CPP
    #define VMF_API __declspec(dllexport)
  #else
    #define VMF_API __declspec(dllimport)
  #endif
#else
  #define VMF_API
#endif

static void emit_json_log(const char* event, double score) {
 const char* env = std::getenv("VMF_LOG_JSON");
 if (!env) return;
 const char* path = std::getenv("VMF_LOG_PATH");
 if (!path) path = "validator_log.jsonl";
 FILE* f = std::fopen(path, "a");
 if (!f) return;
 std::fprintf(f, "{\"event\":\"%s\",\"score\":%.6f}\n", event, score);
 std::fclose(f);
}

extern "C" VMF_API float cpp_color_fidelity_score(const float* h1, const float* h2, int n) {
    if (!h1 || !h2 || n <= 0) return 0.0f;

    // Compute sums for optional normalization
    double sumA = 0.0, sumB = 0.0;
    for (int i = 0; i < n; ++i) {
        double a = h1[i];
        double b = h2[i];
        if (a > 0.0) sumA += a;
        if (b > 0.0) sumB += b;
    }
    if (sumA <= 0.0 || sumB <= 0.0) return 0.0f;

    double bc = 0.0; // Bhattacharyya coefficient for normalized distributions
    for (int i = 0; i < n; ++i) {
        double a = h1[i] / sumA;
        double b = h2[i] / sumB;
        if (a < 0.0) a = 0.0;
        if (b < 0.0) b = 0.0;
        bc += std::sqrt(a * b);
    }

    if (bc < 0.0) bc = 0.0;
    if (bc > 1.0) bc = 1.0;
    emit_json_log("cpp_color_fidelity_score", bc);
    return static_cast<float>(bc);
}