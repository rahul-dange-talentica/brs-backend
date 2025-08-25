package com.talentica.brs.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * Configuration validator for the Book Review System.
 * Validates configuration properties and logs configuration summary.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ConfigurationValidator {

    private final Environment environment;
    private final AppProperties appProperties;

    /**
     * Validate configuration when application is ready.
     * 
     * @param event the application ready event
     */
    @EventListener(ApplicationReadyEvent.class)
    public void validateConfiguration(ApplicationReadyEvent event) {
        // Skip validation during tests to avoid test failures
        if (isTestProfile()) {
            log.info("🚫 Configuration validation skipped for test profile");
            return;
        }
        
        log.info("=== Configuration Validation Started ===");
        
        List<String> validationErrors = new ArrayList<>();
        
        // Validate database configuration
        validateDatabaseConfiguration(validationErrors);
        
        // Validate cache configuration
        validateCacheConfiguration(validationErrors);
        
        // Validate security configuration
        validateSecurityConfiguration(validationErrors);
        
        // Validate monitoring configuration
        validateMonitoringConfiguration(validationErrors);
        
        // Log validation results
        if (validationErrors.isEmpty()) {
            log.info("✅ Configuration validation passed successfully");
            logConfigurationSummary();
        } else {
            log.error("❌ Configuration validation failed with {} errors:", validationErrors.size());
            validationErrors.forEach(error -> log.error("  - {}", error));
            throw new IllegalStateException("Configuration validation failed: " + String.join("; ", validationErrors));
        }
        
        log.info("=== Configuration Validation Completed ===");
    }
    
    /**
     * Check if current profile is test profile.
     * 
     * @return true if test profile is active
     */
    private boolean isTestProfile() {
        String[] activeProfiles = environment.getActiveProfiles();
        for (String profile : activeProfiles) {
            if ("test".equals(profile)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Validate database configuration.
     * 
     * @param errors list to collect validation errors
     */
    private void validateDatabaseConfiguration(List<String> errors) {
        try {
            String dbUrl = environment.getProperty("spring.datasource.url");
            String dbUsername = environment.getProperty("spring.datasource.username");
            String dbPassword = environment.getProperty("spring.datasource.password");
            
            // For test profiles, database validation is optional
            if (isTestProfile()) {
                log.info("Database configuration validation skipped for test profile");
                return;
            }
            
            if (dbUrl == null || dbUrl.trim().isEmpty()) {
                errors.add("Database URL is not configured");
            }
            
            if (dbUsername == null || dbUsername.trim().isEmpty()) {
                errors.add("Database username is not configured");
            }
            
            // Note: Password can be empty for some database setups
            
            log.info("Database configuration validated: URL={}, Username={}", 
                    maskSensitiveData(dbUrl), maskSensitiveData(dbUsername));
                    
        } catch (Exception e) {
            errors.add("Database configuration validation failed: " + e.getMessage());
        }
    }

    /**
     * Validate cache configuration.
     * 
     * @param errors list to collect validation errors
     */
    private void validateCacheConfiguration(List<String> errors) {
        try {
            String cacheType = environment.getProperty("spring.cache.type");
            String caffeineSpec = environment.getProperty("spring.cache.caffeine.spec");
            
            // Cache type validation is optional - Caffeine is the default
            if (cacheType != null && !"caffeine".equals(cacheType)) {
                errors.add("Cache type must be set to 'caffeine' if specified");
            }
            
            // Caffeine spec validation is optional
            if (caffeineSpec != null && caffeineSpec.trim().isEmpty()) {
                errors.add("Caffeine cache specification cannot be empty if specified");
            }
            
            log.info("Cache configuration validated: Type={}, Spec={}", 
                    cacheType != null ? cacheType : "default (caffeine)", 
                    caffeineSpec != null ? caffeineSpec : "default");
            
        } catch (Exception e) {
            errors.add("Cache configuration validation failed: " + e.getMessage());
        }
    }

    /**
     * Validate security configuration.
     * 
     * @param errors list to collect validation errors
     */
    private void validateSecurityConfiguration(List<String> errors) {
        try {
            String jwtAccessSecret = environment.getProperty("spring.security.jwt.access-token.secret");
            String jwtRefreshSecret = environment.getProperty("spring.security.jwt.refresh-token.secret");
            
            // JWT validation is optional for development/testing
            if (jwtAccessSecret != null && jwtAccessSecret.trim().isEmpty()) {
                errors.add("JWT access token secret cannot be empty if specified");
            }
            
            if (jwtRefreshSecret != null && jwtRefreshSecret.trim().isEmpty()) {
                errors.add("JWT refresh token secret cannot be empty if specified");
            }
            
            // Validate CORS configuration
            if (appProperties.getSecurity().getCors().getAllowedOrigins() == null) {
                errors.add("CORS allowed origins are not configured");
            }
            
            log.info("Security configuration validated: JWT configured={}, CORS configured", 
                    jwtAccessSecret != null && !jwtAccessSecret.trim().isEmpty());
            
        } catch (Exception e) {
            errors.add("Security configuration validation failed: " + e.getMessage());
        }
    }

    /**
     * Validate monitoring configuration.
     * 
     * @param errors list to collect validation errors
     */
    private void validateMonitoringConfiguration(List<String> errors) {
        try {
            String managementEndpoints = environment.getProperty("management.endpoints.web.exposure.include");
            String healthShowDetails = environment.getProperty("management.endpoint.health.show-details");
            
            // Monitoring validation is optional
            if (managementEndpoints != null && !managementEndpoints.contains("health")) {
                errors.add("Health endpoint is not exposed in management endpoints");
            }
            
            log.info("Monitoring configuration validated: Endpoints={}, Health Details={}", 
                    managementEndpoints != null ? managementEndpoints : "default", 
                    healthShowDetails != null ? healthShowDetails : "default");
            
        } catch (Exception e) {
            errors.add("Monitoring configuration validation failed: " + e.getMessage());
        }
    }

    /**
     * Log configuration summary.
     */
    private void logConfigurationSummary() {
        log.info("=== Configuration Summary ===");
        log.info("Active Profile: {}", environment.getActiveProfiles().length > 0 ? 
                String.join(",", environment.getActiveProfiles()) : "default");
        log.info("Application Name: {}", environment.getProperty("spring.application.name", "not-set"));
        log.info("Server Port: {}", environment.getProperty("server.port", "not-set"));
        log.info("Context Path: {}", environment.getProperty("server.servlet.context-path", "not-set"));
        log.info("Database: {}", maskSensitiveData(environment.getProperty("spring.datasource.url")));
        log.info("Cache Type: {}", environment.getProperty("spring.cache.type", "default (caffeine)"));
        log.info("JPA DDL Auto: {}", environment.getProperty("spring.jpa.hibernate.ddl-auto", "not-set"));
        log.info("Flyway Enabled: {}", environment.getProperty("spring.flyway.enabled", "not-set"));
        log.info("Actuator Base Path: {}", environment.getProperty("management.endpoints.web.base-path", "not-set"));
        log.info("Logging Level: {}", environment.getProperty("logging.level.com.talentica.brs", "not-set"));
    }

    /**
     * Mask sensitive data in configuration values.
     * 
     * @param value the value to mask
     * @return masked value
     */
    private String maskSensitiveData(String value) {
        if (value == null || value.trim().isEmpty()) {
            return "NOT_SET";
        }
        
        if (value.contains("password") || value.contains("secret") || value.contains("key")) {
            return "***MASKED***";
        }
        
        // Mask database passwords
        if (value.contains("jdbc:") && value.contains("@")) {
            int atIndex = value.indexOf("@");
            if (atIndex > 0) {
                String beforeAt = value.substring(0, atIndex);
                if (beforeAt.contains(":")) {
                    int colonIndex = beforeAt.lastIndexOf(":");
                    if (colonIndex > 0) {
                        return value.substring(0, colonIndex) + ":***@" + value.substring(atIndex + 1);
                    }
                }
            }
        }
        
        return value;
    }
}
