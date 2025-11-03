#pragma once

#include <string>
#include <vector>

struct LineageRecord {
 std::string id;
 std::string type;
 std::string timestamp;
 std::string metadata_json; // small JSON blob
};

class LineageLogger {
public:
 LineageLogger();
 ~LineageLogger();

 void add_record(const LineageRecord& rec);
 void flush_to_file(const std::string& path);
 void flush_to_jsonl(const std::string& path);
 void clear();

private:
 std::vector<LineageRecord> records_;
};
