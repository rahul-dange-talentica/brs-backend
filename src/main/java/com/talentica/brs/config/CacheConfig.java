package com.talentica.brs.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import com.github.benmanes.caffeine.cache.stats.CacheStats;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * Cache configuration for the Book Review System.
 * Configures Caffeine cache with proper TTL, eviction policies, and monitoring.
 */
@Slf4j
@Configuration
@EnableCaching
public class CacheConfig {

    /**
     * Configure Caffeine cache manager with optimized settings.
     * 
     * @return configured CacheManager instance
     */
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager();
        
        // Configure default cache settings
        cacheManager.setCaffeine(Caffeine.newBuilder()
                .maximumSize(1000)
                .expireAfterWrite(Duration.ofHours(1))
                .expireAfterAccess(Duration.ofMinutes(30))
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("Cache entry removed: key={}, cause={}", key, cause))
        );
        
        // Set cache names for the manager
        cacheManager.setCacheNames(java.util.List.of(
            "bookDetails", "bookReviews", "userProfile", "recommendations", "popularBooks"
        ));
        
        log.info("Cache manager configured with Caffeine");
        return cacheManager;
    }

    /**
     * Configure book details cache with specific settings.
     * 
     * @return configured Caffeine cache for book details
     */
    @Bean("bookDetailsCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> bookDetailsCache() {
        return Caffeine.newBuilder()
                .maximumSize(500)
                .expireAfterWrite(2, TimeUnit.HOURS)
                .expireAfterAccess(1, TimeUnit.HOURS)
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("Book details cache entry removed: key={}, cause={}", key, cause))
                .build();
    }

    /**
     * Configure book reviews cache with specific settings.
     * 
     * @return configured Caffeine cache for book reviews
     */
    @Bean("bookReviewsCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> bookReviewsCache() {
        return Caffeine.newBuilder()
                .maximumSize(300)
                .expireAfterWrite(1, TimeUnit.HOURS)
                .expireAfterAccess(30, TimeUnit.MINUTES)
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("Book reviews cache entry removed: key={}, cause={}", key, cause))
                .build();
    }

    /**
     * Configure user profile cache with specific settings.
     * 
     * @return configured Caffeine cache for user profiles
     */
    @Bean("userProfileCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> userProfileCache() {
        return Caffeine.newBuilder()
                .maximumSize(200)
                .expireAfterWrite(4, TimeUnit.HOURS)
                .expireAfterAccess(2, TimeUnit.HOURS)
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("User profile cache entry removed: key={}, cause={}", key, cause))
                .build();
    }

    /**
     * Configure recommendations cache with specific settings.
     * 
     * @return configured Caffeine cache for recommendations
     */
    @Bean("recommendationsCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> recommendationsCache() {
        return Caffeine.newBuilder()
                .maximumSize(100)
                .expireAfterWrite(1, TimeUnit.HOURS)
                .expireAfterAccess(30, TimeUnit.MINUTES)
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("Recommendations cache entry removed: key={}, cause={}", key, cause))
                .build();
    }

    /**
     * Configure popular books cache with specific settings.
     * 
     * @return configured Caffeine cache for popular books
     */
    @Bean("popularBooksCache")
    public com.github.benmanes.caffeine.cache.Cache<String, Object> popularBooksCache() {
        return Caffeine.newBuilder()
                .maximumSize(50)
                .expireAfterWrite(6, TimeUnit.HOURS)
                .expireAfterAccess(3, TimeUnit.HOURS)
                .recordStats()
                .removalListener((key, value, cause) -> 
                    log.debug("Popular books cache entry removed: key={}, cause={}", key, cause))
                .build();
    }

    /**
     * Log cache statistics for monitoring purposes.
     * This method can be called periodically to monitor cache performance.
     */
    public void logCacheStats() {
        log.info("=== Cache Statistics ===");
        log.info("Book Details Cache: {}", getCacheStats(bookDetailsCache()));
        log.info("Book Reviews Cache: {}", getCacheStats(bookReviewsCache()));
        log.info("User Profile Cache: {}", getCacheStats(userProfileCache()));
        log.info("Recommendations Cache: {}", getCacheStats(recommendationsCache()));
        log.info("Popular Books Cache: {}", getCacheStats(popularBooksCache()));
    }

    /**
     * Get formatted cache statistics.
     * 
     * @param cache the cache to get stats for
     * @return formatted statistics string
     */
    private String getCacheStats(com.github.benmanes.caffeine.cache.Cache<String, Object> cache) {
        CacheStats stats = cache.stats();
        return String.format("Size: %d, Hits: %d, Misses: %d, Hit Rate: %.2f%%", 
            cache.estimatedSize(), 
            stats.hitCount(), 
            stats.missCount(),
            stats.hitRate() * 100);
    }
}
