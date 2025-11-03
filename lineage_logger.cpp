#include "lineage_logger.h"
#include <fstream>

LineageLogger::LineageLogger() {}
LineageLogger::~LineageLogger() {}

void LineageLogger::add_record(const LineageRecord& rec) {
 records_.push_back(rec);
}

void LineageLogger::flush_to_file(const std::string& path) {
 std::ofstream ofs(path, std::ios::app);
 if (!ofs) return;		
 for (const auto& r : records_) {
 // simple CSV-like line: id,type,timestamp,metadata
 ofs << r.id << "," << r.type << "," << r.timestamp << "," << r.metadata_json << "\n";
 }
 ofs.close();
 records_.clear();
}

void LineageLogger::flush_to_jsonl(const std::string& path) {
 std::ofstream ofs(path, std::ios::app);
 if (!ofs) return;
 for (const auto& r : records_) {
 // write a minimal JSON line
 ofs << "{\"id\":\"" << r.id << "\",\"type\":\"" << r.type << "\",\"timestamp\":\"" << r.timestamp << "\",\"metadata\":" << r.metadata_json << "}\n";
 }
 ofs.close();
 records_.clear();
}

void LineageLogger::clear() {
 records_.clear();
}
