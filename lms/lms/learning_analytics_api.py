"""API methods for learning analytics."""

import json
import csv
import io
import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, now, getdate, add_days
from frappe.utils.response import Response

from lms.lms.analytics import (
    update_time_analytics, 
    get_student_time_analytics, 
    get_course_time_analytics,
    get_student_course_analytics
)


@frappe.whitelist()
def track_learning_session_start(course_id, unit_type, unit_id, session_id=None):
    """Start a learning session."""
    if not session_id:
        session_id = frappe.generate_hash(length=16)
    
    unit_map = {
        "course": "LMS Course",
        "chapter": "Course Chapter",
        "lesson": "Course Lesson"
    }
    
    # Get related entities
    chapter_id = None
    lesson_id = None
    course_id = course_id
    
    if unit_type == "lesson":
        lesson_doc = frappe.get_doc(unit_map[unit_type], unit_id)
        lesson_id = unit_id
        chapter_id = lesson_doc.chapter
        course_id = lesson_doc.course
    elif unit_type == "chapter":
        chapter_doc = frappe.get_doc(unit_map[unit_type], unit_id)
        chapter_id = unit_id
        course_id = chapter_doc.course
    
    # Create session
    session = frappe.get_doc({
        "doctype": "LMS Learning Session",
        "session_id": session_id,
        "member": frappe.session.user,
        "course": course_id,
        "chapter": chapter_id,
        "lesson": lesson_id,
        "start_time": now(),
        "active_time": 0,
        "idle_time": 0
    })
    session.insert(ignore_permissions=True)
    
    return {"session_id": session_id}


@frappe.whitelist()
def track_learning_heartbeat(session_id, is_focused, is_visible, idle_ms=0):
    """Track a learning heartbeat."""
    try:
        session = frappe.get_doc("LMS Learning Session", {"session_id": session_id})
        
        heartbeat = frappe.get_doc({
            "doctype": "LMS Learning Heartbeat",
            "session_id": session_id,
            "member": frappe.session.user,
            "course": session.course,
            "unit_type": "lesson" if session.lesson else "chapter" if session.chapter else "course",
            "unit_id": session.lesson or session.chapter or session.course,
            "timestamp": now(),
            "is_focused": is_focused,
            "is_visible": is_visible,
            "idle_ms": idle_ms
        })
        heartbeat.insert(ignore_permissions=True)
        
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error tracking heartbeat: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def track_learning_session_end(session_id, end_reason="navigate"):
    """End a learning session."""
    try:
        session = frappe.get_doc("LMS Learning Session", {"session_id": session_id})
        session.end_time = now()
        session.end_reason = end_reason
        
        # Calculate active time from heartbeats
        heartbeats = frappe.get_all(
            "LMS Learning Heartbeat",
            filters={"session_id": session_id, "is_focused": 1, "is_visible": 1},
            fields=["timestamp"],
            order_by="timestamp"
        )
        
        if heartbeats:
            # Simple calculation: time between first and last active heartbeat
            active_time = (get_datetime(session.end_time) - 
                          get_datetime(heartbeats[0].timestamp)).total_seconds()
            session.active_time = min(active_time, 7200)  # Cap at 2 hours
        
        session.save(ignore_permissions=True)
        
        # Update aggregates
        update_time_analytics(session)
        
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error ending session: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_admin_analytics(from_date=None, to_date=None, course=None, student=None):
    """Get analytics data for admin dashboard."""
    if not frappe.has_permission("LMS Course", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # For Course Admin, restrict to their courses
    if frappe.session.user != "Administrator" and "Course Creator" in frappe.get_roles(frappe.session.user) and "System Manager" not in frappe.get_roles(frappe.session.user):
        courses = [c.name for c in frappe.get_list("LMS Course", 
                                                  filters={"owner": frappe.session.user})]
        if course and course not in courses:
            frappe.throw(_("Not permitted"), frappe.PermissionError)
        elif not course:
            course = ["in", courses]
    
    # Set default date range if not provided
    if not from_date:
        from_date = getdate(add_days(now(), -30))
    if not to_date:
        to_date = getdate(now())
    
    # Get student analytics
    analytics_data = get_student_time_analytics(
        student=student,
        course=course,
        from_date=from_date,
        to_date=to_date
    )
    
    # Calculate summary stats
    total_time = sum(item["total_active_time"] for item in analytics_data)
    active_students = len(set(item["member"] for item in analytics_data))
    
    # Get completion data
    completion_data = []
    if course:
        completion_filters = {"course": course}
    else:
        completion_filters = {}
    
    if student:
        completion_filters["member"] = student
    
    enrollments = frappe.get_all(
        "LMS Enrollment",
        filters=completion_filters,
        fields=["name", "course", "member", "progress"]
    )
    
    completion_rates = [cint(e.progress) for e in enrollments]
    avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
    
    # Prepare response
    summary = {
        "totalTime": total_time,
        "activeStudents": active_students,
        "avgCompletionRate": round(avg_completion_rate, 1),
        "avgTimePerStudent": total_time / active_students if active_students > 0 else 0
    }
    
    # Enrich analytics data with completion percentage
    for item in analytics_data:
        for e in enrollments:
            if e.course == item["course"] and e.member == item["member"]:
                item["completion"] = cint(e.progress)
                break
        else:
            item["completion"] = 0
    
    return {
        "summary": summary,
        "data": analytics_data
    }


@frappe.whitelist()
def get_course_analytics(course, from_date=None, to_date=None):
    """Get analytics data for a specific course."""
    if not frappe.has_permission("LMS Course", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Check if user has permission to view this course
    if frappe.has_role("Course Creator") and not frappe.has_role("System Manager"):
        course_owner = frappe.db.get_value("LMS Course", course, "owner")
        if course_owner != frappe.session.user:
            frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Set default date range if not provided
    if not from_date:
        from_date = getdate(add_days(now(), -30))
    if not to_date:
        to_date = getdate(now())
    
    return get_course_time_analytics(course, from_date, to_date)


@frappe.whitelist()
def get_student_analytics(student, course=None):
    """Get analytics data for a specific student."""
    if not frappe.has_permission("LMS Course", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Check if user is viewing their own data or has admin rights
    is_self = student == frappe.session.user
    is_admin = frappe.has_role("System Manager") or frappe.has_role("Moderator")
    is_course_admin = False
    
    if course and frappe.has_role("Course Creator"):
        course_owner = frappe.db.get_value("LMS Course", course, "owner")
        is_course_admin = course_owner == frappe.session.user
    
    if not (is_self or is_admin or is_course_admin):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    return get_student_course_analytics(student, course)


@frappe.whitelist()
def export_analytics_csv(from_date=None, to_date=None, course=None, student=None):
    """Export analytics data as CSV."""
    if not frappe.has_permission("LMS Course", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    # Get analytics data
    analytics_data = get_student_time_analytics(
        student=student,
        course=course,
        from_date=from_date,
        to_date=to_date
    )
    
    # Prepare CSV data
    f = io.StringIO()
    writer = csv.writer(f)
    
    # Write header
    writer.writerow([
        "Student", "Student Name", "Course", "Course Name", 
        "Time Spent (seconds)", "Time Spent (hours)", "Sessions", 
        "Days Active", "Completion %"
    ])
    
    # Write data rows
    for item in analytics_data:
        writer.writerow([
            item["member"],
            item["member_name"],
            item["course"],
            item["course_name"],
            item["total_active_time"],
            round(item["total_active_time"] / 3600, 2),
            item["total_sessions"],
            item["days_active"],
            item.get("completion", 0)
        ])
    
    # Prepare response
    f.seek(0)
    frappe.response["result"] = f.read()
    frappe.response["type"] = "csv"
    frappe.response["doctype"] = "LMS-Analytics-Export"
    
    return Response(
        frappe.response["result"],
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=lms_analytics.csv"
        }
    )
