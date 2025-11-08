# Contributing to Scripture Sync

Thank you for your interest in contributing to Scripture Sync! This document provides guidelines and instructions for contributing.

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Our Responsibilities

Project maintainers are responsible for clarifying standards of acceptable behavior and will take appropriate action in response to any unacceptable behavior.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Collect relevant information (logs, screenshots, system info)
3. Verify the issue on the latest version

When creating a bug report, include:
- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots if applicable
- System information (OS, Docker version, etc.)
- Relevant logs

Example:
```markdown
**Bug Description:**
WebSocket disconnects after 30 seconds

**Steps to Reproduce:**
1. Start services with `docker-compose up -d`
2. Open dashboard at http://localhost:3000
3. Wait 30 seconds
4. Connection status shows "Disconnected"

**Expected Behavior:**
WebSocket should remain connected

**System Info:**
- OS: Ubuntu 22.04
- Docker: 24.0.5
- Browser: Chrome 119

**Logs:**
[Attach relevant logs]
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear, descriptive title
- Provide detailed description of the proposed enhancement
- Explain why this enhancement would be useful
- List any alternatives you've considered
- Include mockups or examples if applicable

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

## Development Setup

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/scripture-sync.git
cd scripture-sync

# Run development setup
./scripts/dev-setup.sh

# Backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend
npm start
```

### Docker Development

```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Coding Standards

### Python (Backend)

**Style Guide:** PEP 8

```python
# Use type hints
def process_verse(text: str, min_score: float = 0.6) -> Optional[Verse]:
    pass

# Docstrings for all public functions
def match_verse(query: str) -> Dict[str, Any]:
    """
    Match a query string to Bible verses.
    
    Args:
        query: The search query
        
    Returns:
        Dictionary containing matched verse and metadata
    """
    pass

# Use async/await for I/O operations
async def get_verses() -> List[Verse]:
    async with session() as db:
        result = await db.execute(query)
        return result.all()
```

**Formatting:**
```bash
# Install black and flake8
pip install black flake8

# Format code
black app/

# Check style
flake8 app/
```

### JavaScript/React (Frontend)

**Style Guide:** Airbnb JavaScript Style Guide

```javascript
// Use functional components with hooks
function Dashboard() {
  const [verses, setVerses] = useState([]);
  
  useEffect(() => {
    fetchVerses();
  }, []);
  
  return <div>{/* ... */}</div>;
}

// PropTypes for component props
Component.propTypes = {
  verse: PropTypes.object.isRequired,
  onSelect: PropTypes.func
};

// Clear, descriptive names
const handleVerseSelection = (verseId) => {
  // ...
};
```

**Formatting:**
```bash
# Install prettier and eslint
npm install --save-dev prettier eslint

# Format code
npm run format

# Lint
npm run lint
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build/tooling changes

**Examples:**
```
feat(matcher): add semantic search with FAISS

Implement semantic similarity search using sentence transformers
and FAISS for improved verse matching accuracy.

Closes #123
```

```
fix(websocket): prevent disconnection after 30s

Added keep-alive ping messages to maintain WebSocket connection.

Fixes #456
```

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_verse_matcher.py

# Run with coverage
pytest --cov=app tests/
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage
```

### Writing Tests

**Backend:**
```python
import pytest
from app.verse_matcher import VerseMatcher

@pytest.mark.asyncio
async def test_verse_matching():
    matcher = VerseMatcher()
    result = await matcher.find_best_match("test query", session)
    assert result is not None
```

**Frontend:**
```javascript
import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';

test('renders dashboard', () => {
  render(<Dashboard />);
  const heading = screen.getByText(/Scripture Sync/i);
  expect(heading).toBeInTheDocument();
});
```

## Documentation

### Code Documentation

- Add docstrings to all public functions
- Comment complex logic
- Update README when adding features
- Keep ARCHITECTURE.md current

### API Documentation

FastAPI auto-generates docs at `/docs`:
```python
@app.get("/verses/", tags=["Verses"])
async def list_verses(
    version: str = Query(None, description="Bible version (KJV or NIV)"),
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """
    List Bible verses with optional filtering.
    
    - **version**: Filter by Bible version
    - **skip**: Number of verses to skip (pagination)
    - **limit**: Maximum verses to return
    """
    pass
```

## Project Structure

```
scripture-sync/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── database.py  # Database models
│   │   ├── verse_matcher.py  # Matching logic
│   │   └── ...
│   ├── tests/           # Backend tests
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── ...
│   └── package.json
├── scripts/             # Utility scripts
├── data/                # Database and data files
└── docs/                # Documentation
```

## Feature Development Workflow

1. **Plan the feature**
   - Open an issue for discussion
   - Get feedback from maintainers
   - Define requirements and scope

2. **Design the solution**
   - Create technical design document
   - Consider edge cases
   - Think about performance

3. **Implement**
   - Write code following style guidelines
   - Add tests as you go
   - Keep commits atomic and well-described

4. **Test thoroughly**
   - Unit tests for logic
   - Integration tests for APIs
   - Manual testing in UI
   - Test edge cases

5. **Document**
   - Update README if needed
   - Add inline documentation
   - Update ARCHITECTURE.md for major changes

6. **Submit PR**
   - Reference related issue
   - Describe changes clearly
   - Add screenshots for UI changes
   - Request review

## Review Process

### For Contributors

- Respond to review comments promptly
- Make requested changes
- Ask questions if unclear
- Be patient and respectful

### For Reviewers

- Review code for correctness, style, and performance
- Test the changes locally
- Provide constructive feedback
- Approve when satisfied

## Release Process

1. Version bump in appropriate files
2. Update CHANGELOG.md
3. Create release tag
4. Build and push Docker images
5. Create GitHub release with notes

## Areas for Contribution

### High Priority
- [ ] Full Bible data import (all translations)
- [ ] GPU acceleration for Whisper
- [ ] Mobile app development
- [ ] Performance optimization
- [ ] Comprehensive test coverage

### Medium Priority
- [ ] Additional Bible translations
- [ ] Multi-language UI support
- [ ] Theme customization
- [ ] Verse history and favorites
- [ ] Advanced search filters

### Low Priority
- [ ] Browser extensions
- [ ] Keyboard shortcuts
- [ ] Export functionality
- [ ] Statistics dashboard
- [ ] Voice commands

### Documentation
- [ ] Video tutorials
- [ ] More examples
- [ ] API reference
- [ ] Deployment guides
- [ ] Troubleshooting cases

## Questions?

- Check existing documentation
- Search closed issues
- Ask in discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to Scripture Sync! 🙏📖
