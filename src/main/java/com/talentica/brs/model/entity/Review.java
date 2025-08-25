package com.talentica.brs.model.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

/**
 * Review entity representing a user's review and rating of a book.
 * 
 * This entity stores user feedback including numerical ratings (1-5 stars)
 * and optional review text. It maintains relationships with both users
 * and books, and supports soft deletion for data retention.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@Entity
@Table(name = "reviews")
@EntityListeners(AuditingEntityListener.class)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Review {

    /**
     * Unique identifier for the review.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * The book being reviewed.
     * Required relationship with cascade delete.
     */
    @NotNull(message = "Book is required")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_id", nullable = false, foreignKey = @ForeignKey(name = "fk_reviews_book"))
    private Book book;

    /**
     * The user who wrote the review.
     * Required relationship with cascade delete.
     */
    @NotNull(message = "User is required")
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_reviews_user"))
    private User user;

    /**
     * Numerical rating given by the user.
     * Must be between 1 and 5 (whole numbers only).
     */
    @NotNull(message = "Rating is required")
    @Min(value = 1, message = "Rating must be at least 1")
    @Max(value = 5, message = "Rating must be at most 5")
    @Column(name = "rating", nullable = false)
    private Integer rating;

    /**
     * Optional text review written by the user.
     * Provides additional context beyond the numerical rating.
     */
    @Column(name = "review_text", columnDefinition = "TEXT")
    private String reviewText;

    /**
     * Timestamp when the review was created.
     * Automatically set on entity creation.
     */
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Timestamp when the review was last updated.
     * Automatically updated on entity modification.
     */
    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * Timestamp when the review was soft deleted.
     * Null indicates the review is active.
     */
    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    /**
     * Checks if the review is currently active.
     * 
     * @return true if the review is active, false otherwise
     */
    @Transient
    public boolean isActive() {
        return deletedAt == null;
    }

    /**
     * Performs a soft delete of the review.
     * Sets the deletedAt timestamp.
     */
    public void softDelete() {
        this.deletedAt = LocalDateTime.now();
    }

    /**
     * Restores a soft-deleted review.
     * Clears the deletedAt timestamp.
     */
    public void restore() {
        this.deletedAt = null;
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
     * Gets the user ID for convenience.
     * 
     * @return the user ID
     */
    @Transient
    public Long getUserId() {
        return user != null ? user.getId() : null;
    }

    /**
     * Gets the rating as a display string.
     * 
     * @return formatted rating string
     */
    @Transient
    public String getRatingDisplay() {
        if (rating == null) {
            return "No rating";
        }
        return rating + " star" + (rating == 1 ? "" : "s");
    }

    /**
     * Checks if the review has text content.
     * 
     * @return true if the review has text, false otherwise
     */
    @Transient
    public boolean hasText() {
        return reviewText != null && !reviewText.trim().isEmpty();
    }

    /**
     * Gets a truncated version of the review text for display.
     * 
     * @param maxLength maximum length of the truncated text
     * @return truncated review text
     */
    @Transient
    public String getTruncatedText(int maxLength) {
        if (!hasText()) {
            return "";
        }
        if (reviewText.length() <= maxLength) {
            return reviewText;
        }
        return reviewText.substring(0, maxLength - 3) + "...";
    }
}
