# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSLearningSession(Document):
    def validate(self):
        """Validate session data."""
        if not self.session_id:
            self.session_id = frappe.generate_hash(length=16)
        
        if not self.member_name and self.member:
            self.member_name = frappe.db.get_value("User", self.member, "full_name")
        
        if not self.course_name and self.course:
            self.course_name = frappe.db.get_value("LMS Course", self.course, "title")
        
        if not self.chapter_name and self.chapter:
            self.chapter_name = frappe.db.get_value("Course Chapter", self.chapter, "title")
        
        if not self.lesson_name and self.lesson:
            self.lesson_name = frappe.db.get_value("Course Lesson", self.lesson, "title")
    
    def on_update(self):
        """Update related records when session is updated."""
        if self.end_time and self.active_time:
            # Update LMS Course Progress with time info
            self.update_course_progress()
    
    def update_course_progress(self):
        """Update course progress with time information."""
        filters = {
            "member": self.member,
            "course": self.course
        }
        
        if self.lesson:
            filters["lesson"] = self.lesson
        
        progress_records = frappe.get_all(
            "LMS Course Progress",
            filters=filters,
            fields=["name", "total_active_time"]
        )
        
        for record in progress_records:
            current_time = record.get("total_active_time") or 0
            frappe.db.set_value(
                "LMS Course Progress",
                record.name,
                {
                    "total_active_time": current_time + self.active_time,
                    "last_active": frappe.utils.now()
                }
            )
