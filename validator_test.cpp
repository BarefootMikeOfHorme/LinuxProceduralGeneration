#include <iostream>
#include "validator.h"
#include "lineage_logger.h"

int main() {
    const int n = 8;
    LineageLogger logger;

    // unnormalized vs normalized
    float a[n] = { 10.f, 20.f, 30.f, 40.f, 0.f, 0.f, 0.f, 0.f };
    float b[n] = { 0.1f, 0.2f, 0.3f, 0.4f, 0.f, 0.f, 0.f, 0.f };
    float score1 = cpp_color_fidelity_score(a, b, n);
    std::cout << "Score (unnormalized a vs normalized b): " << score1 << std::endl;

    LineageRecord rec1;
    rec1.id = "test1";
    rec1.type = "color_fidelity";
    rec1.timestamp = "2025-10-28T12:00:00Z";
    rec1.metadata_json = "{\"score\":" + std::to_string(score1) + "}";
    logger.add_record(rec1);

    // identical histograms
    float c[n] = { 10.f, 20.f, 30.f, 40.f, 0.f, 0.f, 0.f, 0.f };
    float d[n] = { 10.f, 20.f, 30.f, 40.f, 0.f, 0.f, 0.f, 0.f };
    float score2 = cpp_color_fidelity_score(c, d, n);
    std::cout << "Score (identical histograms): " << score2 << std::endl;

    LineageRecord rec2;
    rec2.id = "test2";
    rec2.type = "color_fidelity";
    rec2.timestamp = "2025-10-28T12:00:01Z";
    rec2.metadata_json = "{\"score\":" + std::to_string(score2) + "}";
    logger.add_record(rec2);

    // flush to file in current directory
    logger.flush_to_file("lineage_log.csv");

    return 0;
}