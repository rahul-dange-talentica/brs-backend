package com.talentica.brs;

import com.talentica.brs.model.entity.User;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Simplified schema validation test for the Book Review System.
 * 
 * This test verifies basic entity functionality without complex PostgreSQL features
 * that H2 doesn't support well (like TEXT[] arrays).
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class SimpleSchemaValidationTest {

    @PersistenceContext
    private EntityManager entityManager;

    @Autowired
    private Validator validator;

    @Test
    void testUserEntityCreation() {
        // Create a valid user
        User user = User.builder()
                .username("testuser")
                .email("test@example.com")
                .firstName("Test")
                .lastName("User")
                .password("$2a$10$test.hash.password")
                .isActive(true)
                .build();

        // Validate entity
        Set<ConstraintViolation<User>> violations = validator.validate(user);
        assertTrue(violations.isEmpty(), "User entity should have no validation violations");

        // Persist and verify
        entityManager.persist(user);
        entityManager.flush();
        entityManager.clear();

        User foundUser = entityManager.find(User.class, user.getId());
        assertNotNull(foundUser);
        assertEquals("testuser", foundUser.getUsername());
        assertEquals("test@example.com", foundUser.getEmail());
        assertTrue(foundUser.isAccountActive());
        assertNotNull(foundUser.getCreatedAt());
        assertNotNull(foundUser.getUpdatedAt());
        assertNull(foundUser.getDeletedAt());
    }

    @Test
    void testUserSoftDelete() {
        // Create and persist user
        User user = User.builder()
                .username("deleteuser" + System.currentTimeMillis())
                .email("delete" + System.currentTimeMillis() + "@example.com")
                .firstName("Delete")
                .lastName("User")
                .password("$2a$10$test.hash.password")
                .isActive(true)
                .build();

        entityManager.persist(user);
        entityManager.flush();

        // Test soft delete
        user.softDelete();
        assertFalse(user.isAccountActive());
        assertNotNull(user.getDeletedAt());

        // Test restore
        user.restore();
        assertTrue(user.isAccountActive());
        assertNull(user.getDeletedAt());
    }

    @Test
    void testUserValidationConstraints() {
        // Test username validation
        User userWithoutUsername = User.builder()
                .email("test@example.com")
                .firstName("Test")
                .lastName("User")
                .password("$2a$10$test.hash.password")
                .isActive(true)
                .build();

        Set<ConstraintViolation<User>> violations = validator.validate(userWithoutUsername);
        assertFalse(violations.isEmpty(), "User without username should have validation violations");
        assertTrue(violations.stream().anyMatch(v -> v.getPropertyPath().toString().equals("username")));

        // Test email validation
        User userWithInvalidEmail = User.builder()
                .username("testuser")
                .email("invalid-email")
                .firstName("Test")
                .lastName("User")
                .password("$2a$10$test.hash.password")
                .isActive(true)
                .build();

        violations = validator.validate(userWithInvalidEmail);
        assertFalse(violations.isEmpty(), "User with invalid email should have validation violations");
        assertTrue(violations.stream().anyMatch(v -> v.getPropertyPath().toString().equals("email")));
    }

    @Test
    void testApplicationContextLoads() {
        // This test verifies that the Spring application context loads successfully
        // with all required beans and configurations
        assertNotNull(entityManager, "EntityManager should be available");
        assertNotNull(validator, "Validator should be available");
    }

    @Test
    void testDatabaseConnection() {
        // This test verifies that we can connect to the database and perform basic operations
        try {
            // Simple query to test database connectivity
            Long count = entityManager.createQuery("SELECT COUNT(u) FROM User u", Long.class).getSingleResult();
            assertNotNull(count, "Database query should return a result");
        } catch (Exception e) {
            fail("Database connection test failed: " + e.getMessage());
        }
    }
}
