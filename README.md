# Secure Python Web API

A secure Python web API with PostgreSQL demonstrating security best practices.

## Project Structure

```
├── app/                    # Main application code
│   ├── routers/           # API route handlers
│   ├── templates/         # HTML templates
│   └── ...
├── alembic/               # Database migrations
├── config/                # Configuration files
│   ├── alembic.ini
│   ├── mypy.ini
│   ├── pytest.ini
│   ├── setup.cfg
│   └── pyproject.toml
├── data/                  # Generated data files
│   ├── *.db              # Database files
│   ├── *.json            # Reports
│   ├── *.xml             # Coverage reports
│   └── htmlcov/          # HTML coverage reports
├── docs/                  # Documentation
│   ├── README.md
│   └── SECURITY.md
├── examples/             # Example configurations
│   ├── env.example
│   ├── init-db.sql
│   └── nginx.conf
├── requirements/          # Python dependencies
│   ├── requirements.txt
│   └── requirements-dev.txt
├── scripts/               # Utility scripts
│   ├── create_superuser.py
│   ├── generate_ssl_cert.sh
│   └── setup.sh
├── tests/                 # Test files
├── tools/                 # Debug and test utilities
├── .github/workflows/     # CI/CD workflows
├── docker-compose.yml     # Docker configuration
├── Dockerfile
└── Makefile              # Build automation
```

## Quick Start

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Set up development environment:**
   ```bash
   make setup-dev
   ```

3. **Run tests:**
   ```bash
   make test
   ```

4. **Start the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

- **Environment variables:** Copy `examples/env.example` to `.env` and configure
- **Database:** See `examples/init-db.sql` for database setup
- **Nginx:** See `examples/nginx.conf` for reverse proxy configuration

## Development

- **Code formatting:** `make format`
- **Linting:** `make lint`
- **Type checking:** `make type-check`
- **Security scans:** `make security`

## Documentation

For detailed documentation, see the `docs/` directory:
- [README.md](docs/README.md) - Detailed project documentation
- [SECURITY.md](docs/SECURITY.md) - Security guidelines and practices

## License

This project is licensed under the MIT License.
