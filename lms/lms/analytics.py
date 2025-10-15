"""Analytics functionality for the LMS module."""

import frappe
from frappe import _
from frappe.utils import getdate, add_days, now_datetime, cint, flt, get_datetime
from datetime import datetime, timedelta


def update_time_analytics(session):
    """Update time analytics from a session."""
    # Get date from session
    date = getdate(session.start_time)
    
    # Check if analytics record exists
    filters = {
        "member": session.member,
        "course": session.course,
        "chapter": session.chapter or "",
        "lesson": session.lesson or "",
        "date": date
    }
    
    analytics = frappe.db.get_value("LMS Time Analytics", filters, ["name", "active_time", "sessions_count"])
    
    if analytics:
        name, active_time, sessions_count = analytics
        frappe.db.set_value(
            "LMS Time Analytics", 
            name, 
            {
                "active_time": cint(active_time) + cint(session.active_time),
                "sessions_count": cint(sessions_count) + 1
            }
        )
    else:
        doc = frappe.get_doc({
            "doctype": "LMS Time Analytics",
            "member": session.member,
            "course": session.course,
            "chapter": session.chapter or "",
            "lesson": session.lesson or "",
            "date": date,
            "active_time": session.active_time,
            "sessions_count": 1
        })
        doc.insert(ignore_permissions=True)
    
    # Note: Time tracking is stored in LMS Time Analytics
    # LMS Course Progress is used only for completion tracking


def get_student_time_analytics(student=None, course=None, from_date=None, to_date=None):
    """Get time analytics for students."""
    filters = {}
    
    if student:
        filters["member"] = student
    if course:
        filters["course"] = course
    if from_date:
        filters["date"] = [">=", from_date]
    if to_date:
        filters["date"] = ["<=", to_date]
    
    analytics = frappe.get_all(
        "LMS Time Analytics",
        filters=filters,
        fields=["member", "member_name", "course", "course_name", "date", "active_time", "sessions_count"],
        order_by="date desc"
    )
    
    # Group by student and course
    result = {}
    for a in analytics:
        key = (a.member, a.course)
        if key not in result:
            result[key] = {
                "member": a.member,
                "member_name": a.member_name,
                "course": a.course,
                "course_name": a.course_name,
                "total_active_time": 0,
                "total_sessions": 0,
                "days_active": 0,
                "daily_data": []
            }
        
        result[key]["total_active_time"] += cint(a.active_time)
        result[key]["total_sessions"] += cint(a.sessions_count)
        result[key]["days_active"] += 1
        result[key]["daily_data"].append({
            "date": a.date,
            "active_time": a.active_time,
            "sessions": a.sessions_count
        })
    
    return list(result.values())


def get_course_time_analytics(course, from_date=None, to_date=None):
    """Get time analytics for a specific course."""
    filters = {"course": course}
    
    if from_date:
        filters["date"] = [">=", from_date]
    if to_date:
        filters["date"] = ["<=", to_date]
    
    # Get chapter/lesson analytics
    unit_analytics = frappe.db.sql("""
        SELECT 
            chapter, chapter_name, lesson, lesson_name, 
            SUM(active_time) as total_active_time,
            SUM(sessions_count) as total_sessions,
            COUNT(DISTINCT member) as unique_students
        FROM `tabLMS Time Analytics`
        WHERE course = %s
        AND date BETWEEN %s AND %s
        GROUP BY chapter, lesson
        ORDER BY chapter, lesson
    """, (course, from_date or '2000-01-01', to_date or '2099-12-31'), as_dict=True)
    
    # Get student analytics
    student_analytics = frappe.db.sql("""
        SELECT 
            member, member_name,
            SUM(active_time) as total_active_time,
            SUM(sessions_count) as total_sessions,
            COUNT(DISTINCT date) as days_active
        FROM `tabLMS Time Analytics`
        WHERE course = %s
        AND date BETWEEN %s AND %s
        GROUP BY member
        ORDER BY total_active_time DESC
    """, (course, from_date or '2000-01-01', to_date or '2099-12-31'), as_dict=True)
    
    # Get daily analytics
    daily_analytics = frappe.db.sql("""
        SELECT 
            date,
            SUM(active_time) as total_active_time,
            SUM(sessions_count) as total_sessions,
            COUNT(DISTINCT member) as unique_students
        FROM `tabLMS Time Analytics`
        WHERE course = %s
        AND date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
    """, (course, from_date or '2000-01-01', to_date or '2099-12-31'), as_dict=True)
    
    # Get course completion data
    completion_data = frappe.db.sql("""
        SELECT 
            status, COUNT(*) as count
        FROM `tabLMS Course Progress`
        WHERE course = %s
        GROUP BY status
    """, (course,), as_dict=True)
    
    completion_stats = {
        "Complete": 0,
        "Partially Complete": 0,
        "Incomplete": 0
    }
    
    for item in completion_data:
        completion_stats[item.status] = item.count
    
    # Calculate summary metrics
    total_time = sum(item.total_active_time for item in student_analytics)
    total_students = len(student_analytics)
    avg_time_per_student = total_time / total_students if total_students > 0 else 0
    
    return {
        "summary": {
            "total_active_time": total_time,
            "total_students": total_students,
            "avg_time_per_student": avg_time_per_student,
            "completion_stats": completion_stats
        },
        "units": unit_analytics,
        "students": student_analytics,
        "daily": daily_analytics
    }


def get_student_course_analytics(student, course=None):
    """Get detailed analytics for a specific student."""
    filters = {"member": student}
    
    if course:
        filters["course"] = course
    
    # Get course-level analytics
    course_analytics = frappe.db.sql("""
        SELECT 
            course, course_name,
            SUM(active_time) as total_active_time,
            SUM(sessions_count) as total_sessions,
            COUNT(DISTINCT date) as days_active,
            MIN(date) as first_access,
            MAX(date) as last_access
        FROM `tabLMS Time Analytics`
        WHERE member = %s
        GROUP BY course
        ORDER BY total_active_time DESC
    """, (student,), as_dict=True)
    
    result = []
    
    # Enrich with completion data and chapter/lesson details
    for course_data in course_analytics:
        course_id = course_data.course
        
        # Get completion percentage
        progress = frappe.db.get_value(
            "LMS Enrollment",
            {"course": course_id, "member": student},
            "progress"
        )
        
        # Get chapter/lesson analytics
        unit_analytics = frappe.db.sql("""
            SELECT 
                chapter, chapter_name, lesson, lesson_name, 
                SUM(active_time) as total_active_time,
                SUM(sessions_count) as total_sessions,
                MAX(date) as last_access
            FROM `tabLMS Time Analytics`
            WHERE member = %s AND course = %s
            GROUP BY chapter, lesson
            ORDER BY chapter, lesson
        """, (student, course_id), as_dict=True)
        
        # Group by chapter
        chapters = {}
        for unit in unit_analytics:
            chapter_id = unit.chapter
            if not chapter_id:
                continue
                
            if chapter_id not in chapters:
                chapters[chapter_id] = {
                    "name": chapter_id,
                    "title": unit.chapter_name,
                    "total_active_time": 0,
                    "lessons": []
                }
            
            chapters[chapter_id]["total_active_time"] += cint(unit.total_active_time)
            
            if unit.lesson:
                chapters[chapter_id]["lessons"].append({
                    "name": unit.lesson,
                    "title": unit.lesson_name,
                    "active_time": unit.total_active_time,
                    "last_access": unit.last_access
                })
        
        # Get daily activity
        daily_activity = frappe.db.sql("""
            SELECT 
                date,
                SUM(active_time) as active_time,
                SUM(sessions_count) as sessions
            FROM `tabLMS Time Analytics`
            WHERE member = %s AND course = %s
            GROUP BY date
            ORDER BY date
        """, (student, course_id), as_dict=True)
        
        result.append({
            "course": {
                "name": course_id,
                "title": course_data.course_name
            },
            "summary": {
                "total_active_time": course_data.total_active_time,
                "sessions_count": course_data.total_sessions,
                "days_active": course_data.days_active,
                "first_access": course_data.first_access,
                "last_access": course_data.last_access,
                "completion": progress or 0
            },
            "chapters": list(chapters.values()),
            "daily_activity": daily_activity
        })
    
    return result


def aggregate_daily_analytics():
    """Scheduled task to aggregate analytics data."""
    yesterday = getdate(add_days(now_datetime(), -1))
    
    # Find sessions that ended yesterday
    sessions = frappe.get_all(
        "LMS Learning Session",
        filters={
            "end_time": ["between", [datetime.combine(yesterday, datetime.min.time()), 
                                     datetime.combine(yesterday, datetime.max.time())]]
        },
        fields=["name"]
    )
    
    # Process each session
    for session_data in sessions:
        session = frappe.get_doc("LMS Learning Session", session_data.name)
        update_time_analytics(session)
    
    frappe.db.commit()
