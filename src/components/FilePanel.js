// src/components/FilePanel.js
/**
 * File panel component.
 * 
 * This panel shows the agent's filesystem workspace and provides viewing/editing
 * capabilities. It has three main modes:
 * 1. Browser mode: Tree view of all files and directories
 * 2. Viewer mode: Display file contents with syntax highlighting
 * 3. Approval mode: Show pending file operations with diff view
 */

import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import './FilePanel.css';

function FilePanel({ files, selectedFile, onFileSelect, approvalContext }) {
  const [fileTree, setFileTree] = useState({});
  const [fileContent, setFileContent] = useState(null);
  const [viewMode, setViewMode] = useState('browser'); // 'browser' or 'viewer'

  /**
   * Organize files into a tree structure for display.
   * 
   * The agent's filesystem has a directory structure like:
   * /analysis/employment_agreements.md
   * /analysis/ip_analysis.md
   * /notes/risk_summary.txt
   * /report/final_report.md
   * 
   * We need to organize this into a hierarchical tree for navigation.
   */
  useEffect(() => {
    const tree = buildFileTree(files);
    setFileTree(tree);
  }, [files]);

  /**
   * When a file is selected, load its content.
   */
  useEffect(() => {
    if (selectedFile) {
      loadFileContent(selectedFile);
      setViewMode('viewer');
    } else {
      setViewMode('browser');
    }
  }, [selectedFile]);

  /**
   * Build a tree structure from flat file list.
   */
  const buildFileTree = (files) => {
    const tree = {};

    files.forEach(file => {
      const parts = file.path.split('/').filter(p => p);
      let current = tree;

      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // This is a file
          if (!current.files) {
            current.files = [];
          }
          current.files.push({
            name: part,
            path: file.path,
            size: file.size,
            modified: file.modified
          });
        } else {
          // This is a directory
          if (!current.dirs) {
            current.dirs = {};
          }
          if (!current.dirs[part]) {
            current.dirs[part] = {};
          }
          current = current.dirs[part];
        }
      });
    });

    return tree;
  };

  /**
   * Load file content from backend.
   */
  const loadFileContent = async (file) => {
    try {
      // In a real implementation, you'd fetch from your backend
      // For now, we'll assume the file object already has content
      setFileContent({
        path: file.path,
        content: file.content || 'Loading...',
        language: detectLanguage(file.path)
      });
    } catch (error) {
      console.error('Failed to load file:', error);
    }
  };

  /**
   * Detect programming language for syntax highlighting.
   */
  const detectLanguage = (path) => {
    const ext = path.split('.').pop().toLowerCase();
    const languageMap = {
      'md': 'markdown',
      'txt': 'plaintext',
      'py': 'python',
      'js': 'javascript',
      'json': 'json',
      'html': 'html',
      'css': 'css'
    };
    return languageMap[ext] || 'plaintext';
  };

  /**
   * Render the file tree browser.
   */
  const renderFileTree = (tree, depth = 0) => {
    const items = [];

    // Render directories
    if (tree.dirs) {
      Object.keys(tree.dirs).sort().forEach(dirName => {
        items.push(
          <DirectoryItem
            key={`dir-${dirName}-${depth}`}
            name={dirName}
            depth={depth}
            tree={tree.dirs[dirName]}
            onFileSelect={onFileSelect}
          />
        );
      });
    }

    // Render files
    if (tree.files) {
      tree.files.sort((a, b) => a.name.localeCompare(b.name)).forEach(file => {
        items.push(
          <FileItem
            key={`file-${file.path}`}
            file={file}
            depth={depth}
            isSelected={selectedFile?.path === file.path}
            isHighlighted={isFileHighlighted(file.path)}
            onSelect={onFileSelect}
          />
        );
      });
    }

    return items;
  };

  /**
   * Check if a file is highlighted due to approval context.
   */
  const isFileHighlighted = (filePath) => {
    if (!approvalContext || !approvalContext.context) {
      return false;
    }

    const { tool_name, context } = approvalContext;
    
    if ((tool_name === 'write_file' || tool_name === 'edit_file') && context.file_path) {
      return context.file_path === filePath;
    }

    return false;
  };

  /**
   * Render the file browser view.
   */
  const renderBrowser = () => {
    return (
      <div className="file-browser">
        <div className="panel-header">
          <h2>Agent Workspace</h2>
          <span className="file-count">{files.length} files</span>
        </div>

        {approvalContext && (
          <div className="approval-indicator">
            ⚠️ File operation pending approval
          </div>
        )}

        <div className="file-tree">
          {Object.keys(fileTree).length === 0 ? (
            <div className="empty-state">
              <p>No files yet.</p>
              <p className="empty-hint">
                Files will appear here as the agent conducts its analysis.
              </p>
            </div>
          ) : (
            renderFileTree(fileTree)
          )}
        </div>
      </div>
    );
  };

  /**
   * Render the file viewer with syntax highlighting.
   */
  const renderViewer = () => {
    if (!fileContent) {
      return <div className="loading">Loading file...</div>;
    }

    return (
      <div className="file-viewer">
        <div className="viewer-header">
          <button onClick={() => onFileSelect(null)} className="back-button">
            ← Back to Files
          </button>
          <h3>{fileContent.path}</h3>
        </div>

        <div className="editor-container">
          <Editor
            height="100%"
            language={fileContent.language}
            value={fileContent.content}
            theme="vs-light"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              wordWrap: 'on'
            }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="file-panel">
      {viewMode === 'browser' ? renderBrowser() : renderViewer()}
    </div>
  );
}

/**
 * DirectoryItem component - a collapsible directory in the tree.
 */
function DirectoryItem({ name, depth, tree, onFileSelect }) {
  const [expanded, setExpanded] = useState(true);

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  const indent = depth * 20;

  return (
    <>
      <div
        className="directory-item"
        style={{ paddingLeft: `${indent}px` }}
        onClick={handleToggle}
      >
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
        <span className="directory-icon">📁</span>
        <span className="directory-name">{name}</span>
      </div>

      {expanded && (
        <div className="directory-children">
          {renderFileTree(tree, depth + 1, onFileSelect)}
        </div>
      )}
    </>
  );

  // Helper function to render the tree (same logic as in FilePanel)
  function renderFileTree(tree, depth) {
    const items = [];

    if (tree.dirs) {
      Object.keys(tree.dirs).sort().forEach(dirName => {
        items.push(
          <DirectoryItem
            key={`subdir-${dirName}-${depth}`}
            name={dirName}
            depth={depth}
            tree={tree.dirs[dirName]}
            onFileSelect={onFileSelect}
          />
        );
      });
    }

    if (tree.files) {
      tree.files.sort((a, b) => a.name.localeCompare(b.name)).forEach(file => {
        items.push(
          <FileItem
            key={`subfile-${file.path}`}
            file={file}
            depth={depth}
            isSelected={false}
            isHighlighted={false}
            onSelect={onFileSelect}
          />
        );
      });
    }

    return items;
  }
}

/**
 * FileItem component - a single file in the tree.
 */
function FileItem({ file, depth, isSelected, isHighlighted, onSelect }) {
  const indent = depth * 20;

  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.md')) return '📝';
    if (fileName.endsWith('.txt')) return '📄';
    if (fileName.endsWith('.json')) return '📊';
    if (fileName.endsWith('.py')) return '🐍';
    return '📄';
  };

  return (
    <div
      className={`file-item ${isSelected ? 'selected' : ''} ${isHighlighted ? 'highlighted' : ''}`}
      style={{ paddingLeft: `${indent + 20}px` }}
      onClick={() => onSelect(file)}
    >
      <span className="file-icon">{getFileIcon(file.name)}</span>
      <span className="file-name">{file.name}</span>
      {file.size && (
        <span className="file-size">{formatFileSize(file.size)}</span>
      )}
    </div>
  );
}

/**
 * Format file size for display.
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default FilePanel;
