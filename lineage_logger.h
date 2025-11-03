#pragma once

#include <string>
#include <vector>

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

struct VMF_API LineageRecord {
 std::string id;
 std::string type;
 std::string timestamp;
 std::string metadata_json; // small JSON blob
};

class VMF_API LineageLogger {
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
