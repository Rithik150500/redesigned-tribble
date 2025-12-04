// src/App.js
/**
 * Main application component for Legal Risk Analysis system.
 * 
 * This component:
 * - Manages the WebSocket connection
 * - Coordinates the three-panel layout
 * - Maintains global state (selected document, current files, etc.)
 * - Handles layout transitions (expanding panels when viewing documents)
 */

import React, { useState, useEffect, useCallback } from 'react';
import SplitPane from 'react-split-pane';
import './App.css';

import DocumentPanel from './components/DocumentPanel';
import WorkflowPanel from './components/WorkflowPanel';
import FilePanel from './components/FilePanel';
import AgentWebSocket from './services/websocket';

function App() {
  // Connection and session state
  const [sessionId, setSessionId] = useState(null);
  const [websocket, setWebsocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // UI state
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [layoutMode, setLayoutMode] = useState('default'); // default, document-view, file-edit

  // Analysis state
  const [documents, setDocuments] = useState([]);
  const [agentMessages, setAgentMessages] = useState([]);
  const [todos, setTodos] = useState([]);
  const [files, setFiles] = useState([]);
  const [approvalRequest, setApprovalRequest] = useState(null);

  /**
   * Initialize the session and WebSocket connection.
   * 
   * This runs once when the app loads. We create a new analysis session
   * on the backend and connect via WebSocket.
   */
  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Create a new session
        const response = await fetch('http://localhost:8000/api/sessions', {
          method: 'POST'
        });
        const data = await response.json();
        const newSessionId = data.session_id;
        
        setSessionId(newSessionId);
        
        // Create WebSocket connection
        const ws = new AgentWebSocket(newSessionId);
        
        // Register message handlers
        ws.on('connected', handleConnected);
        ws.on('analysis_started', handleAnalysisStarted);
        ws.on('agent_message', handleAgentMessage);
        ws.on('approval_required', handleApprovalRequired);
        ws.on('approval_processed', handleApprovalProcessed);
        ws.on('analysis_complete', handleAnalysisComplete);
        ws.on('error', handleError);
        
        // Connect
        ws.connect();
        setWebsocket(ws);
        
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };

    initializeSession();

    // Cleanup on unmount
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []); // Empty dependency array means this runs once on mount

  /**
   * Load documents from the backend.
   * 
   * This populates the document list in the left panel.
   */
  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/documents');
        const data = await response.json();
        setDocuments(data.documents);
      } catch (error) {
        console.error('Failed to load documents:', error);
      }
    };

    loadDocuments();
  }, []);

  // WebSocket message handlers

  const handleConnected = useCallback((data) => {
    console.log('Connected to analysis session:', data.sessionId);
    setConnectionStatus('connected');
  }, []);

  const handleAnalysisStarted = useCallback((data) => {
    console.log('Analysis started:', data.message);
    setAgentMessages(prev => [...prev, {
      type: 'system',
      content: data.message,
      timestamp: new Date()
    }]);
  }, []);

  const handleAgentMessage = useCallback((data) => {
    console.log('Agent message:', data);
    setAgentMessages(prev => [...prev, {
      type: 'agent',
      content: data.content,
      timestamp: new Date()
    }]);
  }, []);

  const handleApprovalRequired = useCallback((data) => {
    console.log('Approval required:', data);
    setApprovalRequest(data);
    
    // Add system message about approval
    setAgentMessages(prev => [...prev, {
      type: 'system',
      content: 'Waiting for your approval...',
      timestamp: new Date()
    }]);
  }, []);

  const handleApprovalProcessed = useCallback((data) => {
    console.log('Approval processed:', data.message);
    setApprovalRequest(null);
    
    setAgentMessages(prev => [...prev, {
      type: 'system',
      content: data.message,
      timestamp: new Date()
    }]);
  }, []);

  const handleAnalysisComplete = useCallback((data) => {
    console.log('Analysis complete:', data);
    setAgentMessages(prev => [...prev, {
      type: 'system',
      content: data.message,
      timestamp: new Date()
    }]);
  }, []);

  const handleError = useCallback((data) => {
    console.error('Agent error:', data);
    setAgentMessages(prev => [...prev, {
      type: 'error',
      content: data.message || 'An error occurred',
      timestamp: new Date()
    }]);
  }, []);

  /**
   * Start a new analysis.
   * 
   * This is called when the user types their analysis request and hits submit.
   */
  const startAnalysis = useCallback((message) => {
    if (!websocket) {
      console.error('WebSocket not connected');
      return;
    }

    websocket.send({
      type: 'start_analysis',
      message: message
    });
  }, [websocket]);

  /**
   * Send approval decisions to the backend.
   * 
   * This is called when the user approves, edits, or rejects agent actions.
   */
  const sendApprovalDecisions = useCallback((decisions) => {
    if (!websocket) {
      console.error('WebSocket not connected');
      return;
    }

    websocket.send({
      type: 'approval_decision',
      decisions: decisions
    });
  }, [websocket]);

  /**
   * Handle document selection.
   * 
   * When the user clicks a document in the left panel, we:
   * 1. Set it as selected
   * 2. Switch to document-view layout mode (left panel expands)
   * 3. Load document details
   */
  const handleDocumentSelect = useCallback(async (doc) => {
    setSelectedDocument(doc);
    setLayoutMode('document-view');
  }, []);

  /**
   * Handle file selection.
   * 
   * When the user clicks a file in the right panel, we:
   * 1. Set it as selected
   * 2. Switch to file-edit layout mode (right panel expands)
   */
  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setLayoutMode('file-edit');
  }, []);

  /**
   * Calculate panel sizes based on layout mode.
   * 
   * This creates the dynamic layout that adapts to what the user is viewing.
   */
  const getPanelSizes = () => {
    switch (layoutMode) {
      case 'document-view':
        return { left: '40%', center: '40%', right: '20%' };
      case 'file-edit':
        return { left: '20%', center: '40%', right: '40%' };
      default:
        return { left: '20%', center: '60%', right: '20%' };
    }
  };

  const sizes = getPanelSizes();

  return (
    <div className="App">
      {/* Header */}
      <div className="app-header">
        <h1>Legal Risk Analysis System</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus}`}></span>
          {connectionStatus === 'connected' ? 'Connected' : 'Connecting...'}
        </div>
      </div>

      {/* Three-panel layout */}
      <div className="app-content">
        <SplitPane 
          split="vertical" 
          defaultSize={sizes.left}
          minSize={150}
        >
          {/* Left panel: Documents */}
          <DocumentPanel
            documents={documents}
            selectedDocument={selectedDocument}
            onDocumentSelect={handleDocumentSelect}
            approvalContext={approvalRequest?.actions?.find(a => 
              a.tool_name === 'get_documents' || a.tool_name === 'get_page_text'
            )}
          />

          <SplitPane 
            split="vertical" 
            defaultSize={sizes.center}
            minSize={200}
          >
            {/* Center panel: Workflow */}
            <WorkflowPanel
              messages={agentMessages}
              todos={todos}
              approvalRequest={approvalRequest}
              onStartAnalysis={startAnalysis}
              onApprovalDecision={sendApprovalDecisions}
              connectionStatus={connectionStatus}
            />

            {/* Right panel: Files */}
            <FilePanel
              files={files}
              selectedFile={selectedFile}
              onFileSelect={handleFileSelect}
              approvalContext={approvalRequest?.actions?.find(a =>
                a.tool_name === 'write_file' || a.tool_name === 'edit_file'
              )}
            />
          </SplitPane>
        </SplitPane>
      </div>
    </div>
  );
}

export default App;
