import { call } from 'frappe-ui';

// Configuration
const HEARTBEAT_INTERVAL = 15000; // 15 seconds
const IDLE_TIMEOUT = 60000; // 60 seconds

class LearningAnalytics {
  constructor() {
    this.currentSession = null;
    this.heartbeatTimer = null;
    this.lastActivity = Date.now();
    this.isActive = true;
    this.isVisible = true;
    this.sessionQueue = []; // For offline support
  }

  // Initialize tracking
  init() {
    // Set up visibility change detection
    document.addEventListener('visibilitychange', this._handleVisibilityChange.bind(this));
    
    // Set up activity tracking
    document.addEventListener('mousemove', this._handleUserActivity.bind(this));
    document.addEventListener('keypress', this._handleUserActivity.bind(this));
    document.addEventListener('click', this._handleUserActivity.bind(this));
    document.addEventListener('scroll', this._handleUserActivity.bind(this));
    
    // Set up page unload
    window.addEventListener('beforeunload', this._handleBeforeUnload.bind(this));
    
    // Check for unsent sessions in localStorage
    this._processOfflineQueue();
  }

  // Start a learning session
  startSession(courseId, unitType, unitId) {
    // End any existing session
    if (this.currentSession) {
      this.endSession('navigate');
    }
    
    // Create new session
    call('lms.lms.learning_analytics_api.track_learning_session_start', {
      course_id: courseId,
      unit_type: unitType,
      unit_id: unitId
    }).then(response => {
      this.currentSession = {
        id: response.session_id,
        courseId,
        unitType,
        unitId,
        startTime: Date.now()
      };
      
      // Start heartbeat
      this._startHeartbeat();
    }).catch(error => {
      console.error('Failed to start learning session:', error);
      // Store session start for offline processing
      this._queueOfflineEvent('session_start', {
        course_id: courseId,
        unit_type: unitType,
        unit_id: unitId,
        timestamp: Date.now()
      });
    });
  }

  // End current session
  endSession(reason = 'navigate') {
    if (!this.currentSession) return;
    
    // Stop heartbeat
    this._stopHeartbeat();
    
    // Send session end
    call('lms.lms.learning_analytics_api.track_learning_session_end', {
      session_id: this.currentSession.id,
      end_reason: reason
    }).catch(error => {
      console.error('Failed to end learning session:', error);
      // Store session end for offline processing
      this._queueOfflineEvent('session_end', {
        session_id: this.currentSession.id,
        end_reason: reason,
        timestamp: Date.now()
      });
    });
    
    this.currentSession = null;
  }

  // Private: Start heartbeat timer
  _startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this._sendHeartbeat();
    }, HEARTBEAT_INTERVAL);
  }

  // Private: Stop heartbeat timer
  _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // Private: Send heartbeat to server
  _sendHeartbeat() {
    if (!this.currentSession) return;
    
    // Calculate idle time
    const idleTime = Date.now() - this.lastActivity;
    
    // Check if user is idle
    if (idleTime >= IDLE_TIMEOUT) {
      this.isActive = false;
      
      // If idle timeout reached, end session
      this.endSession('idle_timeout');
      return;
    }
    
    // Send heartbeat
    call('lms.lms.learning_analytics_api.track_learning_heartbeat', {
      session_id: this.currentSession.id,
      is_focused: this.isActive,
      is_visible: this.isVisible,
      idle_ms: idleTime
    }).catch(error => {
      console.error('Failed to send heartbeat:', error);
      // Store heartbeat for offline processing
      this._queueOfflineEvent('heartbeat', {
        session_id: this.currentSession.id,
        is_focused: this.isActive,
        is_visible: this.isVisible,
        idle_ms: idleTime,
        timestamp: Date.now()
      });
    });
  }

  // Private: Handle visibility change
  _handleVisibilityChange() {
    this.isVisible = document.visibilityState === 'visible';
    
    if (this.currentSession) {
      if (this.isVisible) {
        // Page became visible again
        this._handleUserActivity();
      } else {
        // Page hidden
        this._sendHeartbeat();
      }
    }
  }

  // Private: Handle user activity
  _handleUserActivity() {
    this.lastActivity = Date.now();
    this.isActive = true;
  }

  // Private: Handle page unload
  _handleBeforeUnload() {
    if (this.currentSession) {
      // Synchronous end session on page unload
      const formData = new FormData();
      formData.append('cmd', 'lms.lms.learning_analytics_api.track_learning_session_end');
      formData.append('session_id', this.currentSession.id);
      formData.append('end_reason', 'close');
      
      navigator.sendBeacon('/api/method/lms.lms.learning_analytics_api.track_learning_session_end', formData);
    }
  }

  // Private: Queue offline event
  _queueOfflineEvent(type, data) {
    const event = { type, data };
    this.sessionQueue.push(event);
    
    // Store in localStorage
    try {
      localStorage.setItem('lms_analytics_queue', JSON.stringify(this.sessionQueue));
    } catch (e) {
      console.error('Failed to store offline event:', e);
    }
  }

  // Private: Process offline queue
  _processOfflineQueue() {
    try {
      const queue = localStorage.getItem('lms_analytics_queue');
      if (queue) {
        this.sessionQueue = JSON.parse(queue);
        
        // Process queue
        if (navigator.onLine) {
          this._sendQueuedEvents();
        } else {
          // Listen for online event
          window.addEventListener('online', this._sendQueuedEvents.bind(this));
        }
      }
    } catch (e) {
      console.error('Failed to process offline queue:', e);
    }
  }

  // Private: Send queued events
  _sendQueuedEvents() {
    if (!this.sessionQueue.length) return;
    
    // Process each event
    const promises = this.sessionQueue.map(event => {
      switch (event.type) {
        case 'session_start':
          return call('lms.lms.learning_analytics_api.track_learning_session_start', event.data);
        case 'session_end':
          return call('lms.lms.learning_analytics_api.track_learning_session_end', event.data);
        case 'heartbeat':
          return call('lms.lms.learning_analytics_api.track_learning_heartbeat', event.data);
        default:
          return Promise.resolve();
      }
    });
    
    // Clear queue when all sent
    Promise.allSettled(promises).then(() => {
      this.sessionQueue = [];
      localStorage.removeItem('lms_analytics_queue');
    });
  }
}

// Create singleton instance
const analytics = new LearningAnalytics();
export default analytics;
