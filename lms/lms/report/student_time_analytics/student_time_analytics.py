# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint

from lms.lms.analytics import get_student_time_analytics

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "member",
            "fieldtype": "Link",
            "label": _("Student"),
            "options": "User",
            "width": 150
        },
        {
            "fieldname": "member_name",
            "fieldtype": "Data",
            "label": _("Student Name"),
            "width": 150
        },
        {
            "fieldname": "course",
            "fieldtype": "Link",
            "label": _("Course"),
            "options": "LMS Course",
            "width": 150
        },
        {
            "fieldname": "course_name",
            "fieldtype": "Data",
            "label": _("Course Name"),
            "width": 200
        },
        {
            "fieldname": "total_active_time",
            "fieldtype": "Duration",
            "label": _("Total Time Spent"),
            "width": 150
        },
        {
            "fieldname": "days_active",
            "fieldtype": "Int",
            "label": _("Days Active"),
            "width": 100
        },
        {
            "fieldname": "total_sessions",
            "fieldtype": "Int",
            "label": _("Total Sessions"),
            "width": 120
        },
        {
            "fieldname": "avg_session_time",
            "fieldtype": "Duration",
            "label": _("Avg. Session Time"),
            "width": 150
        },
        {
            "fieldname": "completion",
            "fieldtype": "Percent",
            "label": _("Completion %"),
            "width": 120
        }
    ]

def get_data(filters):
    data = get_student_time_analytics(
        student=filters.get("student"),
        course=filters.get("course"),
        from_date=filters.get("from_date"),
        to_date=filters.get("to_date")
    )
    
    # Enrich with completion data
    for row in data:
        # Get completion percentage
        progress = frappe.db.get_value(
            "LMS Enrollment",
            {"course": row["course"], "member": row["member"]},
            "progress"
        )
        row["completion"] = cint(progress or 0)
        
        # Calculate average session time
        if row["total_sessions"] > 0:
            row["avg_session_time"] = row["total_active_time"] / row["total_sessions"]
        else:
            row["avg_session_time"] = 0
    
    return data

def get_chart(data):
    if not data:
        return None
    
    labels = []
    time_values = []
    completion_values = []
    
    # Take top 10 entries by time spent
    sorted_data = sorted(data, key=lambda x: x["total_active_time"], reverse=True)[:10]
    
    for row in sorted_data:
        labels.append(f"{row['member_name']} - {row['course_name']}")
        time_values.append(row["total_active_time"] / 3600)  # Convert to hours
        completion_values.append(row["completion"])
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Time Spent (hours)",
                    "values": time_values
                },
                {
                    "name": "Completion %",
                    "values": completion_values
                }
            ]
        },
        "type": "bar",
        "colors": ["#7cd6fd", "#5e64ff"]
    }
