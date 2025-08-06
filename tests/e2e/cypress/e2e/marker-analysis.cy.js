describe('Marker Engine E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.intercept('GET', '**/health', { statusCode: 200, body: { status: 'healthy' } });
    cy.intercept('GET', '**/api/markers', { fixture: 'markers.json' });
  });

  describe('File Upload', () => {
    it('should upload and analyze a WhatsApp ZIP file', () => {
      // Prepare file upload
      cy.fixture('whatsapp-chat.zip', 'base64').then(fileContent => {
        cy.get('[data-testid="file-uploader"]').attachFile({
          fileContent,
          fileName: 'whatsapp-chat.zip',
          mimeType: 'application/zip',
          encoding: 'base64'
        });
      });

      // Verify upload started
      cy.contains('Analyzing...').should('be.visible');
      
      // Wait for analysis
      cy.intercept('POST', '**/api/upload', {
        statusCode: 200,
        body: {
          status: 'success',
          file_id: 'test-file-123',
          filename: 'whatsapp-chat.zip'
        }
      });

      // Check for results
      cy.get('[data-testid="marker-timeline"]', { timeout: 10000 }).should('be.visible');
      cy.get('[data-testid="marker-badges"]').should('be.visible');
    });

    it('should handle text input analysis', () => {
      const testText = 'This is a test message for marker analysis. I feel happy today!';
      
      cy.get('[data-testid="text-input"]').type(testText);
      cy.get('[data-testid="text-input"]').blur();

      // Mock WebSocket connection
      cy.window().its('socket').invoke('emit', 'analyze_stream', {
        content: testText,
        session_id: 'test-session'
      });

      // Verify markers appear
      cy.get('[data-testid="marker-badge"]').should('have.length.greaterThan', 0);
      cy.get('[data-testid="emotion-chart"]').should('be.visible');
    });
  });

  describe('Marker Visualization', () => {
    beforeEach(() => {
      // Setup mock data
      cy.intercept('GET', '**/api/events/*', { fixture: 'events.json' });
    });

    it('should display marker timeline correctly', () => {
      cy.get('[data-testid="marker-timeline"]').should('be.visible');
      
      // Check timeline elements
      cy.get('.timeline-marker').should('have.length.greaterThan', 0);
      
      // Check marker levels
      cy.get('.marker-level-ATO').should('exist');
      cy.get('.marker-level-SEM').should('exist');
      cy.get('.marker-level-CLU').should('exist');
      cy.get('.marker-level-MEMA').should('exist');
    });

    it('should show emotion dynamics chart', () => {
      cy.get('[data-testid="emotion-chart"]').should('be.visible');
      
      // Check chart elements
      cy.get('canvas').should('exist');
      
      // Verify metrics
      cy.contains('Home Base').should('be.visible');
      cy.contains('Variability').should('be.visible');
      cy.contains('Drift').should('be.visible');
    });

    it('should display marker badges with correct colors', () => {
      cy.get('[data-testid="marker-badges"]').within(() => {
        cy.get('.badge-ATO').should('have.css', 'background-color', 'rgb(59, 130, 246)');
        cy.get('.badge-SEM').should('have.css', 'background-color', 'rgb(34, 197, 94)');
        cy.get('.badge-CLU').should('have.css', 'background-color', 'rgb(251, 191, 36)');
        cy.get('.badge-MEMA').should('have.css', 'background-color', 'rgb(239, 68, 68)');
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export analysis as YAML', () => {
      // Trigger some analysis first
      cy.get('[data-testid="text-input"]').type('Test message');
      cy.get('[data-testid="text-input"]').blur();
      
      cy.wait(2000); // Wait for analysis
      
      // Click export button
      cy.get('[data-testid="export-button"]').click();
      cy.get('[data-testid="export-yaml"]').click();
      
      // Verify download
      cy.readFile('cypress/downloads/analysis_*.yaml').should('exist');
    });

    it('should export analysis as JSON', () => {
      cy.get('[data-testid="export-button"]').click();
      cy.get('[data-testid="export-json"]').click();
      
      cy.readFile('cypress/downloads/analysis_*.json').should('exist');
    });
  });

  describe('Real-time Updates', () => {
    it('should receive real-time marker events via WebSocket', () => {
      // Mock WebSocket events
      cy.window().then(win => {
        const mockEvent = {
          marker_id: 'A_TE_',
          level: 'ATO',
          content: 'Test marker',
          confidence: 0.95
        };
        
        win.socket.emit('marker_event', { event: mockEvent });
      });
      
      // Verify marker appears
      cy.get('[data-testid="marker-badge"]').contains('A_TE_').should('be.visible');
    });

    it('should update statistics in real-time', () => {
      const initialCount = 5;
      
      // Check initial count
      cy.get('[data-testid="total-markers"]').should('contain', initialCount);
      
      // Emit new marker event
      cy.window().its('socket').invoke('emit', 'marker_event', {
        event: { marker_id: 'NEW_', level: 'ATO' }
      });
      
      // Verify count increased
      cy.get('[data-testid="total-markers"]').should('contain', initialCount + 1);
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', () => {
      cy.intercept('POST', '**/api/upload', {
        statusCode: 500,
        body: { error: 'Internal server error' }
      });
      
      // Try to upload
      cy.get('[data-testid="file-uploader"]').attachFile('test.txt');
      
      // Check error message
      cy.contains('Failed to upload file').should('be.visible');
    });

    it('should handle WebSocket disconnection', () => {
      // Disconnect WebSocket
      cy.window().its('socket').invoke('disconnect');
      
      // Check disconnection message
      cy.contains('Connection lost').should('be.visible');
      
      // Verify reconnection attempt
      cy.wait(5000);
      cy.window().its('socket').its('connected').should('be.true');
    });
  });

  describe('Performance', () => {
    it('should load page within acceptable time', () => {
      cy.visit('/', {
        onBeforeLoad: (win) => {
          win.performance.mark('start');
        },
        onLoad: (win) => {
          win.performance.mark('end');
          win.performance.measure('pageLoad', 'start', 'end');
          
          const measure = win.performance.getEntriesByName('pageLoad')[0];
          expect(measure.duration).to.be.lessThan(3000); // 3 seconds
        }
      });
    });

    it('should handle large datasets efficiently', () => {
      // Generate large dataset
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        marker_id: `M_${i}`,
        level: ['ATO', 'SEM', 'CLU', 'MEMA'][i % 4],
        content: `Marker ${i}`,
        confidence: Math.random()
      }));
      
      // Send large dataset
      cy.window().its('socket').invoke('emit', 'analysis_complete', {
        result: { markers: largeDataset }
      });
      
      // Verify rendering performance
      cy.get('[data-testid="marker-timeline"]').should('be.visible');
      cy.get('[data-testid="marker-badges"]').children().should('have.length.lessThan', 100); // Should paginate
    });
  });
});