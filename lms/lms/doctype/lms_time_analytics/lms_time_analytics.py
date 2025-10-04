# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSTimeAnalytics(Document):
    def validate(self):
        """Validate time analytics data."""
        if not self.member_name and self.member:
            self.member_name = frappe.db.get_value("User", self.member, "full_name")
        
        if not self.course_name and self.course:
            self.course_name = frappe.db.get_value("LMS Course", self.course, "title")
        
        if not self.chapter_name and self.chapter:
            self.chapter_name = frappe.db.get_value("Course Chapter", self.chapter, "title")
        
        if not self.lesson_name and self.lesson:
            self.lesson_name = frappe.db.get_value("Course Lesson", self.lesson, "title")
        
        if not self.date:
            self.date = frappe.utils.today()
    
    @staticmethod
    def get_stats(filters=None):
        """Get aggregated statistics based on filters."""
        if not filters:
            filters = {}
        
        # Build query filters
        query_filters = {}
        for key, value in filters.items():
            if key in ["member", "course", "chapter", "lesson", "date"]:
                query_filters[key] = value
        
        # Get aggregated data
        result = frappe.db.sql("""
            SELECT 
                SUM(active_time) as total_active_time,
                SUM(sessions_count) as total_sessions,
                COUNT(DISTINCT date) as days_active,
                COUNT(DISTINCT member) as unique_students
            FROM `tabLMS Time Analytics`
            WHERE {conditions}
        """.format(
            conditions = " AND ".join([f"{key} = %s" for key in query_filters.keys()]) or "1=1"
        ), tuple(query_filters.values()), as_dict=True)
        
        return result[0] if result else {
            "total_active_time": 0,
            "total_sessions": 0,
            "days_active": 0,
            "unique_students": 0
        }
