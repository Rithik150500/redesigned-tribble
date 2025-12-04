// src/components/WorkflowPanel.js
/**
 * Workflow panel - the central hub for agent interaction.
 * 
 * This panel manages multiple views:
 * 1. Initial state: Input form for starting analysis
 * 2. Active analysis: Message timeline with agent thinking
 * 3. To-do list: Current plan visible at top
 * 4. Approval dialogs: Context-rich decision points
 * 5. Completion state: Final results and report access
 * 
 * The key design principle here is progressive disclosure - show the right
 * information at the right time, with enough context for informed decisions.
 */

import React, { useState, useEffect, useRef } from 'react';
import './WorkflowPanel.css';

function WorkflowPanel({
  messages,
  todos,
  approvalRequest,
  onStartAnalysis,
  onApprovalDecision,
  connectionStatus
}) {
  const [analysisInput, setAnalysisInput] = useState('');
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const messagesEndRef = useRef(null);
  const [expandedTodos, setExpandedTodos] = useState(true);

  /**
   * Auto-scroll to newest messages as they arrive.
   * 
   * This keeps the latest agent activity visible without requiring
   * manual scrolling. We use smooth scrolling for a polished feel.
   */
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  /**
   * Handle starting a new analysis.
   */
  const handleStartAnalysis = () => {
    if (!analysisInput.trim()) {
      return;
    }

    onStartAnalysis(analysisInput);
    setAnalysisStarted(true);
  };

  /**
   * Render the initial input form.
   * 
   * This is what users see before analysis begins. We want to make it
   * clear what kinds of requests work well, so we provide examples.
   */
  const renderInputForm = () => {
    return (
      <div className="analysis-input-container">
        <h2>Legal Risk Analysis</h2>
        <p className="input-description">
          Describe what you'd like to analyze. The agent will develop a comprehensive
          strategy and work through your documents systematically.
        </p>

        <textarea
          className="analysis-input"
          value={analysisInput}
          onChange={(e) => setAnalysisInput(e.target.value)}
          placeholder="Example: Conduct a comprehensive legal risk analysis focusing on contractual obligations, intellectual property issues, and regulatory compliance..."
          rows={6}
          disabled={connectionStatus !== 'connected'}
        />

        <button
          className="start-button"
          onClick={handleStartAnalysis}
          disabled={connectionStatus !== 'connected' || !analysisInput.trim()}
        >
          {connectionStatus !== 'connected' ? 'Connecting...' : 'Start Analysis'}
        </button>

        <div className="example-queries">
          <h4>Example Analysis Requests:</h4>
          <div className="example-item" onClick={() => setAnalysisInput('Conduct a comprehensive legal risk analysis of all documents in the data room, focusing on contractual obligations, intellectual property issues, and regulatory compliance risks.')}>
            "Conduct a comprehensive legal risk analysis..."
          </div>
          <div className="example-item" onClick={() => setAnalysisInput('Review all employment agreements for non-compete clauses, confidentiality provisions, and potential enforceability issues.')}>
            "Review all employment agreements for non-compete clauses..."
          </div>
          <div className="example-item" onClick={() => setAnalysisInput('Identify all contractual deadlines and time-sensitive obligations across the document set.')}>
            "Identify all contractual deadlines and time-sensitive obligations..."
          </div>
        </div>
      </div>
    );
  };

  /**
   * Render the to-do list at the top of the workflow.
   * 
   * This shows the agent's current plan. Users can collapse it to save
   * space once they've reviewed the strategy.
   */
  const renderTodoList = () => {
    if (!todos || todos.length === 0) {
      return null;
    }

    return (
      <div className="todo-section">
        <div className="todo-header" onClick={() => setExpandedTodos(!expandedTodos)}>
          <h3>Analysis Plan</h3>
          <span className="toggle-icon">{expandedTodos ? '▼' : '▶'}</span>
        </div>

        {expandedTodos && (
          <div className="todo-list">
            {todos.map((todo, index) => (
              <div
                key={index}
                className={`todo-item ${todo.status}`}
              >
                <span className="todo-checkbox">
                  {todo.status === 'complete' ? '✓' : '○'}
                </span>
                <span className="todo-text">{todo.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  /**
   * Render a single message in the timeline.
   * 
   * Different message types get different styling and icons to make
   * scanning the timeline easier.
   */
  const renderMessage = (message, index) => {
    const getMessageIcon = (type) => {
      switch (type) {
        case 'system':
          return '⚙️';
        case 'agent':
          return '🤖';
        case 'user':
          return '👤';
        case 'error':
          return '⚠️';
        default:
          return '•';
      }
    };

    return (
      <div key={index} className={`message message-${message.type}`}>
        <div className="message-header">
          <span className="message-icon">{getMessageIcon(message.type)}</span>
          <span className="message-timestamp">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
        <div className="message-content">
          {message.content}
        </div>
      </div>
    );
  };

  /**
   * Render the approval dialog.
   * 
   * This is the most complex part of the workflow panel because it needs
   * to present rich context for each type of approval. The key is making
   * it clear WHAT the agent wants to do and WHY, with enough visual
   * context for informed decisions.
   */
  const renderApprovalDialog = () => {
    if (!approvalRequest) {
      return null;
    }

    const { actions, agent_messages } = approvalRequest;

    return (
      <div className="approval-dialog">
        <div className="approval-header">
          <h3>⚠️ Approval Required</h3>
          <p className="approval-count">
            {actions.length} action{actions.length > 1 ? 's' : ''} pending review
          </p>
        </div>

        {/* Show agent's reasoning */}
        {agent_messages && agent_messages.length > 0 && (
          <div className="agent-reasoning">
            <h4>Agent's Reasoning:</h4>
            <div className="reasoning-content">
              {agent_messages[agent_messages.length - 1].content}
            </div>
          </div>
        )}

        {/* Show each action requiring approval */}
        <div className="approval-actions">
          {actions.map((action, index) => (
            <ApprovalAction
              key={index}
              action={action}
              index={index}
              onDecision={(decision) => handleActionDecision(index, decision)}
            />
          ))}
        </div>

        {/* Batch approval buttons */}
        <div className="approval-buttons">
          <button
            className="approve-all-button"
            onClick={() => handleApproveAll()}
          >
            ✓ Approve All
          </button>
          <button
            className="reject-all-button"
            onClick={() => handleRejectAll()}
          >
            ✗ Reject All
          </button>
        </div>
      </div>
    );
  };

  /**
   * Handle approval decisions.
   * 
   * We collect decisions for all actions, then send them as a batch
   * to the backend.
   */
  const [decisions, setDecisions] = useState([]);

  const handleActionDecision = (index, decision) => {
    const newDecisions = [...decisions];
    newDecisions[index] = decision;
    setDecisions(newDecisions);

    // If all decisions are made, send them
    if (newDecisions.length === approvalRequest.actions.length) {
      onApprovalDecision(newDecisions);
      setDecisions([]);
    }
  };

  const handleApproveAll = () => {
    const allApproved = approvalRequest.actions.map(() => ({
      decision: 'approve'
    }));
    onApprovalDecision(allApproved);
    setDecisions([]);
  };

  const handleRejectAll = () => {
    const allRejected = approvalRequest.actions.map(() => ({
      decision: 'reject'
    }));
    onApprovalDecision(allRejected);
    setDecisions([]);
  };

  /**
   * Main render logic.
   * 
   * We show different views based on the current state:
   * - Before analysis: Input form
   * - During analysis: To-do list + message timeline + approvals
   */
  return (
    <div className="workflow-panel">
      {!analysisStarted ? (
        renderInputForm()
      ) : (
        <div className="workflow-content">
          {renderTodoList()}
          
          <div className="message-timeline">
            {messages.map((msg, idx) => renderMessage(msg, idx))}
            <div ref={messagesEndRef} />
          </div>

          {renderApprovalDialog()}
        </div>
      )}
    </div>
  );
}

/**
 * ApprovalAction component - renders a single action needing approval.
 * 
 * This component is separated out because each action type needs custom
 * rendering logic based on what context is available.
 */
function ApprovalAction({ action, index, onDecision }) {
  const [editMode, setEditMode] = useState(false);
  const [editedArgs, setEditedArgs] = useState(JSON.stringify(action.arguments, null, 2));

  /**
   * Render action-specific context.
   * 
   * This is where we show enriched information based on what the agent
   * wants to do. The backend has already looked up relevant metadata
   * and included it in the context field.
   */
  const renderActionContext = () => {
    const { tool_name, context } = action;

    if (!context) {
      return null;
    }

    switch (tool_name) {
      case 'get_documents':
        return renderDocumentAccessContext(context);
      case 'get_page_text':
        return renderPageAccessContext(context);
      case 'write_file':
      case 'edit_file':
        return renderFileOperationContext(context);
      case 'task':
        return renderSubagentContext(context);
      case 'write_todos':
        return renderTodoContext(context);
      default:
        return renderGenericContext(context);
    }
  };

  /**
   * Context renderer for document access.
   * 
   * Shows which documents will be accessed and highlights their
   * legally significant pages.
   */
  const renderDocumentAccessContext = (context) => {
    if (!context.documents) {
      return null;
    }

    return (
      <div className="context-details document-context">
        <h5>Documents to be accessed:</h5>
        {context.documents.map((doc, idx) => (
          <div key={idx} className="context-document">
            <div className="doc-name">📄 {doc.filename}</div>
            <div className="doc-summary">{doc.summdesc}</div>
            {doc.significant_pages && doc.significant_pages.length > 0 && (
              <div className="significant-pages">
                ⚖️ Significant pages: {doc.significant_pages.join(', ')}
              </div>
            )}
            {doc.page_summaries && (
              <div className="page-summaries-preview">
                <strong>Page summaries included:</strong>
                <ul>
                  {doc.page_summaries.slice(0, 3).map((page, pIdx) => (
                    <li key={pIdx}>
                      Page {page.page_num}: {page.summdesc}
                    </li>
                  ))}
                  {doc.page_summaries.length > 3 && (
                    <li>...and {doc.page_summaries.length - 3} more pages</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  /**
   * Context renderer for specific page access.
   */
  const renderPageAccessContext = (context) => {
    if (!context.pages) {
      return null;
    }

    return (
      <div className="context-details page-context">
        <h5>Pages to be accessed:</h5>
        <div className="context-document">
          <div className="doc-name">📄 {context.document_name}</div>
          <div className="pages-list">
            {context.pages.map((page, idx) => (
              <div key={idx} className="page-item">
                <strong>Page {page.page_num}:</strong> {page.summdesc}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  /**
   * Context renderer for file operations.
   */
  const renderFileOperationContext = (context) => {
    return (
      <div className="context-details file-context">
        <h5>File: {context.file_path}</h5>
        <div className="file-preview">
          <pre>{context.content}</pre>
        </div>
      </div>
    );
  };

  /**
   * Context renderer for subagent invocations.
   */
  const renderSubagentContext = (context) => {
    return (
      <div className="context-details subagent-context">
        <h5>Subagent: {context.subagent_name}</h5>
        <div className="task-description">
          <strong>Task:</strong>
          <p>{context.task}</p>
        </div>
      </div>
    );
  };

  /**
   * Context renderer for to-do list updates.
   */
  const renderTodoContext = (context) => {
    if (!context.todos) {
      return null;
    }

    return (
      <div className="context-details todo-context">
        <h5>Proposed Analysis Plan:</h5>
        <ol className="todo-preview">
          {context.todos.map((todo, idx) => (
            <li key={idx}>{todo}</li>
          ))}
        </ol>
      </div>
    );
  };

  /**
   * Generic context renderer for other tool types.
   */
  const renderGenericContext = (context) => {
    return (
      <div className="context-details generic-context">
        <pre>{JSON.stringify(context, null, 2)}</pre>
      </div>
    );
  };

  /**
   * Handle editing arguments.
   */
  const handleSaveEdit = () => {
    try {
      const parsed = JSON.parse(editedArgs);
      onDecision({
        decision: 'approve',
        edited_arguments: parsed
      });
      setEditMode(false);
    } catch (error) {
      alert('Invalid JSON syntax in edited arguments');
    }
  };

  return (
    <div className="approval-action">
      <div className="action-header">
        <h4>
          <span className="action-number">{index + 1}.</span>
          {action.tool_name}
        </h4>
        <span className="action-allowed-decisions">
          Allowed: {action.review_config?.allowed_decisions?.join(', ')}
        </span>
      </div>

      {/* Show arguments */}
      <div className="action-arguments">
        <h5>Arguments:</h5>
        {editMode ? (
          <textarea
            className="edit-arguments"
            value={editedArgs}
            onChange={(e) => setEditedArgs(e.target.value)}
            rows={10}
          />
        ) : (
          <pre>{JSON.stringify(action.arguments, null, 2)}</pre>
        )}
      </div>

      {/* Show enriched context */}
      {renderActionContext()}

      {/* Action buttons */}
      <div className="action-buttons">
        {action.review_config?.allowed_decisions?.includes('approve') && (
          <button
            className="approve-button"
            onClick={() => onDecision({ decision: 'approve' })}
          >
            ✓ Approve
          </button>
        )}
        
        {action.review_config?.allowed_decisions?.includes('edit') && (
          <>
            {editMode ? (
              <>
                <button className="save-edit-button" onClick={handleSaveEdit}>
                  Save & Approve
                </button>
                <button className="cancel-edit-button" onClick={() => setEditMode(false)}>
                  Cancel
                </button>
              </>
            ) : (
              <button className="edit-button" onClick={() => setEditMode(true)}>
                ✏️ Edit
              </button>
            )}
          </>
        )}
        
        {action.review_config?.allowed_decisions?.includes('reject') && (
          <button
            className="reject-button"
            onClick={() => onDecision({ decision: 'reject' })}
          >
            ✗ Reject
          </button>
        )}
      </div>
    </div>
  );
}

export default WorkflowPanel;
