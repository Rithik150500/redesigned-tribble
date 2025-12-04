# Test Suite Documentation

Comprehensive test coverage for the Legal Risk Analysis System, organized by architectural layers.

## Test Organization

```
tests/
├── test_layer1_document_processing.py  # Layer 1: Document Processing & Database
├── test_layer2_mcp_server.py          # Layer 2: MCP Document Analysis Server
├── test_layer3_agent_system.py        # Layer 3: Deep Agent Orchestration
├── test_layer4_web_interface.py       # Layer 4: Web Interface (REST + WebSocket)
├── test_integration.py                # Cross-layer integration tests
└── README.md                          # This file
```

## Running Tests

### Run All Tests

```bash
cd backend
source venv/bin/activate
pytest tests/
```

### Run Tests by Layer

```bash
# Layer 1: Document Processing & Database
pytest tests/test_layer1_document_processing.py -v

# Layer 2: MCP Server
pytest tests/test_layer2_mcp_server.py -v

# Layer 3: Agent System
pytest tests/test_layer3_agent_system.py -v

# Layer 4: Web Interface
pytest tests/test_layer4_web_interface.py -v

# Integration Tests
pytest tests/test_integration.py -v
```

### Run Specific Test Classes

```bash
# Run only database schema tests
pytest tests/test_layer1_document_processing.py::TestDatabaseSchema -v

# Run only MCP tool tests
pytest tests/test_layer2_mcp_server.py::TestGetDocumentsTool -v
```

### Run Tests with Markers

```bash
# Run only layer1 tests
pytest -m layer1

# Run integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"
```

## Test Coverage by Layer

### Layer 1: Document Processing & Database (68 tests)

**Database Tests** (`TestDatabaseSchema`, `TestDocumentOperations`, `TestPageOperations`)
- ✓ Schema creation and validation
- ✓ Document CRUD operations
- ✓ Page CRUD operations
- ✓ Foreign key constraints
- ✓ Unique constraints
- ✓ Index creation

**Document Processor Tests** (`TestDocumentProcessor`, `TestDocumentProcessingIntegration`)
- ✓ PDF text extraction
- ✓ Page image rendering
- ✓ AI summarization (mocked)
- ✓ Document-level analysis
- ✓ Significance detection
- ✓ File hash calculation
- ✓ Error handling

**Edge Cases** (`TestEdgeCases`)
- ✓ Empty page text
- ✓ Large page images
- ✓ Unicode characters
- ✓ Malformed PDFs

### Layer 2: MCP Document Analysis Server (42 tests)

**Server Setup** (`TestMCPServerSetup`)
- ✓ Server initialization
- ✓ Tool registration
- ✓ Database connectivity

**MCP Tools** (`TestListDocumentsTool`, `TestGetDocumentsTool`, `TestGetPageTextTool`, `TestGetPageImageTool`)
- ✓ list_documents: Returns formatted document list
- ✓ get_documents: Provides layered access (summaries + significant pages)
- ✓ get_page_text: Returns specific page content
- ✓ get_page_image: Returns page images with usage warnings
- ✓ All tools handle errors gracefully
- ✓ All tools provide helpful error messages

**Layered Access** (`TestLayeredAccess`)
- ✓ Token-efficient data transfer
- ✓ Progressive detail revelation
- ✓ Workflow optimization

**Performance** (`TestPerformance`)
- ✓ Large document lists (50+ documents)
- ✓ Documents with many pages (100+ pages)
- ✓ Concurrent access

### Layer 3: Deep Agent Orchestration (35 tests)

**Agent Creation** (`TestAgentCreation`, `TestSubagents`)
- ✓ Main agent initialization
- ✓ Checkpointer configuration
- ✓ Memory store setup
- ✓ Subagent registration
- ✓ API key validation

**Approval Workflow** (`TestApprovalWorkflow`)
- ✓ Agent pauses for approval
- ✓ Interrupt handling
- ✓ Approval context building
- ✓ Resume after approval

**MCP Integration** (`TestMCPIntegration`)
- ✓ MCP server startup
- ✓ Tool configuration
- ✓ Agent access to documents

**State Management** (`TestStateManagement`)
- ✓ State persistence
- ✓ Checkpointing
- ✓ Filesystem backend

**Command-Line Flow** (`TestCommandLineApproval`)
- ✓ CLI approval simulation
- ✓ Context display
- ✓ Decision handling

### Layer 4: Web Interface (52 tests)

**REST API** (`TestRESTEndpoints`)
- ✓ GET /api/documents
- ✓ GET /api/documents/{id}
- ✓ GET /api/documents/{id}/pdf
- ✓ GET /api/documents/{id}/page/{num}/image
- ✓ POST /api/sessions
- ✓ DELETE /api/sessions/{id}
- ✓ Error handling (404, 400, etc.)

**WebSocket** (`TestWebSocketConnection`, `TestAnalysisWorkflow`)
- ✓ Connection establishment
- ✓ Ping/pong keepalive
- ✓ Message routing
- ✓ start_analysis handling
- ✓ approval_required messages
- ✓ approval_decision processing
- ✓ Real-time updates

**Session Management** (`TestSessionManagement`)
- ✓ Session creation
- ✓ Multiple sessions
- ✓ Session persistence
- ✓ Session cleanup

**Security** (`TestCORSAndSecurity`)
- ✓ CORS configuration
- ✓ Content-Type handling
- ✓ Input validation

### Integration Tests (28 tests)

**Cross-Layer Integration**
- ✓ Layer 1 → Layer 2: Document processing to MCP access
- ✓ Layer 2 → Layer 3: MCP tools to agent invocation
- ✓ Layer 3 → Layer 4: Agent execution to web interface
- ✓ Full pipeline: PDF → Database → MCP → Agent → Web

**Performance Integration**
- ✓ Multiple documents through pipeline
- ✓ Concurrent operations
- ✓ Resource management

**Error Recovery**
- ✓ Database error propagation
- ✓ Agent error handling
- ✓ Graceful degradation

## Test Statistics

**Total Tests**: 225+
**Total Test Files**: 5
**Coverage Target**: 80%+

### By Category
- Unit Tests: ~150
- Integration Tests: ~40
- API Tests: ~25
- Performance Tests: ~10

### By Layer
- Layer 1: 68 tests
- Layer 2: 42 tests
- Layer 3: 35 tests
- Layer 4: 52 tests
- Integration: 28 tests

## Mocking Strategy

### What We Mock

1. **External APIs**: Anthropic API calls are mocked to avoid costs and rate limits
2. **PDF Operations**: pdf2image and pypdf are mocked for speed
3. **File System**: Temporary files used, cleaned up after tests
4. **Database**: Temporary SQLite databases per test

### What We Don't Mock

1. **Database Operations**: Real SQLite operations (with temp DB)
2. **FastAPI**: Real FastAPI application (with TestClient)
3. **Business Logic**: All business logic runs without mocking

## Fixtures

### Common Fixtures

- `temp_db`: Temporary database for testing
- `mock_anthropic_client`: Mocked Anthropic API
- `populated_db`: Database with test data
- `client`: FastAPI TestClient
- `mock_agent`: Mocked agent for testing

### Fixture Scope

- Most fixtures: `function` scope (new instance per test)
- Database fixtures: `function` scope (isolated tests)
- Client fixtures: `function` scope (fresh client per test)

## Writing New Tests

### Test Structure

```python
class TestFeature:
    """Test specific feature."""

    def test_feature_works(self, fixture_name):
        """Test that feature works correctly."""
        # Arrange
        # ... setup ...

        # Act
        # ... execute ...

        # Assert
        assert result is not None
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use descriptive names: `test_get_documents_returns_page_summaries`

### Assertions

Use descriptive assertions:
```python
# Good
assert doc['filename'] == "expected.pdf"
assert "Error" in result

# Avoid
assert doc
assert result
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Every push to main branch
- Every pull request
- Scheduled daily runs

### CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

## Test Data

### Sample Documents

- `tests/fixtures/`: Sample PDFs for testing
- Created dynamically in tests when needed
- Cleaned up after test completion

### Database Fixtures

- Temporary SQLite databases
- Populated with realistic test data
- Isolated per test

## Debugging Tests

### Run with More Detail

```bash
# Show print statements
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ -v -l

# Stop on first failure
pytest tests/ -v -x

# Run specific test with full output
pytest tests/test_layer1_document_processing.py::TestDatabaseSchema::test_database_initialization -vv -s
```

### Debugging Failed Tests

1. Check error message and traceback
2. Run test in isolation: `pytest path/to/test::test_name -v`
3. Add `print()` statements or use `pytest -s`
4. Use `pytest --pdb` to drop into debugger on failure

## Performance Testing

### Running Performance Tests

```bash
# Run only performance tests
pytest tests/ -k "performance" -v

# With timing
pytest tests/ --durations=10
```

### Performance Benchmarks

- Document processing: < 5s per page
- MCP tool calls: < 100ms
- API endpoints: < 200ms
- WebSocket messages: < 50ms

## Best Practices

### DO

✓ Write tests before fixing bugs
✓ Test edge cases and error conditions
✓ Use descriptive test names
✓ Keep tests independent
✓ Mock external services
✓ Clean up resources (files, connections)
✓ Test both success and failure paths

### DON'T

✗ Depend on test execution order
✗ Share state between tests
✗ Use real API keys in tests
✗ Commit temporary test files
✗ Skip error handling tests
✗ Test implementation details
✗ Write tests that are hard to understand

## Coverage Reports

### Generate Coverage Report

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Goals

- Overall: 80%+
- Critical paths: 90%+
- Error handling: 100%

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Ensure tests can find modules
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

**Database Locked**
- Tests use temporary databases
- Each test gets fresh database
- If issues persist, check file permissions

**Async Test Failures**
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Check `pytest.ini` has `asyncio_mode = auto`

**Mock Not Working**
- Check patch path is correct
- Ensure patch is applied before import
- Use `with patch()` context manager

## Contributing Tests

When contributing new features:

1. Add tests in appropriate layer file
2. Ensure tests pass: `pytest tests/ -v`
3. Check coverage: `pytest tests/ --cov`
4. Update this README if needed
5. Submit with pull request

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
