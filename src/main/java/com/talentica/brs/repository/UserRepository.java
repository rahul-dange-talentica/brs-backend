package com.talentica.brs.repository;

import com.talentica.brs.model.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository interface for User entity operations.
 * 
 * Provides data access methods for user management including CRUD operations,
 * authentication queries, and soft delete support. Extends JpaRepository for
 * basic CRUD functionality and adds custom query methods.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    /**
     * Finds a user by username, excluding soft-deleted users.
     * 
     * @param username the username to search for
     * @return Optional containing the user if found
     */
    @Query("SELECT u FROM User u WHERE u.username = :username AND u.deletedAt IS NULL")
    Optional<User> findByUsername(@Param("username") String username);

    /**
     * Finds a user by email, excluding soft-deleted users.
     * 
     * @param email the email to search for
     * @return Optional containing the user if found
     */
    @Query("SELECT u FROM User u WHERE u.email = :email AND u.deletedAt IS NULL")
    Optional<User> findByEmail(@Param("email") String username);

    /**
     * Finds a user by username or email, excluding soft-deleted users.
     * Used for authentication purposes.
     * 
     * @param usernameOrEmail the username or email to search for
     * @return Optional containing the user if found
     */
    @Query("SELECT u FROM User u WHERE (u.username = :usernameOrEmail OR u.email = :usernameOrEmail) AND u.deletedAt IS NULL")
    Optional<User> findByUsernameOrEmail(@Param("usernameOrEmail") String usernameOrEmail);

    /**
     * Checks if a username exists, excluding soft-deleted users.
     * 
     * @param username the username to check
     * @return true if the username exists, false otherwise
     */
    @Query("SELECT COUNT(u) > 0 FROM User u WHERE u.username = :username AND u.deletedAt IS NULL")
    boolean existsByUsername(@Param("username") String username);

    /**
     * Checks if an email exists, excluding soft-deleted users.
     * 
     * @param email the email to check
     * @return true if the email exists, false otherwise
     */
    @Query("SELECT COUNT(u) > 0 FROM User u WHERE u.email = :email AND u.deletedAt IS NULL")
    boolean existsByEmail(@Param("email") String email);

    /**
     * Finds all active users with pagination.
     * 
     * @param pageable pagination and sorting parameters
     * @return Page of active users
     */
    @Query("SELECT u FROM User u WHERE u.deletedAt IS NULL AND u.isActive = true")
    Page<User> findAllActive(Pageable pageable);

    /**
     * Finds all active users.
     * 
     * @return List of active users
     */
    @Query("SELECT u FROM User u WHERE u.deletedAt IS NULL AND u.isActive = true")
    List<User> findAllActive();

    /**
     * Finds users by first name or last name containing the search term.
     * 
     * @param searchTerm the term to search for in names
     * @param pageable pagination and sorting parameters
     * @return Page of matching users
     */
    @Query("SELECT u FROM User u WHERE u.deletedAt IS NULL AND " +
           "(LOWER(u.firstName) LIKE LOWER(CONCAT('%', :searchTerm, '%')) OR " +
           "LOWER(u.lastName) LIKE LOWER(CONCAT('%', :searchTerm, '%')))")
    Page<User> findByNameContaining(@Param("searchTerm") String searchTerm, Pageable pageable);

    /**
     * Finds users created within a specific date range.
     * 
     * @param startDate the start date (inclusive)
     * @param endDate the end date (inclusive)
     * @param pageable pagination and sorting parameters
     * @return Page of users created in the date range
     */
    @Query("SELECT u FROM User u WHERE u.deletedAt IS NULL AND u.createdAt BETWEEN :startDate AND :endDate")
    Page<User> findByCreatedAtBetween(@Param("startDate") LocalDateTime startDate, 
                                     @Param("endDate") LocalDateTime endDate, 
                                     Pageable pageable);

    /**
     * Counts active users.
     * 
     * @return the number of active users
     */
    @Query("SELECT COUNT(u) FROM User u WHERE u.deletedAt IS NULL AND u.isActive = true")
    long countActiveUsers();

    /**
     * Counts users created within a specific date range.
     * 
     * @param startDate the start date (inclusive)
     * @param endDate the end date (inclusive)
     * @return the number of users created in the date range
     */
    @Query("SELECT COUNT(u) FROM User u WHERE u.deletedAt IS NULL AND u.createdAt BETWEEN :startDate AND :endDate")
    long countByCreatedAtBetween(@Param("startDate") LocalDateTime startDate, 
                                @Param("endDate") LocalDateTime endDate);
}
