package com.talentica.brs.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import java.time.Duration;

/**
 * Application-specific configuration properties.
 * Provides type-safe access to application configuration values.
 */
@Data
@Component
@Validated
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    /**
     * Security-related configuration properties.
     */
    private Security security = new Security();

    /**
     * Monitoring and metrics configuration properties.
     */
    private Monitoring monitoring = new Monitoring();

    /**
     * Debug and development configuration properties.
     */
    private Debug debug = new Debug();

    /**
     * Security configuration properties.
     */
    @Data
    public static class Security {
        
        /**
         * CORS configuration properties.
         */
        private Cors cors = new Cors();

        /**
         * CORS configuration details.
         */
        @Data
        public static class Cors {
            
            /**
             * Allowed origins for CORS requests.
             */
            @NotBlank(message = "CORS allowed origins must be specified")
            private String allowedOrigins = "*";
            
            /**
             * Allowed HTTP methods for CORS requests.
             */
            @NotBlank(message = "CORS allowed methods must be specified")
            private String allowedMethods = "GET,POST,PUT,DELETE,OPTIONS";
            
            /**
             * Allowed headers for CORS requests.
             */
            @NotBlank(message = "CORS allowed headers must be specified")
            private String allowedHeaders = "*";
            
            /**
             * Whether to allow credentials in CORS requests.
             */
            @NotNull(message = "CORS allow credentials must be specified")
            private Boolean allowCredentials = false;
            
            /**
             * Maximum age for CORS preflight requests in seconds.
             */
            @Positive(message = "CORS max age must be positive")
            private Long maxAge = 3600L;
        }
    }

    /**
     * Monitoring configuration properties.
     */
    @Data
    public static class Monitoring {
        
        /**
         * Whether monitoring is enabled.
         */
        @NotNull(message = "Monitoring enabled flag must be specified")
        private Boolean enabled = true;
        
        /**
         * Whether metrics collection is enabled.
         */
        @NotNull(message = "Metrics collection flag must be specified")
        private Boolean metricsCollection = true;
        
        /**
         * Health check interval in seconds.
         */
        @NotBlank(message = "Health check interval must be specified")
        private String healthCheckInterval = "30s";
        
        /**
         * Get health check interval as Duration.
         */
        public Duration getHealthCheckIntervalAsDuration() {
            return Duration.parse("PT" + healthCheckInterval);
        }
    }

    /**
     * Debug configuration properties.
     */
    @Data
    public static class Debug {
        
        /**
         * Whether debug mode is enabled.
         */
        @NotNull(message = "Debug enabled flag must be specified")
        private Boolean enabled = false;
        
        /**
         * Whether to show SQL queries.
         */
        @NotNull(message = "Show SQL flag must be specified")
        private Boolean showSql = false;
        
        /**
         * Whether to show cache operations.
         */
        @NotNull(message = "Show cache flag must be specified")
        private Boolean showCache = false;
    }
}
