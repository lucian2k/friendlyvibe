"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from tasks import _extract_youtube_id, check_video

class TasksMethodsTest(TestCase):
    def test_extract_youtube_id(self):
        """
        Tests that the ID is correctly extracted from various Youtube links
        """
        self.assertEqual(_extract_youtube_id('http://youtu.be/WBKnpyoFEBo'), 'WBKnpyoFEBo')
        self.assertEqual(_extract_youtube_id('https://www.youtube.com/watch?v=Fkked2Wgd1g'), 'Fkked2Wgd1g')

