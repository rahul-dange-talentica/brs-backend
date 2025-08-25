package com.talentica.brs.model.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * User entity representing a user account in the Book Review System.
 * 
 * This entity stores user authentication information, personal details,
 * and account status. It supports soft deletion and audit timestamps.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@Entity
@Table(name = "users")
@EntityListeners(AuditingEntityListener.class)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {

    /**
     * Unique identifier for the user.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Unique username for authentication and display.
     * Must be between 3 and 50 characters.
     */
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    @Column(name = "username", unique = true, nullable = false, length = 50)
    private String username;

    /**
     * User's email address for communication and account recovery.
     * Must be a valid email format and unique across the system.
     */
    @NotBlank(message = "Email is required")
    @Email(message = "Email must be a valid email address")
    @Column(name = "email", unique = true, nullable = false, length = 100)
    private String email;

    /**
     * User's first name.
     * Must be between 1 and 100 characters.
     */
    @NotBlank(message = "First name is required")
    @Size(min = 1, max = 100, message = "First name must be between 1 and 100 characters")
    @Column(name = "first_name", nullable = false, length = 100)
    private String firstName;

    /**
     * User's last name.
     * Must be between 1 and 100 characters.
     */
    @NotBlank(message = "Last name is required")
    @Size(min = 1, max = 100, message = "Last name must be between 1 and 100 characters")
    @Column(name = "last_name", nullable = false, length = 100)
    private String lastName;

    /**
     * Hashed password for user authentication.
     * Stored as BCrypt hash for security.
     */
    @NotBlank(message = "Password is required")
    @Column(name = "password", nullable = false)
    private String password;

    /**
     * Timestamp when the user account was created.
     * Automatically set on entity creation.
     */
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Timestamp when the user account was last updated.
     * Automatically updated on entity modification.
     */
    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * Timestamp when the user account was soft deleted.
     * Null indicates the account is active.
     */
    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    /**
     * Flag indicating whether the user account is active.
     * Defaults to true for new accounts.
     */
    @Column(name = "is_active", nullable = false)
    @Builder.Default
    private Boolean isActive = true;

    /**
     * Checks if the user account is currently active.
     * 
     * @return true if the account is active, false otherwise
     */
    @Transient
    public boolean isAccountActive() {
        return isActive && deletedAt == null;
    }

    /**
     * Performs a soft delete of the user account.
     * Sets the deletedAt timestamp and deactivates the account.
     */
    public void softDelete() {
        this.deletedAt = LocalDateTime.now();
        this.isActive = false;
    }

    /**
     * Restores a soft-deleted user account.
     * Clears the deletedAt timestamp and reactivates the account.
     */
    public void restore() {
        this.deletedAt = null;
        this.isActive = true;
    }
}
