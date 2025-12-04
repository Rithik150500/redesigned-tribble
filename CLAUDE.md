# CLAUDE.md - AI Assistant Guide

This document provides context for AI assistants (like Claude) working with this codebase.

## Project Overview

This is a **Legal Risk Analysis System** - a React-based frontend application that provides a real-time interface for AI-powered legal document analysis. The system connects to a backend agent service via WebSocket and displays analysis progress, document content, and generated files in a three-panel layout.

## Architecture

### Frontend Structure

```
src/
├── App.js                    # Main application component with WebSocket orchestration
├── components/
│   ├── DocumentPanel.js      # Left panel: Legal document viewer (PDF support)
│   ├── WorkflowPanel.js      # Center panel: Agent messages, todos, approvals
│   ├── FilePanel.js          # Right panel: Agent workspace file browser
│   └── *.css                 # Component styles
└── services/
    └── websocket.js          # WebSocket connection manager
```

### Key Technologies

- **React 18.2.0**: UI framework
- **react-split-pane**: Resizable three-panel layout
- **@monaco-editor/react**: Code/text editor with syntax highlighting
- **@react-pdf-viewer**: PDF document viewing
- **WebSocket**: Real-time bidirectional communication with backend

### Data Flow

1. **Session Initialization**: App creates a session with backend API (`POST /api/sessions`)
2. **WebSocket Connection**: Establishes persistent connection to `ws://localhost:8000/ws/{sessionId}`
3. **Document Loading**: Fetches available documents from `GET /api/documents`
4. **Analysis Workflow**:
   - User submits analysis request via WorkflowPanel
   - Backend agent processes request, sends progress updates via WebSocket
   - Agent actions requiring approval are displayed to user
   - User approves/rejects, backend continues processing
   - Generated files appear in FilePanel

### WebSocket Message Types

The system handles these message types (see `src/App.js:108-171`):

- `connected`: WebSocket connection established
- `analysis_started`: Agent begins analysis
- `agent_message`: Progress update from agent
- `approval_required`: Agent needs user approval for an action
- `approval_processed`: Approval decision processed
- `analysis_complete`: Analysis finished
- `error`: Error occurred

## Component Responsibilities

### App.js (Main Orchestrator)
- Manages WebSocket connection lifecycle
- Maintains global state (documents, messages, todos, files, approvals)
- Coordinates three-panel layout
- Handles layout transitions based on user interactions
- Routes WebSocket messages to appropriate handlers

### DocumentPanel.js
- Displays list of legal documents
- PDF viewer with page navigation
- Highlights documents involved in approval actions
- Expands when document is selected

### WorkflowPanel.js
- Shows agent conversation and progress
- Displays todo list
- Handles approval requests (user can approve, edit, or reject)
- Input area for starting new analysis
- Connection status indicator

### FilePanel.js
- File tree browser for agent's workspace
- Monaco Editor for viewing file contents with syntax highlighting
- Detects file types (markdown, python, javascript, etc.)
- Highlights files involved in approval actions
- Expands when file is selected

### websocket.js
- Encapsulates WebSocket connection logic
- Automatic reconnection with exponential backoff (max 5 attempts)
- Event-based handler registration (`.on(type, handler)`)
- Message serialization/deserialization

## Dynamic Layout System

The app uses three layout modes (see `src/App.js:237-246`):

- **default**: Balanced view - 20% | 60% | 20%
- **document-view**: Focus on document - 40% | 40% | 20%
- **file-edit**: Focus on file - 20% | 40% | 40%

Panels automatically expand/contract based on user actions.

## Common Development Tasks

### Adding a New Message Type

1. Add handler in `src/App.js` (follow pattern of existing handlers)
2. Register handler in WebSocket setup (`ws.on(...)`)
3. Update appropriate panel component to handle the new data

### Modifying the Approval System

Approval logic is spread across:
- `App.js`: Receives `approval_required`, stores in state
- `WorkflowPanel.js`: Displays approval UI, sends decisions
- `DocumentPanel.js` & `FilePanel.js`: Highlight affected items

### Adding File Type Support

Update `detectLanguage()` in `src/components/FilePanel.js:107-119` to add new file extensions and Monaco language modes.

## Backend API Expectations

The frontend expects these backend endpoints:

- `POST /api/sessions`: Create new session, returns `{session_id: string}`
- `GET /api/documents`: List documents, returns `{documents: Array}`
- `WS /ws/{sessionId}`: WebSocket endpoint for real-time communication

## State Management

Currently uses React useState hooks for all state. Key state variables in App.js:

- `sessionId`: Current session identifier
- `websocket`: WebSocket connection instance
- `connectionStatus`: 'disconnected' | 'connected'
- `selectedDocument`: Currently viewed document
- `selectedFile`: Currently viewed file
- `layoutMode`: Current panel layout configuration
- `documents`: Available legal documents
- `agentMessages`: Conversation history
- `todos`: Task list from agent
- `files`: Files in agent workspace
- `approvalRequest`: Pending approval (if any)

## Development Notes

### Browser Mode vs Viewer Mode

FilePanel has two modes:
- **Browser**: Shows file tree with all files
- **Viewer**: Shows single file content with Monaco Editor

The mode switches automatically based on whether a file is selected.

### Approval Context

When an approval is required, `approvalContext` is passed to panels to highlight relevant items. Each panel checks if the approval action relates to its domain:
- DocumentPanel: Checks for `get_documents`, `get_page_text` tools
- FilePanel: Checks for `write_file`, `edit_file` tools

### Connection Resilience

The WebSocket service automatically reconnects if the connection drops, with exponential backoff (2s, 4s, 8s, 16s, 32s). After 5 failed attempts, it gives up and notifies handlers.

## Common Issues & Solutions

### "WebSocket not connected" errors
- Check that backend is running on `localhost:8000`
- Verify session was created successfully
- Check browser console for connection errors

### Layout not updating
- Verify `layoutMode` state is changing
- Check that `getPanelSizes()` is being called
- Ensure SplitPane `defaultSize` is updating

### Files not appearing
- Check `files` array in state
- Verify `buildFileTree()` is processing paths correctly
- Ensure WebSocket is sending file updates

### Approval requests not displaying
- Verify `approvalRequest` state is set
- Check WorkflowPanel is receiving the prop
- Ensure approval message type is registered in WebSocket handlers

## Testing Considerations

When testing, note:
- WebSocket connection requires backend running
- Document loading requires API server
- File operations depend on agent workspace state
- Approval flow requires agent to request approval

## Security Notes

Current implementation connects to `localhost:8000` hardcoded. For production:
- Use environment variables for API/WebSocket URLs
- Implement authentication for session creation
- Add authorization for document access
- Sanitize file paths to prevent directory traversal
- Validate WebSocket messages before processing

## Future Enhancement Ideas

- State management with Redux/Zustand for better scalability
- Persistent session storage (localStorage)
- Download files from agent workspace
- Edit files and send changes to agent
- Export analysis results
- Multi-session support
- Dark mode
- Keyboard shortcuts
- Search within documents and files
