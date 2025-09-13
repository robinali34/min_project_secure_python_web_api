# Secure Python Web API

A comprehensive Python-based web API demonstrating security best practices with PostgreSQL. This project showcases modern security techniques, authentication, authorization, input validation, and monitoring.

## 🛡️ Security Features

### Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **Password hashing** using bcrypt with configurable rounds
- **Account locking** after failed login attempts
- **Role-based access control** with superuser privileges
- **Session management** with token revocation

### Input Validation & Sanitization
- **Pydantic schemas** for request/response validation
- **Password strength validation** with complexity requirements
- **Input sanitization** to prevent injection attacks
- **Email and username format validation**
- **SQL injection prevention**

### Security Headers & Middleware
- **Comprehensive security headers** (HSTS, CSP, X-Frame-Options, etc.)
- **CORS configuration** with allowed origins
- **Rate limiting** to prevent abuse
- **Request ID tracking** for audit trails
- **Slow request monitoring**

### Database Security
- **SSL-required connections** to PostgreSQL
- **Connection pooling** with security parameters
- **Prepared statements** to prevent SQL injection
- **Audit logging** for all database operations
- **Secure connection parameters**

### Monitoring & Logging
- **Structured logging** with JSON format
- **Security event tracking** for all operations
- **Failed login attempt monitoring**
- **Account lockout tracking**
- **Performance monitoring**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd secure_python_web_api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Configure PostgreSQL**
   ```bash
   # Create database
   createdb secure_api_db
   
   # Set up user with appropriate permissions
   psql -c "CREATE USER api_user WITH PASSWORD 'secure_password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE secure_api_db TO api_user;"
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   python -m app.main
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecurePass123!
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

#### Change Password
```http
POST /auth/change-password
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

### User Management Endpoints

#### Get Current User
```http
GET /users/me
Authorization: Bearer your_access_token
```

#### Update Profile
```http
PUT /users/me
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

### Security Monitoring Endpoints

#### Get Security Events
```http
GET /security/events?hours=24&severity=WARNING
Authorization: Bearer your_superuser_token
```

#### Security Health Check
```http
GET /security/health
Authorization: Bearer your_access_token
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (min 32 chars) | Required |
| `BCRYPT_ROUNDS` | Password hashing rounds | 12 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token validity | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token validity | 7 |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | 60 |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `ALLOWED_HOSTS` | Allowed host headers | `["localhost", "127.0.0.1"]` |

### Security Configuration

The application includes several security configurations:

- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, digits, and special characters
- **Account Lockout**: 5 failed attempts lock account for 30 minutes
- **Token Expiration**: Configurable access and refresh token lifetimes
- **Rate Limiting**: Configurable per-minute request limits
- **Security Headers**: Comprehensive set of security headers

## 🧪 Testing

### Run Tests
```bash
pytest
```

### Test Coverage
```bash
pytest --cov=app --cov-report=html
```

### Security Testing
```bash
# Test password strength validation
python -c "from app.security_utils import SecurityValidator; print(SecurityValidator.validate_password_strength('weak'))"

# Test input sanitization
python -c "from app.security_utils import SecurityValidator; print(SecurityValidator.sanitize_input('test<script>alert(1)</script>'))"
```

## 🔍 Security Best Practices Implemented

### 1. Authentication Security
- Strong password requirements
- Account lockout after failed attempts
- JWT tokens with short expiration times
- Refresh token rotation
- Secure password hashing with bcrypt

### 2. Input Validation
- Comprehensive input validation using Pydantic
- SQL injection prevention
- XSS prevention through input sanitization
- Length and format validation

### 3. Database Security
- SSL-required connections
- Parameterized queries
- Connection pooling with security settings
- Audit logging for all operations

### 4. API Security
- Rate limiting to prevent abuse
- CORS configuration
- Security headers
- Request/response validation

### 5. Monitoring & Logging
- Structured logging for security events
- Failed login attempt tracking
- Performance monitoring
- Security event correlation

## 🚨 Security Considerations

### Production Deployment

1. **Environment Variables**
   - Use strong, unique secret keys
   - Configure proper CORS origins
   - Set appropriate rate limits
   - Use environment-specific database URLs

2. **Database Security**
   - Use SSL connections
   - Implement database-level security policies
   - Regular security updates
   - Backup and recovery procedures

3. **Infrastructure Security**
   - Use HTTPS in production
   - Implement proper firewall rules
   - Regular security updates
   - Monitor logs and metrics

4. **Application Security**
   - Regular dependency updates
   - Security scanning
   - Penetration testing
   - Code review processes

## 📖 Development

### Code Quality
```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For security issues, please contact the maintainers directly.

For general questions and support, please open an issue in the repository.

## 🔗 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
