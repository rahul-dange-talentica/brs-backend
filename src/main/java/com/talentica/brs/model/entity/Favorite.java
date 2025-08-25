package com.talentica.brs.model.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * Favorite entity representing a user's favorite book relationship.
 * 
 * This entity maintains a many-to-many relationship between users and books
 * for tracking user preferences. It supports soft deletion and maintains
 * creation timestamps for tracking when favorites were added.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@Entity
@Table(name = "favorites")
@EntityListeners(AuditingEntityListener.class)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Favorite {

    /**
     * Unique identifier for the favorite relationship.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * The user who marked the book as favorite.
     * Required relationship with cascade delete.
     */
    @NotNull(message = "User is required")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_favorites_user"))
    private User user;

    /**
     * The book marked as favorite by the user.
     * Required relationship with cascade delete.
     */
    @NotNull(message = "Book is required")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_id", nullable = false, foreignKey = @ForeignKey(name = "fk_favorites_book"))
    private Book book;

    /**
     * Timestamp when the book was marked as favorite.
     * Automatically set on entity creation.
     */
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Gets the user ID for convenience.
     * 
     * @return the user ID
     */
    @Transient
    public Long getUserId() {
        return user != null ? user.getId() : null;
    }

    /**
     * Gets the book ID for convenience.
     * 
     * @return the book ID
     */
    @Transient
    public Long getBookId() {
        return book != null ? book.getId() : null;
    }

    /**
     * Gets the username for display purposes.
     * 
     * @return the username
     */
    @Transient
    public String getUsername() {
        return user != null ? user.getUsername() : null;
    }

    /**
     * Gets the book title for display purposes.
     * 
     * @return the book title
     */
    @Transient
    public String getBookTitle() {
        return book != null ? book.getTitle() : null;
    }

    /**
     * Gets the book author for display purposes.
     * 
     * @return the book author
     */
    @Transient
    public String getBookAuthor() {
        return book != null ? book.getAuthor() : null;
    }

    /**
     * Gets the book cover image URL for display purposes.
     * 
     * @return the book cover image URL
     */
    @Transient
    public String getBookCoverImageUrl() {
        return book != null ? book.getCoverImageUrl() : null;
    }

    /**
     * Gets the book average rating for display purposes.
     * 
     * @return the book average rating
     */
    @Transient
    public String getBookRatingDisplay() {
        return book != null ? book.getRatingDisplayText() : null;
    }
}
