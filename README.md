# Book Review System Backend

A comprehensive Spring Boot 3.x backend service for managing books, user reviews, ratings, and recommendations.

## 🚀 Technology Stack

- **Java**: 21 (LTS)
- **Spring Boot**: 3.2.0
- **Build Tool**: Gradle 8.5
- **Database**: PostgreSQL 15+
- **Migration**: Flyway 10.8.1
- **JPA Provider**: Hibernate 6.x
- **Security**: Spring Security + JWT
- **Caching**: Caffeine
- **Testing**: JUnit 5 + Testcontainers

## 📋 Prerequisites

- Java 21 (OpenJDK or Oracle JDK)
- PostgreSQL 15+ installed and running
- Gradle 8.5+ (or use the included wrapper)

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd brs-backend
```

### 2. Set Up Database

#### Option A: Using the Setup Script

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -h localhost

# Run the setup script
\i database-setup.sql
```

#### Option B: Manual Setup

```sql
-- Create database
CREATE DATABASE brs_dev;

-- Create user
CREATE USER brs_user WITH PASSWORD 'dev_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE brs_dev TO brs_user;
```

### 3. Build and Run

```bash
# Using Gradle wrapper
./gradlew bootRun

# Or build and run JAR
./gradlew build
java -jar build/libs/brs-backend-0.0.1-SNAPSHOT.jar
```

### 4. Verify Installation

- **Application**: http://localhost:8080/api/v1
- **Health Check**: http://localhost:8080/api/v1/actuator/health
- **H2 Console** (test profile): http://localhost:8080/h2-console

## 🗄️ Database Schema

The system includes the following core entities:

- **Users**: User accounts with authentication
- **Books**: Book catalog with metadata and ratings
- **Reviews**: User reviews and ratings (1-5 stars)
- **Favorites**: User-book relationships

### Key Features

- **Soft Deletion**: All entities support soft delete for data retention
- **Rating Aggregation**: Automatic rating calculation via database triggers
- **Full-text Search**: PostgreSQL GIN indexes for book search
- **Performance Indexes**: Strategic indexing for common queries

## 🔧 Configuration

### Environment Profiles

- **dev**: Development configuration with PostgreSQL
- **test**: Test configuration with H2 in-memory database
- **prod**: Production configuration (configure via environment variables)

### Key Configuration Files

- `application.yml`: Main configuration
- `application-dev.yml`: Development profile
- `application-test.yml`: Test profile

### Database Configuration

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/brs_dev
    username: brs_user
    password: dev_password
```

## 🧪 Testing

### Run Tests

```bash
# All tests
./gradlew test

# Specific test class
./gradlew test --tests BookReviewServiceApplicationTests

# Integration tests
./gradlew integrationTest
```

### Test Coverage

```bash
./gradlew jacocoTestReport
```

## 📚 API Documentation

Once the application is running, access the API documentation:

- **Swagger UI**: http://localhost:8080/api/v1/swagger-ui.html
- **OpenAPI Spec**: http://localhost:8080/api/v1/v3/api-docs

## 🏗️ Project Structure

```
src/
├── main/
│   ├── java/com/talentica/brs/
│   │   ├── BookReviewServiceApplication.java
│   │   ├── controller/          # REST endpoints
│   │   ├── service/            # Business logic
│   │   ├── repository/         # Data access
│   │   ├── model/             # Entities and DTOs
│   │   ├── config/            # Configuration classes
│   │   └── exception/         # Custom exceptions
│   └── resources/
│       ├── application.yml     # Main configuration
│       └── db/migration/      # Flyway migrations
└── test/
    ├── java/                  # Test classes
    └── resources/             # Test configuration
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: BCrypt password encryption
- **Rate Limiting**: API rate limiting to prevent abuse
- **CORS Configuration**: Cross-origin resource sharing setup

## 📊 Monitoring & Health

- **Health Checks**: Database, cache, and application health
- **Metrics**: Prometheus metrics export
- **Actuator**: Spring Boot Actuator endpoints

## 🚀 Deployment

### Docker

```bash
# Build Docker image
docker build -t brs-backend .

# Run container
docker run -p 8080:8080 brs-backend
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the Technical PRD in the `docs/` folder

## 📈 Roadmap

- [x] Project setup and database schema
- [ ] User management system
- [ ] Book management system
- [ ] Review and rating system
- [ ] JWT authentication
- [ ] Recommendation engine
- [ ] API documentation
- [ ] Performance optimization
- [ ] Kubernetes deployment

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Status**: In Development
