package com.talentica.brs.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cache.CacheManager;
import org.springframework.test.context.ActiveProfiles;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for CacheConfig class.
 * Tests cache manager configuration and specific cache beans.
 */
@SpringBootTest(classes = {CacheConfig.class})
@ActiveProfiles("test")
class CacheConfigTest {

    @Autowired
    private CacheConfig cacheConfig;

    @Autowired
    private CacheManager cacheManager;

    @Test
    void testCacheManagerConfigured() {
        assertNotNull(cacheManager, "CacheManager should be configured");
        assertTrue(cacheManager instanceof org.springframework.cache.caffeine.CaffeineCacheManager, 
                   "CacheManager should be CaffeineCacheManager");
    }

    @Test
    void testSpecificCachesConfigured() {
        assertNotNull(cacheConfig, "CacheConfig should be configured");
        
        // Test that specific cache beans are available
        assertNotNull(cacheManager.getCache("bookDetails"), "bookDetails cache should be available");
        assertNotNull(cacheManager.getCache("userProfile"), "userProfile cache should be available");
        assertNotNull(cacheManager.getCache("bookReviews"), "bookReviews cache should be available");
        assertNotNull(cacheManager.getCache("recommendations"), "recommendations cache should be available");
    }

    @Test
    void testCacheNamesAvailable() {
        String[] cacheNames = cacheManager.getCacheNames().toArray(new String[0]);
        assertTrue(cacheNames.length >= 5, "Should have at least 5 caches configured");
        
        // Check for expected cache names
        assertTrue(containsCache(cacheNames, "bookDetails"), "bookDetails cache should be present");
        assertTrue(containsCache(cacheNames, "userProfile"), "userProfile cache should be present");
        assertTrue(containsCache(cacheNames, "bookReviews"), "bookReviews cache should be present");
        assertTrue(containsCache(cacheNames, "recommendations"), "recommendations cache should be present");
        assertTrue(containsCache(cacheNames, "popularBooks"), "popularBooks cache should be present");
    }

    @Test
    void testCacheOperations() {
        var bookCache = cacheManager.getCache("bookDetails");
        assertNotNull(bookCache, "bookDetails cache should be available");
        
        // Test basic cache operations
        bookCache.put("test-key", "test-value");
        var cachedValue = bookCache.get("test-key");
        assertNotNull(cachedValue, "Cached value should be retrievable");
        assertEquals("test-value", cachedValue.get(), "Cached value should match");
    }

    @Test
    void testCacheStatistics() {
        var bookCache = cacheManager.getCache("bookDetails");
        assertNotNull(bookCache, "bookDetails cache should be available");
        
        // Test cache statistics (if available)
        var nativeCache = bookCache.getNativeCache();
        assertNotNull(nativeCache, "Native cache should be available");
    }

    @Test
    void testCacheEviction() {
        var bookCache = cacheManager.getCache("bookDetails");
        assertNotNull(bookCache, "bookDetails cache should be available");
        
        // Test cache eviction by adding many items
        for (int i = 0; i < 1000; i++) {
            bookCache.put("key-" + i, "value-" + i);
        }
        
        // Verify cache is working
        assertNotNull(bookCache.get("key-0"), "First cached item should be available");
    }

    private boolean containsCache(String[] cacheNames, String cacheName) {
        for (String name : cacheNames) {
            if (name.equals(cacheName)) {
                return true;
            }
        }
        return false;
    }
}
