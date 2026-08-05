#include "cache.h"

namespace cache {

void TimedCache::put(const std::string& key, const std::string& value) {
    put(key, value, default_ttl_);
}

void TimedCache::put(const std::string& key, const std::string& value,
                     std::chrono::milliseconds ttl) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto expires = std::chrono::steady_clock::now() + ttl;
    store_[key] = CacheEntry{value, expires};
}

std::optional<std::string> TimedCache::get(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = store_.find(key);
    if (it == store_.end()) {
        return std::nullopt;
    }
    if (std::chrono::steady_clock::now() > it->second.expires_at) {
        store_.erase(it);
        return std::nullopt;
    }
    return it->second.value;
}

void TimedCache::evict_expired() {
    std::lock_guard<std::mutex> lock(mutex_);
    auto now = std::chrono::steady_clock::now();
    for (auto it = store_.begin(); it != store_.end();) {
        if (now > it->second.expires_at) {
            it = store_.erase(it);
        } else {
            ++it;
        }
    }
}

size_t TimedCache::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return store_.size();
}

} // namespace cache
