package com.talentica.brs.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Simple unit tests for configuration classes.
 * These tests don't require Spring context loading.
 */
class SimpleConfigTest {

    private AppProperties appProperties;

    @BeforeEach
    void setUp() {
        appProperties = new AppProperties();
        
        // Set up test data
        AppProperties.Security.Cors cors = new AppProperties.Security.Cors();
        cors.setAllowedOrigins("*");
        cors.setAllowedMethods("GET,POST,PUT,DELETE,OPTIONS");
        cors.setAllowedHeaders("*");
        cors.setAllowCredentials(false);
        cors.setMaxAge(3600L);
        
        AppProperties.Security security = new AppProperties.Security();
        security.setCors(cors);
        appProperties.setSecurity(security);
        
        AppProperties.Monitoring monitoring = new AppProperties.Monitoring();
        monitoring.setEnabled(true);
        monitoring.setMetricsCollection(true);
        monitoring.setHealthCheckInterval("30s");
        appProperties.setMonitoring(monitoring);
        
        AppProperties.Debug debug = new AppProperties.Debug();
        debug.setEnabled(true);
        debug.setShowSql(true);
        debug.setShowCache(true);
        appProperties.setDebug(debug);
    }

    @Test
    void testAppPropertiesConfiguration() {
        assertNotNull(appProperties, "AppProperties should not be null");
        assertNotNull(appProperties.getSecurity(), "Security should not be null");
        assertNotNull(appProperties.getSecurity().getCors(), "CORS should not be null");
        assertNotNull(appProperties.getMonitoring(), "Monitoring should not be null");
        assertNotNull(appProperties.getDebug(), "Debug should not be null");
    }

    @Test
    void testSecurityConfiguration() {
        AppProperties.Security.Cors cors = appProperties.getSecurity().getCors();
        assertEquals("*", cors.getAllowedOrigins(), "Allowed origins should be *");
        assertEquals("GET,POST,PUT,DELETE,OPTIONS", cors.getAllowedMethods(), "Allowed methods should match");
        assertEquals("*", cors.getAllowedHeaders(), "Allowed headers should be *");
        assertFalse(cors.getAllowCredentials(), "Allow credentials should be false");
        assertEquals(3600L, cors.getMaxAge(), "Max age should be 3600L");
    }

    @Test
    void testMonitoringConfiguration() {
        AppProperties.Monitoring monitoring = appProperties.getMonitoring();
        assertTrue(monitoring.getEnabled(), "Monitoring should be enabled");
        assertTrue(monitoring.getMetricsCollection(), "Metrics collection should be enabled");
        assertEquals("30s", monitoring.getHealthCheckInterval(), "Health check interval should be 30s");
    }

    @Test
    void testDebugConfiguration() {
        AppProperties.Debug debug = appProperties.getDebug();
        assertTrue(debug.getEnabled(), "Debug should be enabled");
        assertTrue(debug.getShowSql(), "Show SQL should be enabled");
        assertTrue(debug.getShowCache(), "Show cache should be enabled");
    }

    @Test
    void testCacheConfigCreation() {
        // Test that CacheConfig can be instantiated
        CacheConfig cacheConfig = new CacheConfig();
        assertNotNull(cacheConfig, "CacheConfig should be created successfully");
    }

    @Test
    void testAsyncConfigCreation() {
        // Test that AsyncConfig can be instantiated
        AsyncConfig asyncConfig = new AsyncConfig();
        assertNotNull(asyncConfig, "AsyncConfig should be created successfully");
    }

    @Test
    void testCorsConfigCreation() {
        // Test that CorsConfig can be instantiated
        CorsConfig corsConfig = new CorsConfig(appProperties);
        assertNotNull(corsConfig, "CorsConfig should be created successfully");
    }
}
