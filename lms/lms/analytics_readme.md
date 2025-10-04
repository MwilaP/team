# LMS Learning Analytics

This module provides comprehensive learning analytics for the Frappe LMS platform, tracking student engagement and progress through courses, chapters, and lessons.

## Features

- **Time Tracking**: Accurately measure time spent by students on courses, chapters, and lessons
- **Admin Dashboard**: Visualize analytics data with interactive charts and tables
- **Course Analytics**: Drill down into specific courses to see student engagement
- **Student Analytics**: View detailed analytics for individual students
- **Export**: Download analytics data as CSV for further analysis

## Architecture

### Data Model

1. **LMS Learning Session**
   - Tracks individual learning sessions with start/end times
   - Records active time and idle time
   - Links to course, chapter, and lesson

2. **LMS Learning Heartbeat**
   - Captures periodic activity signals during a session (15s intervals)
   - Tracks focus state and visibility
   - Records idle time

3. **LMS Time Analytics**
   - Stores aggregated daily metrics for reporting
   - Enables efficient querying for dashboards

### Client-side Tracking

The client-side tracking is implemented in `learning-analytics.js` and includes:
- 15-second heartbeats
- Idle detection (60s timeout)
- Page visibility tracking
- Offline queue for reliability

### Backend API

API endpoints in `learning_analytics_api.py`:
- `track_learning_session_start`: Start a learning session
- `track_learning_heartbeat`: Record a heartbeat
- `track_learning_session_end`: End a session and calculate metrics
- `get_admin_analytics`: Get data for admin dashboard
- `get_course_analytics`: Get data for course analytics
- `get_student_analytics`: Get data for student analytics
- `export_analytics_csv`: Export analytics data as CSV

### Frontend Components

- `AdminAnalytics.vue`: Main dashboard view
- `CourseAnalytics.vue`: Course-level analytics
- `StudentAnalytics.vue`: Student-level analytics

## Security

Access to analytics data is controlled by role-based permissions:
- **System Manager**: Full access to all analytics
- **Moderator**: Full access to all analytics
- **Course Creator**: Access to analytics for their courses only
- **LMS Student**: No access to admin analytics

## Installation

The analytics module is integrated into the LMS app and requires no additional installation steps.

## Usage

1. **For Administrators**:
   - Access the Learning Analytics dashboard from the sidebar
   - Use filters to view data for specific date ranges, courses, or students
   - Export data as needed

2. **For Developers**:
   - Use the `learning-analytics.js` module to track user activity
   - Call the appropriate API endpoints for data retrieval
   - Extend the analytics module as needed

## Scheduled Tasks

- `aggregate_daily_analytics`: Daily aggregation of analytics data (runs at midnight)

## Future Enhancements

- Real-time analytics dashboard
- Predictive analytics for student success
- Learning path optimization based on engagement data
- Integration with external analytics tools
