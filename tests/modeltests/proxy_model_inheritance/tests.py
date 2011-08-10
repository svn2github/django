"""
XX. Proxy model inheritance

Proxy model inheritance across apps can result in syncdb not creating the table
for the proxied model (as described in #12286).  This test creates two dummy
apps and calls syncdb, then verifies that the table has been created.
"""

import os
import sys

from django.conf import settings
from django.core.management import call_command
from django.db.models.loading import load_app
from django.test import TransactionTestCase
from django.test.utils import override_settings

# @override_settings(INSTALLED_APPS=('app1', 'app2'))
class ProxyModelInheritanceTests(TransactionTestCase):

    def setUp(self):
        self.old_sys_path = sys.path[:]
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        map(load_app, settings.INSTALLED_APPS)

    def tearDown(self):
        sys.path = self.old_sys_path

    def test_table_exists(self):
        call_command('syncdb', verbosity=0)
        global ProxyModel, NiceModel
        from app1.models import ProxyModel
        from app2.models import NiceModel
        self.assertEqual(NiceModel.objects.all().count(), 0)
        self.assertEqual(ProxyModel.objects.all().count(), 0)

ProxyModelInheritanceTests = override_settings(INSTALLED_APPS=('app1', 'app2'))(ProxyModelInheritanceTests)
