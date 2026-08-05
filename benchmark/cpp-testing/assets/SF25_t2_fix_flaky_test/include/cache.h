#pragma once

#include <string>
#include <unordered_map>
#include <chrono>
#include <mutex>
#include <optional>

namespace cache {

struct CacheEntry {
    std::string value;
    std::chrono::steady_clock::time_point expires_at;
};

class TimedCache {
public:
    explicit TimedCache(std::chrono::milliseconds default_ttl)
        : default_ttl_(default_ttl) {}

    void put(const std::string& key, const std::string& value);
    void put(const std::string& key, const std::string& value,
             std::chrono::milliseconds ttl);

    std::optional<std::string> get(const std::string& key);

    void evict_expired();

    size_t size() const;

private:
    std::chrono::milliseconds default_ttl_;
    std::unordered_map<std::string, CacheEntry> store_;
    mutable std::mutex mutex_;
};

} // namespace cache
