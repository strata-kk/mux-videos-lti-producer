from django.test import TestCase

from muxltiproducer import openedx


class OpenedXTests(TestCase):
    def test_lti_context_openedx_pattern(self):
        course_id = "course-v1:org1+course1+run1"
        org, course, run = openedx.course_pattern_match(course_id)
        self.assertEqual("org1", org)
        self.assertEqual("course1", course)
        self.assertEqual("run1", run)
