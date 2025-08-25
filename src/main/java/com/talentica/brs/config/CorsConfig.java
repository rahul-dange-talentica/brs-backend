package com.talentica.brs.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * CORS configuration for the Book Review System.
 * Handles cross-origin requests with configurable settings.
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class CorsConfig {

    private final AppProperties appProperties;

    /**
     * Configure CORS configuration source.
     * 
     * @return configured CorsConfigurationSource
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // Get CORS settings from application properties
        String allowedOrigins = appProperties.getSecurity().getCors().getAllowedOrigins();
        String allowedMethods = appProperties.getSecurity().getCors().getAllowedMethods();
        String allowedHeaders = appProperties.getSecurity().getCors().getAllowedHeaders();
        Boolean allowCredentials = appProperties.getSecurity().getCors().getAllowCredentials();
        Long maxAge = appProperties.getSecurity().getCors().getMaxAge();
        
        // Configure allowed origins
        if ("*".equals(allowedOrigins)) {
            configuration.setAllowedOriginPatterns(List.of("*"));
        } else {
            configuration.setAllowedOrigins(Arrays.asList(allowedOrigins.split(",")));
        }
        
        // Configure allowed methods
        configuration.setAllowedMethods(Arrays.asList(allowedMethods.split(",")));
        
        // Configure allowed headers
        if ("*".equals(allowedHeaders)) {
            configuration.setAllowedHeaders(List.of("*"));
        } else {
            configuration.setAllowedHeaders(Arrays.asList(allowedHeaders.split(",")));
        }
        
        // Configure credentials
        configuration.setAllowCredentials(allowCredentials);
        
        // Configure max age
        configuration.setMaxAge(maxAge);
        
        // Configure exposed headers
        configuration.setExposedHeaders(Arrays.asList(
            "Authorization", 
            "Content-Type", 
            "X-Requested-With", 
            "Accept", 
            "Origin", 
            "Access-Control-Request-Method", 
            "Access-Control-Request-Headers"
        ));
        
        // Log CORS configuration
        log.info("CORS configuration: origins={}, methods={}, headers={}, credentials={}, maxAge={}",
                allowedOrigins, allowedMethods, allowedHeaders, allowCredentials, maxAge);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        
        return source;
    }
}
