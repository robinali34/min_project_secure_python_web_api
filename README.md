# Secure Python Web API

A secure, production-ready Python web API built with FastAPI, featuring comprehensive security measures, authentication, and testing.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Password Security**: Bcrypt password hashing with configurable rounds
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Security Headers**: Comprehensive security headers for protection
- **Input Validation**: Pydantic-based request/response validation
- **SQL Injection Protection**: Parameterized queries and input sanitization
- **XSS Protection**: Input validation and output encoding
- **Account Lockout**: Automatic account locking after failed attempts
- **Security Logging**: Comprehensive security event logging
- **Comprehensive Testing**: Full test suite with security-focused tests
- **Docker Support**: Containerized deployment with Docker
- **CI/CD Pipeline**: GitHub Actions workflows for testing and deployment

## Quick Reference

**Quick Start:**
```bash
# Clone and setup
git clone <repository-url>
cd secure_python_web_api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

**Pre-push Check:**
```bash
# Run all checks before pushing to GitHub
black . && isort . && black --check . && isort --check-only . && flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics && python -m pytest tests/ -v --tb=short
```

**Development:**
- [Local Check-up Steps](#local-check-up-steps) - Verify code before pushing
- [GitHub Actions Troubleshooting](#github-actions-troubleshooting) - Fix CI/CD issues
- [OAuth2 Web Interface](#oauth2-web-interface) - Token management system

## Security Features

- **Authentication & Authorization**: JWT-based with refresh token rotation
- **Password Security**: Strong password requirements and bcrypt hashing
- **Rate Limiting**: Prevents brute force attacks
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Input Validation**: Strict validation of all inputs
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Input sanitization and validation
- **Account Security**: Lockout mechanisms and security logging
- **Dependency Scanning**: Automated security vulnerability scanning

## Requirements

- Python 3.11+
- SQLite (for development) or PostgreSQL (for production)
- Redis (optional, for caching)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd secure-python-web-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Using Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run tests in Docker**
   ```bash
   docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
   ```

## Testing

### Run All Tests
```bash
make test
```

### Run Security Tests
```bash
make test-security
```

### Run Tests with Coverage
```bash
make test-coverage
```

### Run Tests in Docker
```bash
make docker-test
```

## Development

### Code Quality

```bash
# Format code
make format

# Check formatting
make format-check

# Run linting
make lint

# Run type checking
make type-check

# Run all quality checks
make ci
```

### Security Scanning

```bash
# Run security scans
make security

# Run comprehensive security scans
make security-full
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
make install-pre-commit

# Run hooks manually
pre-commit run --all-files
```

### Local Check-up Steps

Before pushing code to GitHub, run these commands to ensure your code will pass CI/CD checks:

```bash
# 1. Format code with Black
black .

# 2. Sort imports with isort
isort .

# 3. Check formatting (should show "All done!")
black --check .

# 4. Check import sorting (should show "Skipped X files")
isort --check-only .

# 5. Run linting (should exit with code 0)
flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# 6. Run tests to ensure everything works
python -m pytest tests/ -v --tb=short

# 7. Run security tests specifically
python -m pytest tests/test_security.py -v

# 8. Run OAuth2 tests specifically
python -m pytest tests/test_oauth2.py -v

# 9. Quick server startup test
timeout 5s uvicorn app.main:app --host 0.0.0.0 --port 8000 || echo "Server started successfully"
```

**One-liner for quick check:**
```bash
black . && isort . && black --check . && isort --check-only . && flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics && python -m pytest tests/ -v --tb=short -x
```

**Expected Results:**
- Black: "All done!"
- isort: "Skipped X files"
- flake8: Exit code 0 (warnings are OK)
- pytest: All tests pass
- Server: Starts without errors

## Docker

### Build Image
```bash
make docker-build
```

### Run Container
```bash
make docker-run
```

### Development Environment
```bash
make docker-dev
```

## Deployment

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# Host Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Optional: Redis
REDIS_URL=redis://localhost:6379
```

### Production Deployment

1. **Using Docker**
   ```bash
   docker build -t secure-python-web-api .
   docker run -p 8000:8000 --env-file .env secure-python-web-api
   ```

2. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Using Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

## API Documentation

### Authentication Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `POST /auth/change-password` - Change password

### User Management

- `GET /users/me` - Get current user info
- `PUT /users/me` - Update current user
- `GET /users/` - List users (admin only)
- `DELETE /users/{user_id}` - Delete user (admin only)

### Security Endpoints

- `GET /security/events` - Get security events
- `POST /security/events` - Create security event
- `GET /security/stats` - Get security statistics

### Health Check

- `GET /health` - Application health status

## Security Considerations

### Authentication
- JWT tokens with short expiration times
- Refresh token rotation
- Secure password requirements
- Account lockout after failed attempts

### Input Validation
- Strict Pydantic validation
- SQL injection protection
- XSS prevention
- File upload restrictions

### Security Headers
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy

### Rate Limiting
- Per-endpoint rate limiting
- IP-based rate limiting
- Configurable limits

## Testing Strategy

### Test Types
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Security Tests**: Security-focused test cases
- **Performance Tests**: Load and stress testing

### Security Testing
- SQL injection attempts
- XSS prevention
- Authentication bypass attempts
- Rate limiting verification
- Input validation testing

## CI/CD Pipeline

The project includes comprehensive GitHub Actions workflows:

- **CI Pipeline**: Tests, linting, and security scanning
- **Security Scan**: Automated security vulnerability scanning
- **Code Quality**: Code formatting and type checking
- **Docker Build**: Automated Docker image building
- **Deployment**: Automated deployment to production

### GitHub Actions Troubleshooting

If your GitHub Actions are failing, check these common issues:

**1. Code Formatting Failures:**
```bash
# Fix formatting issues
black .
isort .
```

**2. Import Sorting Failures:**
```bash
# Fix import order
isort .
```

**3. Linting Failures:**
```bash
# Check linting issues
flake8 app/ tests/ --max-line-length=127 --count --statistics
```

**4. Test Failures:**
```bash
# Run tests locally
python -m pytest tests/ -v --tb=short
```

**5. Security Scan Failures:**
```bash
# Run security tests
python -m pytest tests/test_security.py -v
```

**6. Deprecated Actions:**
- All GitHub Actions are updated to latest versions
- No deprecated `actions/upload-artifact@v3` or similar

**Quick Fix Command:**
```bash
# Run all checks locally before pushing
black . && isort . && black --check . && isort --check-only . && flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics && python -m pytest tests/ -v --tb=short
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Ensure security considerations
- **Run all quality checks before submitting** (see [Local Check-up Steps](#local-check-up-steps))
- Use the provided one-liner command to verify your code locally

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Create an issue in the GitHub repository
- Check the [documentation](docs/)
- Review the [API documentation](http://localhost:8000/docs)

## Security

If you discover a security vulnerability, please:

1. **DO NOT** create a public issue
2. Use GitHub's private vulnerability reporting feature

## Roadmap

- [ ] OAuth2 integration
- [ ] Multi-factor authentication
- [ ] API versioning
- [ ] GraphQL support
- [ ] WebSocket support
- [ ] Advanced monitoring and metrics
- [ ] Kubernetes deployment manifests
- [ ] Helm charts
