# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSLearningHeartbeat(Document):
    def validate(self):
        """Validate heartbeat data."""
        if not self.timestamp:
            self.timestamp = frappe.utils.now()
        
        # Ensure unit_type is valid
        if self.unit_type not in ["course", "chapter", "lesson"]:
            frappe.throw("Invalid unit type. Must be one of: course, chapter, lesson")
        
        # Validate unit_id based on unit_type
        if self.unit_type == "course":
            if not frappe.db.exists("LMS Course", self.unit_id):
                frappe.throw(f"Course {self.unit_id} does not exist")
        elif self.unit_type == "chapter":
            if not frappe.db.exists("Course Chapter", self.unit_id):
                frappe.throw(f"Chapter {self.unit_id} does not exist")
        elif self.unit_type == "lesson":
            if not frappe.db.exists("Course Lesson", self.unit_id):
                frappe.throw(f"Lesson {self.unit_id} does not exist")
