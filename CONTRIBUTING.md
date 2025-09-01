# Contributing to Spotify App Agent Template

Thank you for your interest in contributing to the Spotify App Agent Template! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (for testing)
- Spotify Developer Account
- Git

### Development Setup
1. **Fork and clone** the repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```
3. **Set up environment**:
   ```bash
   cp docs/env.example .env
   cp docs/config.yaml.example config/config.yaml
   # Edit .env with your Spotify credentials
   ```
4. **Run tests**:
   ```bash
   pytest
   ```

## 📝 Code Style

### Python
- **Type hints**: Use type hints for all function parameters and return values
- **Docstrings**: Follow Google-style docstrings for all public functions and classes
- **Line length**: Maximum 88 characters (Black formatter)
- **Imports**: Use absolute imports, group imports (standard library, third-party, local)

### Example
```python
from typing import Dict, List, Optional
import logging

from .spotify_client import SpotifyClient


def process_tracks(tracks: List[Dict[str, Any]], 
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Process a list of tracks with optional limit.
    
    Args:
        tracks: List of track dictionaries to process
        limit: Maximum number of tracks to return (None for all)
        
    Returns:
        Processed list of tracks
        
    Raises:
        ValueError: If tracks list is empty
    """
    if not tracks:
        raise ValueError("Tracks list cannot be empty")
    
    # Process tracks...
    return processed_tracks
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_spotify_client.py

# Run with verbose output
pytest -v
```

### Writing Tests
- **Test files**: Place in `tests/` directory
- **Naming**: Use `test_*.py` naming convention
- **Coverage**: Aim for >90% code coverage
- **Mocking**: Mock external API calls and file operations

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from app.spotify_client import SpotifyClient


class TestSpotifyClient:
    """Test cases for SpotifyClient class."""
    
    def test_initialization_success(self):
        """Test successful client initialization."""
        with patch.dict('os.environ', {
            'SPOTIFY_CLIENT_ID': 'test_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret',
            'SPOTIFY_REFRESH_TOKEN': 'test_token',
            'SPOTIFY_USER_ID': 'test_user'
        }):
            client = SpotifyClient()
            assert client.client_id == 'test_id'
    
    def test_initialization_missing_env_vars(self):
        """Test initialization fails with missing environment variables."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Missing required"):
                SpotifyClient()
```

## 🔧 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code following the style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Pre-commit Checks
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/

# Run tests
pytest
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add new feature description

- Detailed change description
- Any breaking changes
- Related issue number"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

## 📋 Pull Request Guidelines

### PR Title Format
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### PR Description
- **Summary**: Brief description of changes
- **Changes**: Detailed list of changes
- **Testing**: How to test the changes
- **Breaking Changes**: Any breaking changes
- **Related Issues**: Link to related issues

### Example PR Description
```markdown
## Summary
Adds support for custom genre weights in track selection.

## Changes
- New `custom_genre_weights` configuration option
- Updated track scoring algorithm to use custom weights
- Added validation for weight values
- Updated documentation

## Testing
1. Set custom genre weights in config
2. Run track selection
3. Verify weights are applied correctly

## Breaking Changes
None

## Related Issues
Closes #123
```

## 🐛 Bug Reports

### Bug Report Template
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 14.0]
- Python Version: [e.g., 3.11.5]
- Bot Version: [e.g., 2.0.0]

## Additional Information
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear description of the requested feature

## Use Case
Why this feature would be useful

## Proposed Implementation
How you think it could be implemented

## Alternatives Considered
Other approaches you've considered

## Additional Information
Any other relevant information
```

## 📚 Documentation

### Updating Documentation
- **README.md**: Update for user-facing changes
- **docs/**: Update technical documentation
- **CHANGELOG.md**: Add entries for all changes
- **Inline docs**: Update docstrings and comments

### Documentation Standards
- Use clear, concise language
- Include examples where helpful
- Keep documentation up to date with code changes
- Use consistent formatting and structure

## 🤝 Code Review

### Review Process
1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Address feedback** and make requested changes
4. **Approval** from at least one maintainer

### Review Guidelines
- **Be constructive** and respectful
- **Focus on code quality** and functionality
- **Suggest improvements** when possible
- **Ask questions** if something is unclear

## 📞 Getting Help

### Questions and Discussion
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Ask questions in PR reviews

### Contact Maintainers
- **GitHub**: @yourusername
- **Email**: [Contact through GitHub]

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Spotify App Agent Template! 🎵
