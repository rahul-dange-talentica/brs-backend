package com.talentica.brs;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Main Spring Boot application class for the Book Review System.
 * 
 * This application provides a comprehensive backend service for managing books,
 * user reviews, ratings, and recommendations. It follows a layered architecture
 * with proper separation of concerns and industry best practices.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@SpringBootApplication
@EnableJpaAuditing
@EnableCaching
@EnableAsync
public class BookReviewServiceApplication {

    /**
     * Main method to start the Spring Boot application.
     * 
     * @param args command line arguments
     */
    public static void main(String[] args) {
        SpringApplication.run(BookReviewServiceApplication.class, args);
    }
}
