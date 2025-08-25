package com.talentica.brs.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for AppProperties class.
 * Tests configuration properties loading and validation.
 */
@SpringBootTest(classes = {AppProperties.class})
@ActiveProfiles("test")
class AppPropertiesTest {

    @Autowired
    private AppProperties appProperties;

    @Test
    void testAppPropertiesLoaded() {
        assertNotNull(appProperties, "AppProperties should be loaded");
        assertNotNull(appProperties.getSecurity(), "Security properties should be loaded");
        assertNotNull(appProperties.getMonitoring(), "Monitoring properties should be loaded");
        assertNotNull(appProperties.getDebug(), "Debug properties should be loaded");
    }

    @Test
    void testSecurityProperties() {
        AppProperties.Security security = appProperties.getSecurity();
        assertNotNull(security, "Security should not be null");
        
        AppProperties.Security.Cors cors = security.getCors();
        assertNotNull(cors, "CORS should not be null");
        assertNotNull(cors.getAllowedOrigins(), "Allowed origins should not be null");
        assertNotNull(cors.getAllowedMethods(), "Allowed methods should not be null");
        assertNotNull(cors.getAllowedHeaders(), "Allowed headers should not be null");
    }

    @Test
    void testMonitoringProperties() {
        AppProperties.Monitoring monitoring = appProperties.getMonitoring();
        assertNotNull(monitoring, "Monitoring should not be null");
        assertNotNull(monitoring.getEnabled(), "Monitoring enabled should not be null");
        assertNotNull(monitoring.getMetricsCollection(), "Metrics collection should not be null");
        assertNotNull(monitoring.getHealthCheckInterval(), "Health check interval should not be null");
    }

    @Test
    void testDebugProperties() {
        AppProperties.Debug debug = appProperties.getDebug();
        assertNotNull(debug, "Debug should not be null");
        assertNotNull(debug.getEnabled(), "Debug enabled should not be null");
        assertNotNull(debug.getShowSql(), "Show SQL should not be null");
        assertNotNull(debug.getShowCache(), "Show cache should not be null");
    }

    @Test
    void testPropertyValidation() {
        // Test that properties have reasonable default values
        AppProperties.Security.Cors cors = appProperties.getSecurity().getCors();
        assertFalse(cors.getAllowedOrigins().isEmpty(), "Allowed origins should not be empty");
        assertFalse(cors.getAllowedMethods().isEmpty(), "Allowed methods should not be empty");
        assertFalse(cors.getAllowedHeaders().isEmpty(), "Allowed headers should not be empty");
        
        AppProperties.Monitoring monitoring = appProperties.getMonitoring();
        assertNotNull(monitoring.getEnabled(), "Monitoring enabled should have a value");
        assertNotNull(monitoring.getMetricsCollection(), "Metrics collection should have a value");
    }
}
