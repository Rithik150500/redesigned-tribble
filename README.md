# Legal Risk Analysis System

A real-time web application for AI-powered legal document analysis. This frontend provides an interactive interface for conducting legal risk assessments with an AI agent backend.

## Features

- **Three-Panel Layout**: Intuitive interface with separate panels for documents, workflow, and files
- **Real-Time Communication**: WebSocket-based connection for instant updates from the analysis agent
- **PDF Document Viewer**: View and navigate legal documents with integrated PDF support
- **Code Editor**: Syntax-highlighted file viewer for analysis outputs (Markdown, Python, JSON, etc.)
- **Approval Workflow**: Review and approve/reject agent actions before they execute
- **Dynamic Layout**: Panels automatically expand/contract based on what you're viewing
- **Todo Tracking**: Visual task list showing agent progress

## Screenshots

### Main Interface
The application features a three-panel layout:
- **Left Panel**: Browse and view legal documents (PDF support)
- **Center Panel**: Agent conversation, todos, and approval requests
- **Right Panel**: Agent workspace with generated analysis files

## Getting Started

### Prerequisites

- Node.js 14+ and npm/yarn
- Backend API server running on `localhost:8000` (not included in this repository)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/legal-analysis-frontend.git
cd legal-analysis-frontend

# Install dependencies
npm install
```

### Running the Application

```bash
# Start the development server
npm start
```

The application will open at `http://localhost:3000`.

### Building for Production

```bash
# Create optimized production build
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Architecture

### Technology Stack

- **React 18.2.0**: Modern UI framework with hooks
- **WebSocket**: Real-time bidirectional communication
- **Monaco Editor**: VS Code-powered code editor component
- **React PDF Viewer**: Document viewing with page navigation
- **Split Pane**: Resizable panel layout

### Component Structure

```
src/
├── App.js                      # Main application & WebSocket orchestration
├── components/
│   ├── DocumentPanel.js        # Legal document viewer
│   ├── WorkflowPanel.js        # Agent conversation & approvals
│   ├── FilePanel.js            # File browser & editor
│   └── *.css                   # Component styles
└── services/
    └── websocket.js            # WebSocket connection manager
```

### Data Flow

1. App creates a new session with the backend API
2. WebSocket connection established to receive real-time updates
3. User submits analysis request
4. Agent processes request and sends progress updates
5. User reviews and approves/rejects agent actions
6. Agent generates analysis files visible in the file panel
7. Analysis completes with results

## Usage

### Starting an Analysis

1. Ensure the backend server is running
2. Open the application (automatically connects via WebSocket)
3. Type your analysis request in the center panel input
4. Press Enter or click Submit

Example requests:
- "Analyze all employment agreements for IP assignment clauses"
- "Review the NDA for potential liability issues"
- "Generate a risk summary for all documents"

### Viewing Documents

1. Click on any document in the left panel
2. The panel expands to show the PDF viewer
3. Navigate pages using the built-in controls
4. Click "Back to Documents" to return to the list

### Reviewing Agent Actions

When the agent needs approval:
1. An approval request appears in the center panel
2. Review the proposed action and context
3. Choose to:
   - **Approve**: Let the agent proceed
   - **Edit**: Modify the action parameters
   - **Reject**: Block the action

### Viewing Generated Files

1. Files appear in the right panel as the agent creates them
2. Click any file to view its contents
3. Syntax highlighting automatically applied based on file type
4. Click "Back to Files" to return to the file tree

## Configuration

### Backend URL

The application connects to `http://localhost:8000` by default. To change this:

Edit `src/App.js` and `src/services/websocket.js` to update the API and WebSocket URLs.

For production, use environment variables:

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
```

## API Requirements

The frontend expects the backend to provide:

### REST Endpoints

- `POST /api/sessions`
  - Creates a new analysis session
  - Returns: `{session_id: string}`

- `GET /api/documents`
  - Lists available legal documents
  - Returns: `{documents: [{id, title, path, ...}, ...]}`

### WebSocket Endpoint

- `WS /ws/{sessionId}`
  - Real-time bidirectional communication
  - Message types: `analysis_started`, `agent_message`, `approval_required`, `analysis_complete`, etc.

## Development

### Project Structure

- `src/App.js`: Main application component with state management and WebSocket orchestration
- `src/components/DocumentPanel.js`: Document list and PDF viewer
- `src/components/WorkflowPanel.js`: Agent messages, todos, and approval interface
- `src/components/FilePanel.js`: File tree browser and Monaco editor
- `src/services/websocket.js`: WebSocket connection with auto-reconnect

### Adding New Features

#### Adding a New Message Type

1. Add handler in `App.js`:
```javascript
const handleNewMessage = useCallback((data) => {
  // Handle the message
}, []);
```

2. Register in WebSocket setup:
```javascript
ws.on('new_message_type', handleNewMessage);
```

3. Update relevant panel component to display the data

#### Supporting New File Types

Update `detectLanguage()` in `FilePanel.js`:

```javascript
const languageMap = {
  'md': 'markdown',
  'py': 'python',
  'rs': 'rust',  // Add new type
  // ...
};
```

### Running Tests

```bash
npm test
```

### Code Style

This project follows standard React conventions:
- Functional components with hooks
- Props destructuring
- Callback memoization with `useCallback`
- Effect dependencies properly declared

## Troubleshooting

### WebSocket Connection Fails

**Problem**: "WebSocket not connected" or connection keeps dropping

**Solutions**:
- Verify backend server is running on the expected port
- Check browser console for detailed error messages
- Ensure no firewall is blocking WebSocket connections
- Try disabling browser extensions that might interfere

### Documents Not Loading

**Problem**: Document list is empty or won't load

**Solutions**:
- Check that `GET /api/documents` endpoint is accessible
- Verify backend has documents configured
- Check browser network tab for failed requests
- Ensure CORS is properly configured on backend

### Files Not Appearing

**Problem**: Agent workspace shows "No files yet"

**Solutions**:
- Verify the agent has started processing
- Check that file updates are being sent via WebSocket
- Confirm the `files` array is being populated in state
- Check browser console for JavaScript errors

### Approval Requests Not Displaying

**Problem**: Approval requests don't show up in UI

**Solutions**:
- Verify WebSocket is connected
- Check that `approval_required` messages are being received
- Ensure `approvalRequest` state is being set
- Inspect WorkflowPanel component props

## Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
EXPOSE 3000
```

Build and run:
```bash
docker build -t legal-analysis-frontend .
docker run -p 3000:3000 legal-analysis-frontend
```

### Environment Variables

For production deployment, configure:
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_WS_URL`: WebSocket server URL

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write clean, documented code
- Follow existing code style and patterns
- Test WebSocket reconnection scenarios
- Ensure responsive layout works on different screen sizes
- Add comments for complex logic

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [React](https://reactjs.org/)
- Code editing powered by [Monaco Editor](https://microsoft.github.io/monaco-editor/)
- PDF viewing via [React PDF Viewer](https://react-pdf-viewer.dev/)
- Layout management with [React Split Pane](https://github.com/tomkp/react-split-pane)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

- [ ] Authentication and user management
- [ ] Multi-session support
- [ ] File editing and upload
- [ ] Export analysis results
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Search functionality
- [ ] Document annotations
- [ ] Collaborative analysis
- [ ] Mobile responsive design

## Related Projects

This is the frontend component of the Legal Risk Analysis System. The backend agent service is maintained separately.
