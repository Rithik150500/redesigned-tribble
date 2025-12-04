// src/components/DocumentPanel.js
/**
 * Document panel component.
 * 
 * This panel has two modes:
 * 1. List mode: Shows all documents with summaries
 * 2. Viewer mode: Shows full PDF viewer with highlighted pages
 * 
 * When the agent requests to access documents (get_documents or get_page_text),
 * this panel highlights the relevant documents and pages to give you context
 * for your approval decision.
 */

import React, { useState, useEffect } from 'react';
import { Viewer, Worker } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';
import './DocumentPanel.css';

function DocumentPanel({ documents, selectedDocument, onDocumentSelect, approvalContext }) {
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'viewer'
  const [documentDetail, setDocumentDetail] = useState(null);
  const [highlightedPages, setHighlightedPages] = useState([]);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);

  // Create PDF viewer plugin with default layout
  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  /**
   * When a document is selected, load its detailed information.
   * 
   * This includes all page summaries and legally significant page markers,
   * which we use for highlighting in the viewer.
   */
  useEffect(() => {
    if (selectedDocument) {
      loadDocumentDetail(selectedDocument.doc_id);
      setViewMode('viewer');
    } else {
      setViewMode('list');
    }
  }, [selectedDocument]);

  /**
   * When approval context changes (agent wants to access documents),
   * update highlighting to show relevant documents and pages.
   */
  useEffect(() => {
    if (approvalContext && approvalContext.context) {
      const context = approvalContext.context;
      
      if (context.tool === 'get_documents' && context.documents) {
        // Highlight documents that will be accessed
        // For simplicity, we'll highlight the first one in the viewer
        if (context.documents.length > 0) {
          const firstDoc = context.documents[0];
          setHighlightedPages(firstDoc.significant_pages || []);
        }
      } else if (context.tool === 'get_page_text' && context.pages) {
        // Highlight specific pages that will be accessed
        const pageNums = context.pages.map(p => p.page_num);
        setHighlightedPages(pageNums);
      }
    } else {
      // No approval context, show default highlighting (legally significant pages)
      if (documentDetail) {
        setHighlightedPages(documentDetail.significant_pages || []);
      }
    }
  }, [approvalContext, documentDetail]);

  /**
   * Load detailed information about a document.
   */
  const loadDocumentDetail = async (docId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/documents/${docId}`);
      const data = await response.json();
      setDocumentDetail(data);
    } catch (error) {
      console.error('Failed to load document detail:', error);
    }
  };

  /**
   * Handle clicking back to document list.
   */
  const handleBackToList = () => {
    setViewMode('list');
    onDocumentSelect(null);
  };

  /**
   * Render the document list view.
   */
  const renderDocumentList = () => {
    // Check if any documents are highlighted by approval context
    const highlightedDocIds = approvalContext?.context?.documents?.map(d => d.doc_id) || [];

    return (
      <div className="document-list">
        <div className="panel-header">
          <h2>Data Room Documents</h2>
          <span className="document-count">{documents.length} documents</span>
        </div>

        <div className="document-items">
          {documents.map(doc => {
            const isHighlighted = highlightedDocIds.includes(doc.doc_id);
            
            return (
              <div
                key={doc.doc_id}
                className={`document-item ${isHighlighted ? 'highlighted' : ''}`}
                onClick={() => onDocumentSelect(doc)}
              >
                <div className="document-icon">📄</div>
                <div className="document-info">
                  <div className="document-name">{doc.filename}</div>
                  <div className="document-summary">{doc.summdesc}</div>
                  <div className="document-meta">
                    {doc.total_pages} pages
                    {doc.legally_significant_pages > 0 && (
                      <span className="significant-badge">
                        ⚖️ {doc.legally_significant_pages} significant
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  /**
   * Render the PDF viewer with page highlighting.
   */
  const renderDocumentViewer = () => {
    if (!selectedDocument || !documentDetail) {
      return <div className="loading">Loading document...</div>;
    }

    const pdfUrl = `http://localhost:8000/api/documents/${selectedDocument.doc_id}/pdf`;

    return (
      <div className="document-viewer">
        <div className="viewer-header">
          <button onClick={handleBackToList} className="back-button">
            ← Back to Documents
          </button>
          <h3>{selectedDocument.filename}</h3>
        </div>

        <div className="viewer-layout">
          {/* Collapsible sidebar with page summaries */}
          <div className={`page-sidebar ${sidebarExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="sidebar-toggle" onClick={() => setSidebarExpanded(!sidebarExpanded)}>
              {sidebarExpanded ? '◀' : '▶'}
            </div>
            
            {sidebarExpanded && (
              <div className="page-summaries">
                <h4>Page Summaries</h4>
                {documentDetail.pages.map(page => {
                  const isHighlighted = highlightedPages.includes(page.page_num);
                  const isSignificant = page.legally_significant;
                  
                  return (
                    <div
                      key={page.page_num}
                      className={`page-summary-item ${isHighlighted ? 'highlighted' : ''} ${isSignificant ? 'significant' : ''}`}
                    >
                      <div className="page-number">
                        {isSignificant && '⚖️ '}
                        Page {page.page_num}
                      </div>
                      <div className="page-summdesc">{page.summdesc}</div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* PDF viewer */}
          <div className="pdf-viewer-container">
            <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
              <Viewer
                fileUrl={pdfUrl}
                plugins={[defaultLayoutPluginInstance]}
              />
            </Worker>
          </div>
        </div>

        {/* Highlight indicator */}
        {highlightedPages.length > 0 && (
          <div className="highlight-indicator">
            <span className="indicator-icon">⚠️</span>
            Highlighted pages: {highlightedPages.join(', ')}
            <span className="indicator-reason">
              {approvalContext ? '(Agent requesting access)' : '(Legally significant)'}
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="document-panel">
      {viewMode === 'list' ? renderDocumentList() : renderDocumentViewer()}
    </div>
  );
}

export default DocumentPanel;
