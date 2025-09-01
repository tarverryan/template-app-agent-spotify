# Spotify App Agent Template

[![CI/CD Pipeline](https://github.com/yourusername/spotify-app-agent-template/workflows/CI/badge.svg)](https://github.com/yourusername/spotify-app-agent-template/actions)
[![Code Coverage](https://codecov.io/gh/yourusername/spotify-app-agent-template/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/spotify-app-agent-template)
[![Security](https://img.shields.io/badge/security-bandit-yellow.svg)](https://bandit.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 🔒 **SECURITY WARNING**
**FACT:** This template requires Spotify API credentials to function. **NEVER commit your actual credentials to version control!**

**SECURITY REQUIREMENTS:**
- Create a `.env` file with your credentials (see setup instructions)
- Keep your `.env` file out of version control (it's already in `.gitignore`)
- Rotate your Spotify API credentials regularly
- Never hardcode credentials in source code

**See [SECURITY.md](SECURITY.md) for detailed security guidelines.**

---

A comprehensive template for building automated Spotify playlist management bots. This template provides a solid foundation for creating personalized music curation agents that can automatically update playlists based on your listening preferences and schedule.

## ✨ What This Template Provides

- **🎵 Automated Playlist Management**: Create and manage multiple playlists with intelligent track selection
- **🤖 Intelligent Track Selection**: Advanced algorithms for discovering and scoring tracks
- **⏰ Flexible Scheduling**: Configurable update schedules using cron expressions
- **🎨 Custom Branding**: Personalize your bot's identity and playlist names
- **📊 Comprehensive Monitoring**: Real-time dashboard and detailed logging
- **🔐 Secure Authentication**: OAuth 2.0 with automatic token refresh
- **🐳 Docker Support**: Containerized deployment for consistency
- **📚 Educational Content**: Detailed comments and learning objectives

## 🚀 Quick Start

1. **Clone the template**:
   ```bash
   git clone https://github.com/yourusername/spotify-app-agent-template.git
   cd spotify-app-agent-template
   ```

2. **Follow the setup guide**:
   ```bash
   # Read the comprehensive setup guide
   cat TEMPLATE_SETUP.md
   ```

3. **Configure your bot**:
   - Create Spotify API credentials
   - Set up your playlists
   - Configure your bot's persona
   - Customize track selection preferences

4. **Deploy and run**:
   ```bash
   make build
   make run
   ```

## 📁 Project Structure

```
spotify-app-agent-template/
├── app/                          # Main application code
│   ├── main.py                   # Entry point and bot orchestration
│   ├── spotify_client.py         # Spotify API client
│   ├── track_selector.py         # Track selection logic
│   └── playlist_manager.py       # Playlist management
├── config/
│   └── config.yaml               # Configuration file
├── docs/                         # Documentation
│   ├── diagrams/                 # Architecture diagrams
│   ├── user_guides/              # User guides and examples
│   └── development/              # Development documentation
├── scripts/                      # Authentication scripts
├── tools/                        # Utility scripts
├── tests/                        # Test suite
├── .env                          # Environment variables (credentials)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── Makefile                      # Build and run commands
└── README.md                     # This file
```

## ⚙️ Configuration

### Basic Configuration

Edit `config/config.yaml` to customize your bot:

```yaml
persona:
  name: "Your Bot Name"
  prefix: "Your Bot's "
  bio: "Your bot's description"

playlists:
  playlist1:
    id: "your-playlist1-id"
    size: 50
    schedule_cron: "0 4 * * *"  # Daily at 4 AM
    active: true
  playlist2:
    id: "your-playlist2-id"
    size: 100
    schedule_cron: "0 4 * * 6"  # Weekly on Saturday
    active: true
```

### Environment Variables

Create a `.env` file with your credentials:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REFRESH_TOKEN=your_refresh_token
SPOTIFY_USER_ID=your_user_id
```

## 🎯 Usage

### Quick Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
make init-db

# Interactive setup
python tools/cli.py setup
```

### Docker Commands

```bash
# Build the container
make build

# Run the bot
make run

# Stop the bot
make stop

# View logs
make logs

# Test connection
make test
```

### Manual Playlist Updates

```bash
# Update specific playlists
make update-playlist1
make update-playlist2

# Update all playlists
python tools/preseed_playlists.py
```

### Advanced Features

```bash
# Web Dashboard
make dashboard

# Analytics
make analytics

# CLI Management
python tools/cli.py status
python tools/cli.py logs
python tools/cli.py config

# Database Management
make init-db
make reset-db
```

### Monitoring

```bash
# View dashboard
python tools/dashboard.py

# Check bot status
python tools/test_bot.py
```

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main

# Run tests
python -m pytest tests/
```

### Available Tools

- **`tools/test_bot.py`**: Test Spotify connection and configuration
- **`tools/dashboard.py`**: Monitor bot performance and status
- **`tools/create_missing_playlists.py`**: Create playlists automatically
- **`tools/update_playlist_art.py`**: Update playlist cover art
- **`tools/rename_playlists.py`**: Rename playlists to match your branding

## 🔧 Customization

### Track Selection

Customize how tracks are selected by modifying the scoring weights:

```yaml
scoring:
  weights:
    popularity: 0.55
    popularity_delta: 0.30
    recency_boost: 0.10
    audio_feature_fit: 0.05
```

### Genre Preferences

Define your preferred genres and their weights:

```yaml
genres:
  buckets:
    Pop: ["pop", "indie pop", "dance pop"]
    HipHop: ["hip hop", "rap", "trap"]
    Rock: ["rock", "alternative rock", "indie rock"]
```

### Scheduling

Set custom update schedules using cron expressions:

```yaml
playlists:
  playlist1:
    schedule_cron: "0 4 * * *"  # Daily at 4 AM
  playlist2:
    schedule_cron: "0 4 * * 6"  # Weekly on Saturday
```

## 📊 Monitoring and Analytics

### Dashboard

Access the real-time dashboard to monitor your bot:

```bash
python tools/dashboard.py
```

The dashboard shows:
- Bot status and health
- Playlist statistics
- Recent updates and errors
- Performance metrics

### Logging

Comprehensive logging is available:

```bash
# View logs
tail -f logs/spotify_bot.log

# Or use Docker
make logs
```

## 🔐 Security

### Credential Management

- **Environment Variables**: All credentials stored in `.env` file
- **No Hardcoding**: Never hardcode secrets in source code
- **Secure Storage**: Credentials stored outside container
- **Token Refresh**: Automatic OAuth token refresh

### Best Practices

- Rotate credentials regularly
- Monitor API usage and rate limits
- Use strong passwords for your Spotify account
- Keep the template updated with security patches

## 🆘 Troubleshooting

### Common Issues

**Authentication Errors**
- Verify credentials in `.env` file
- Regenerate refresh token if needed
- Check Spotify app configuration

**Playlist Access Errors**
- Ensure playlists are public
- Verify playlist IDs are correct
- Check user permissions

**Configuration Errors**
- Validate YAML syntax
- Check required fields
- Verify cron expressions

### Getting Help

1. **Check the logs** for detailed error messages
2. **Review documentation** in the `docs/` folder
3. **Test components** using provided tools
4. **Check GitHub Issues** for known problems

## 📚 Documentation

- **[TEMPLATE_SETUP.md](TEMPLATE_SETUP.md)**: Complete setup guide
- **[SECURITY.md](SECURITY.md)**: Security guidelines and best practices
- **[docs/diagrams/](docs/diagrams/)**: Architecture diagrams
- **[docs/user_guides/](docs/user_guides/)**: User guides and examples
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: How to contribute

## 🛠️ Development

### Industry-Standard Development Workflow

This template follows enterprise-grade development practices:

#### **Code Quality & Testing**
```bash
# Install development dependencies
make dev-setup

# Run comprehensive tests
make test

# Code quality checks
make lint

# Format code
make format

# Security scanning
make security
```

#### **CI/CD Pipeline**
- **Automated Testing**: Multi-Python version testing (3.9, 3.10, 3.11)
- **Code Quality**: Black, isort, flake8, mypy
- **Security Scanning**: Bandit, Safety
- **Docker Testing**: Container build and test verification
- **Coverage Reporting**: Codecov integration

#### **Development Tools**
- **Pre-commit Hooks**: Automatic code formatting and quality checks
- **Docker Compose**: Complete development environment
- **Monitoring Stack**: Prometheus + Grafana for observability
- **Comprehensive Makefile**: 50+ commands for all development tasks

#### **Quality Standards**
- **Type Hints**: Full mypy compliance
- **Documentation**: Comprehensive docstrings and guides
- **Testing**: Unit, integration, and performance tests
- **Security**: Regular vulnerability scanning
- **Performance**: Load testing and optimization

### Advanced Features

#### **Monitoring & Observability**
```bash
# Start monitoring stack
make monitoring

# View metrics
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

#### **Performance Testing**
```bash
# Run performance tests
make perf-test

# Load testing
make load-test
```

#### **Database Operations**
```bash
# Database migrations
make db-migrate

# Seed database
make db-seed
```

#### **Release Management**
```bash
# Create releases
make release
make release-patch
make release-minor
make release-major
```

### Development Environment

#### **Docker Development**
```bash
# Start development environment
docker-compose up dev

# Run tests in container
docker-compose run --rm test

# Code quality in container
docker-compose run --rm lint
```

#### **Local Development**
```bash
# Install with development extras
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run development server
make dev-run
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Contribution Guidelines

- **Code Style**: Follow Black and isort formatting
- **Testing**: Maintain >90% code coverage
- **Documentation**: Update docs for new features
- **Security**: No hardcoded credentials or secrets
- **Performance**: Consider impact on API rate limits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify Web API** for providing the music data
- **Python community** for excellent libraries and tools
- **Docker** for containerization support
- **Open source contributors** for inspiration and feedback

---

**🎵 Happy playlist curating!** This template gives you everything you need to build your own personalized Spotify playlist curation bot.
