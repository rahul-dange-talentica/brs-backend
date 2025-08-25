package com.talentica.brs.model.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Set;

/**
 * Book entity representing a book in the Book Review System.
 * 
 * This entity stores book metadata, including title, author, description,
 * genres, and aggregated rating information. It supports soft deletion
 * and maintains real-time rating statistics.
 * 
 * @author Development Team
 * @version 1.0
 * @since 2024-12-01
 */
@Entity
@Table(name = "books")
@EntityListeners(AuditingEntityListener.class)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Book {

    /**
     * Unique identifier for the book.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * International Standard Book Number (ISBN) for the book.
     * Must be unique across the system.
     */
    @NotBlank(message = "ISBN is required")
    @Size(max = 20, message = "ISBN must not exceed 20 characters")
    @Column(name = "isbn", unique = true, nullable = false, length = 20)
    private String isbn;

    /**
     * Title of the book.
     * Must be between 1 and 255 characters.
     */
    @NotBlank(message = "Title is required")
    @Size(max = 255, message = "Title must not exceed 255 characters")
    @Column(name = "title", nullable = false, length = 255)
    private String title;

    /**
     * Author of the book.
     * Must be between 1 and 255 characters.
     */
    @NotBlank(message = "Author is required")
    @Size(max = 255, message = "Author must not exceed 255 characters")
    @Column(name = "author", nullable = false, length = 255)
    private String author;

    /**
     * Description or summary of the book.
     * Optional field for additional book information.
     */
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    /**
     * URL to the book's cover image.
     * Optional field for visual representation.
     */
    @Column(name = "cover_image_url", columnDefinition = "TEXT")
    private String coverImageUrl;

    /**
     * Array of genres associated with the book.
     * Uses PostgreSQL TEXT[] for flexible genre categorization.
     */
    @NotNull(message = "Genres are required")
    @Column(name = "genres", nullable = false, columnDefinition = "TEXT[] DEFAULT '{}'")
    private String[] genres;

    /**
     * Year when the book was published.
     * Optional field for historical context.
     */
    @Column(name = "published_year")
    private Integer publishedYear;

    /**
     * Average rating of the book based on user reviews.
     * Ranges from 0.0 to 5.0 with one decimal place precision.
     * Automatically calculated and maintained by database triggers.
     */
    @Column(name = "average_rating", precision = 2, scale = 1, nullable = false)
    @Builder.Default
    private BigDecimal averageRating = BigDecimal.ZERO;

    /**
     * Total number of active reviews for the book.
     * Automatically maintained by database triggers.
     */
    @Column(name = "total_ratings", nullable = false)
    @Builder.Default
    private Integer totalRatings = 0;

    /**
     * Timestamp when the book was added to the system.
     * Automatically set on entity creation.
     */
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Timestamp when the book was last updated.
     * Automatically updated on entity modification.
     */
    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * Timestamp when the book was soft deleted.
     * Null indicates the book is active.
     */
    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    /**
     * Checks if the book is currently active.
     * 
     * @return true if the book is active, false otherwise
     */
    @Transient
    public boolean isActive() {
        return deletedAt == null;
    }

    /**
     * Performs a soft delete of the book.
     * Sets the deletedAt timestamp.
     */
    public void softDelete() {
        this.deletedAt = LocalDateTime.now();
    }

    /**
     * Restores a soft-deleted book.
     * Clears the deletedAt timestamp.
     */
    public void restore() {
        this.deletedAt = null;
    }

    /**
     * Checks if the book has sufficient ratings to display an average.
     * Books with less than 5 ratings are considered insufficient.
     * 
     * @return true if the book has sufficient ratings, false otherwise
     */
    @Transient
    public boolean hasSufficientRatings() {
        return totalRatings >= 5;
    }

    /**
     * Gets the display rating text based on the number of ratings.
     * 
     * @return appropriate rating display text
     */
    @Transient
    public String getRatingDisplayText() {
        if (totalRatings == 0) {
            return "No ratings yet";
        } else if (totalRatings < 5) {
            return "Insufficient ratings";
        } else {
            return String.format("%.1f out of 5", averageRating);
        }
    }

    /**
     * Adds a genre to the book's genre list.
     * 
     * @param genre the genre to add
     */
    public void addGenre(String genre) {
        if (genres == null) {
            genres = new String[0];
        }
        String[] newGenres = new String[genres.length + 1];
        System.arraycopy(genres, 0, newGenres, 0, genres.length);
        newGenres[genres.length] = genre;
        this.genres = newGenres;
    }

    /**
     * Removes a genre from the book's genre list.
     * 
     * @param genre the genre to remove
     * @return true if the genre was removed, false if it wasn't found
     */
    public boolean removeGenre(String genre) {
        if (genres == null || genres.length == 0) {
            return false;
        }
        
        for (int i = 0; i < genres.length; i++) {
            if (genre.equals(genres[i])) {
                String[] newGenres = new String[genres.length - 1];
                System.arraycopy(genres, 0, newGenres, 0, i);
                System.arraycopy(genres, i + 1, newGenres, i, genres.length - i - 1);
                this.genres = newGenres;
                return true;
            }
        }
        return false;
    }
}
