#include <cmath>
extern "C" float cpp_color_fidelity_score(const float* h1, const float* h2, int n) {
    if (!h1 || !h2 || n <= 0) return 0.0f;
    double bc = 0.0; // Bhattacharyya coefficient
    for (int i = 0; i < n; ++i) {
        double a = h1[i];
        double b = h2[i];
        if (a < 0.0) a = 0.0; if (b < 0.0) b = 0.0;
        bc += std::sqrt(a * b);
    }
    if (bc < 0.0) bc = 0.0; if (bc > 1.0) bc = 1.0;
    return static_cast<float>(bc);
}