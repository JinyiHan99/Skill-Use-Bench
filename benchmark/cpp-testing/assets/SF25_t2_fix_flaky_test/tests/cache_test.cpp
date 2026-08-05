#include <gtest/gtest.h>
#include "cache.h"
#include <thread>
#include <chrono>

using namespace cache;
using namespace std::chrono_literals;

class CacheTest : public ::testing::Test {
protected:
    void SetUp() override {
        cache_ = std::make_unique<TimedCache>(100ms);
    }

    std::unique_ptr<TimedCache> cache_;
};

TEST_F(CacheTest, PutAndGetReturnsValue) {
    cache_->put("key1", "value1");
    auto result = cache_->get("key1");
    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(*result, "value1");
}

TEST_F(CacheTest, GetMissingKeyReturnsEmpty) {
    auto result = cache_->get("nonexistent");
    ASSERT_FALSE(result.has_value());
}

TEST_F(CacheTest, EntryExpiresAfterTTL) {
    cache_->put("ephemeral", "data", 50ms);
    // Wait for entry to expire
    std::this_thread::sleep_for(60ms);
    auto result = cache_->get("ephemeral");
    ASSERT_FALSE(result.has_value());
}

TEST_F(CacheTest, EvictRemovesExpiredEntries) {
    cache_->put("a", "1", 30ms);
    cache_->put("b", "2", 200ms);
    std::this_thread::sleep_for(40ms);
    cache_->evict_expired();
    ASSERT_EQ(cache_->size(), 1u);
    ASSERT_FALSE(cache_->get("a").has_value());
    ASSERT_TRUE(cache_->get("b").has_value());
}

TEST_F(CacheTest, ConcurrentAccessDoesNotCrash) {
    // Stress test: multiple threads reading and writing
    auto writer = [this]() {
        for (int i = 0; i < 100; ++i) {
            cache_->put("key" + std::to_string(i), "val" + std::to_string(i));
        }
    };

    auto reader = [this]() {
        for (int i = 0; i < 100; ++i) {
            cache_->get("key" + std::to_string(i));
        }
    };

    std::thread t1(writer);
    std::thread t2(reader);
    std::thread t3(writer);

    t1.join();
    t2.join();
    t3.join();

    // Just verify no crash; exact size depends on timing
    ASSERT_GE(cache_->size(), 0u);
}

TEST_F(CacheTest, CustomTTLOverridesDefault) {
    cache_->put("short", "quick", 20ms);
    cache_->put("long", "lasting", 500ms);
    std::this_thread::sleep_for(30ms);
    ASSERT_FALSE(cache_->get("short").has_value());
    ASSERT_TRUE(cache_->get("long").has_value());
}
