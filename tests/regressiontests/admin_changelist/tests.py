from __future__ import with_statement, absolute_import

from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ChangeList, SEARCH_VAR, ALL_VAR
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase
from django.test.client import RequestFactory

from .admin import (ChildAdmin, QuartetAdmin, BandAdmin, ChordsBandAdmin,
    GroupAdmin, ParentAdmin, DynamicListDisplayChildAdmin,
    DynamicListDisplayLinksChildAdmin, CustomPaginationAdmin,
    FilteredChildAdmin, CustomPaginator, site as custom_site)
from .models import (Child, Parent, Genre, Band, Musician, Group, Quartet,
    Membership, ChordsMusician, ChordsBand, Invitation)


class ChangeListTests(TestCase):
    urls = "regressiontests.admin_changelist.urls"

    def setUp(self):
        self.factory = RequestFactory()

    def test_select_related_preserved(self):
        """
        Regression test for #10348: ChangeList.get_query_set() shouldn't
        overwrite a custom select_related provided by ModelAdmin.queryset().
        """
        m = ChildAdmin(Child, admin.site)
        request = self.factory.get('/child/')
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m)
        self.assertEqual(cl.query_set.query.select_related, {'parent': {'name': {}}})

    def test_result_list_empty_changelist_value(self):
        """
        Regression test for #14982: EMPTY_CHANGELIST_VALUE should be honored
        for relationship fields
        """
        new_child = Child.objects.create(name='name', parent=None)
        request = self.factory.get('/child/')
        m = ChildAdmin(Child, admin.site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, Child, list_display, list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        template = Template('{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}')
        context = Context({'cl': cl})
        table_output = template.render(context)
        row_html = '<tbody><tr class="row1"><th><a href="%d/">name</a></th><td class="nowrap">(None)</td></tr></tbody>' % new_child.id
        self.assertFalse(table_output.find(row_html) == -1,
            'Failed to find expected row element: %s' % table_output)

    def test_result_list_html(self):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        new_parent = Parent.objects.create(name='parent')
        new_child = Child.objects.create(name='name', parent=new_parent)
        request = self.factory.get('/child/')
        m = ChildAdmin(Child, admin.site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, Child, list_display, list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        template = Template('{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}')
        context = Context({'cl': cl})
        table_output = template.render(context)
        row_html = '<tbody><tr class="row1"><th><a href="%d/">name</a></th><td class="nowrap">Parent object</td></tr></tbody>' % new_child.id
        self.assertFalse(table_output.find(row_html) == -1,
            'Failed to find expected row element: %s' % table_output)

    def test_result_list_editable_html(self):
        """
        Regression tests for #11791: Inclusion tag result_list generates a
        table and this checks that the items are nested within the table
        element tags.
        Also a regression test for #13599, verifies that hidden fields
        when list_editable is enabled are rendered in a div outside the
        table.
        """
        new_parent = Parent.objects.create(name='parent')
        new_child = Child.objects.create(name='name', parent=new_parent)
        request = self.factory.get('/child/')
        m = ChildAdmin(Child, admin.site)

        # Test with list_editable fields
        m.list_display = ['id', 'name', 'parent']
        m.list_display_links = ['id']
        m.list_editable = ['name']
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m)
        FormSet = m.get_changelist_formset(request)
        cl.formset = FormSet(queryset=cl.result_list)
        template = Template('{% load admin_list %}{% spaceless %}{% result_list cl %}{% endspaceless %}')
        context = Context({'cl': cl})
        table_output = template.render(context)
        # make sure that hidden fields are in the correct place
        hiddenfields_div = '<div class="hiddenfields"><input type="hidden" name="form-0-id" value="%d" id="id_form-0-id" /></div>' % new_child.id
        self.assertFalse(table_output.find(hiddenfields_div) == -1,
            'Failed to find hidden fields in: %s' % table_output)
        # make sure that list editable fields are rendered in divs correctly
        editable_name_field = '<input name="form-0-name" value="name" class="vTextField" maxlength="30" type="text" id="id_form-0-name" />'
        self.assertFalse('<td>%s</td>' % editable_name_field == -1,
            'Failed to find "name" list_editable field in: %s' % table_output)

    def test_result_list_editable(self):
        """
        Regression test for #14312: list_editable with pagination
        """

        new_parent = Parent.objects.create(name='parent')
        for i in range(200):
            new_child = Child.objects.create(name='name %s' % i, parent=new_parent)
        request = self.factory.get('/child/', data={'p': -1})  # Anything outside range
        m = ChildAdmin(Child, admin.site)

        # Test with list_editable fields
        m.list_display = ['id', 'name', 'parent']
        m.list_display_links = ['id']
        m.list_editable = ['name']
        self.assertRaises(IncorrectLookupParameters, lambda: \
            ChangeList(request, Child, m.list_display, m.list_display_links,
                    m.list_filter, m.date_hierarchy, m.search_fields,
                    m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m))

    def test_custom_paginator(self):
        new_parent = Parent.objects.create(name='parent')
        for i in range(200):
            new_child = Child.objects.create(name='name %s' % i, parent=new_parent)

        request = self.factory.get('/child/')
        m = CustomPaginationAdmin(Child, admin.site)

        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all, m.list_editable, m)

        cl.get_results(request)
        self.assertIsInstance(cl.paginator, CustomPaginator)

    def test_distinct_for_m2m_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't apper more than once. Basic ManyToMany.
        """
        blues = Genre.objects.create(name='Blues')
        band = Band.objects.create(name='B.B. King Review', nr_of_members=11)

        band.genres.add(blues)
        band.genres.add(blues)

        m = BandAdmin(Band, admin.site)
        request = self.factory.get('/band/', data={'genres': blues.pk})

        cl = ChangeList(request, Band, m.list_display,
                m.list_display_links, m.list_filter, m.date_hierarchy,
                m.search_fields, m.list_select_related, m.list_per_page,
                m.list_max_show_all, m.list_editable, m)

        cl.get_results(request)

        # There's only one Group instance
        self.assertEqual(cl.result_count, 1)

    def test_distinct_for_through_m2m_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't apper more than once. With an intermediate model.
        """
        lead = Musician.objects.create(name='Vox')
        band = Group.objects.create(name='The Hype')
        Membership.objects.create(group=band, music=lead, role='lead voice')
        Membership.objects.create(group=band, music=lead, role='bass player')

        m = GroupAdmin(Group, admin.site)
        request = self.factory.get('/group/', data={'members': lead.pk})

        cl = ChangeList(request, Group, m.list_display,
                m.list_display_links, m.list_filter, m.date_hierarchy,
                m.search_fields, m.list_select_related, m.list_per_page,
                m.list_max_show_all, m.list_editable, m)

        cl.get_results(request)

        # There's only one Group instance
        self.assertEqual(cl.result_count, 1)

    def test_distinct_for_inherited_m2m_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't apper more than once. Model managed in the
        admin inherits from the one that defins the relationship.
        """
        lead = Musician.objects.create(name='John')
        four = Quartet.objects.create(name='The Beatles')
        Membership.objects.create(group=four, music=lead, role='lead voice')
        Membership.objects.create(group=four, music=lead, role='guitar player')

        m = QuartetAdmin(Quartet, admin.site)
        request = self.factory.get('/quartet/', data={'members': lead.pk})

        cl = ChangeList(request, Quartet, m.list_display,
                m.list_display_links, m.list_filter, m.date_hierarchy,
                m.search_fields, m.list_select_related, m.list_per_page,
                m.list_max_show_all, m.list_editable, m)

        cl.get_results(request)

        # There's only one Quartet instance
        self.assertEqual(cl.result_count, 1)

    def test_distinct_for_m2m_to_inherited_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't apper more than once. Target of the relationship
        inherits from another.
        """
        lead = ChordsMusician.objects.create(name='Player A')
        three = ChordsBand.objects.create(name='The Chords Trio')
        Invitation.objects.create(band=three, player=lead, instrument='guitar')
        Invitation.objects.create(band=three, player=lead, instrument='bass')

        m = ChordsBandAdmin(ChordsBand, admin.site)
        request = self.factory.get('/chordsband/', data={'members': lead.pk})

        cl = ChangeList(request, ChordsBand, m.list_display,
                m.list_display_links, m.list_filter, m.date_hierarchy,
                m.search_fields, m.list_select_related, m.list_per_page,
                m.list_max_show_all, m.list_editable, m)

        cl.get_results(request)

        # There's only one ChordsBand instance
        self.assertEqual(cl.result_count, 1)

    def test_distinct_for_non_unique_related_object_in_list_filter(self):
        """
        Regressions tests for #15819: If a field listed in list_filters
        is a non-unique related object, distinct() must be called.
        """
        parent = Parent.objects.create(name='Mary')
        # Two children with the same name
        Child.objects.create(parent=parent, name='Daniel')
        Child.objects.create(parent=parent, name='Daniel')

        m = ParentAdmin(Parent, admin.site)
        request = self.factory.get('/parent/', data={'child__name': 'Daniel'})

        cl = ChangeList(request, Parent, m.list_display, m.list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)

        # Make sure distinct() was called
        self.assertEqual(cl.query_set.count(), 1)

    def test_distinct_for_non_unique_related_object_in_search_fields(self):
        """
        Regressions tests for #15819: If a field listed in search_fields
        is a non-unique related object, distinct() must be called.
        """
        parent = Parent.objects.create(name='Mary')
        Child.objects.create(parent=parent, name='Danielle')
        Child.objects.create(parent=parent, name='Daniel')

        m = ParentAdmin(Parent, admin.site)
        request = self.factory.get('/parent/', data={SEARCH_VAR: 'daniel'})

        cl = ChangeList(request, Parent, m.list_display, m.list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)

        # Make sure distinct() was called
        self.assertEqual(cl.query_set.count(), 1)

    def test_pagination(self):
        """
        Regression tests for #12893: Pagination in admins changelist doesn't
        use queryset set by modeladmin.
        """
        parent = Parent.objects.create(name='anything')
        for i in range(30):
            Child.objects.create(name='name %s' % i, parent=parent)
            Child.objects.create(name='filtered %s' % i, parent=parent)

        request = self.factory.get('/child/')

        # Test default queryset
        m = ChildAdmin(Child, admin.site)
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all,
                m.list_editable, m)
        self.assertEqual(cl.query_set.count(), 60)
        self.assertEqual(cl.paginator.count, 60)
        self.assertEqual(cl.paginator.page_range, [1, 2, 3, 4, 5, 6])

        # Test custom queryset
        m = FilteredChildAdmin(Child, admin.site)
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, m.list_max_show_all,
                m.list_editable, m)
        self.assertEqual(cl.query_set.count(), 30)
        self.assertEqual(cl.paginator.count, 30)
        self.assertEqual(cl.paginator.page_range, [1, 2, 3])

    def test_dynamic_list_display(self):
        """
        Regression tests for #14206: dynamic list_display support.
        """
        parent = Parent.objects.create(name='parent')
        for i in range(10):
            Child.objects.create(name='child %s' % i, parent=parent)

        user_noparents = User.objects.create(
            username='noparents',
            is_superuser=True)
        user_parents = User.objects.create(
            username='parents',
            is_superuser=True)

        def _mocked_authenticated_request(user):
            request = self.factory.get('/child/')
            request.user = user
            return request

        # Test with user 'noparents'
        m = custom_site._registry[Child]
        request = _mocked_authenticated_request(user_noparents)
        response = m.changelist_view(request)
        self.assertNotContains(response, 'Parent object')

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ['name', 'age'])
        self.assertEqual(list_display_links, ['name'])

        # Test with user 'parents'
        m = DynamicListDisplayChildAdmin(Child, admin.site)
        request = _mocked_authenticated_request(user_parents)
        response = m.changelist_view(request)
        self.assertContains(response, 'Parent object')

        custom_site.unregister(Child)

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ('parent', 'name', 'age'))
        self.assertEqual(list_display_links, ['parent'])

        # Test default implementation
        custom_site.register(Child, ChildAdmin)
        m = custom_site._registry[Child]
        request = _mocked_authenticated_request(user_noparents)
        response = m.changelist_view(request)
        self.assertContains(response, 'Parent object')

    def test_show_all(self):
        parent = Parent.objects.create(name='anything')
        for i in range(30):
            Child.objects.create(name='name %s' % i, parent=parent)
            Child.objects.create(name='filtered %s' % i, parent=parent)

        # Add "show all" parameter to request
        request = self.factory.get('/child/', data={ALL_VAR: ''})

        # Test valid "show all" request (number of total objects is under max)
        m = ChildAdmin(Child, admin.site)
        # 200 is the max we'll pass to ChangeList
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, 200, m.list_editable, m)
        cl.get_results(request)
        self.assertEqual(len(cl.result_list), 60)

        # Test invalid "show all" request (number of total objects over max)
        # falls back to paginated pages
        m = ChildAdmin(Child, admin.site)
        # 30 is the max we'll pass to ChangeList for this test
        cl = ChangeList(request, Child, m.list_display, m.list_display_links,
                m.list_filter, m.date_hierarchy, m.search_fields,
                m.list_select_related, m.list_per_page, 30, m.list_editable, m)
        cl.get_results(request)
        self.assertEqual(len(cl.result_list), 10)

    def test_dynamic_list_display_links(self):
        """
        Regression tests for #16257: dynamic list_display_links support.
        """
        parent = Parent.objects.create(name='parent')
        for i in range(1, 10):
            Child.objects.create(id=i, name='child %s' % i, parent=parent, age=i)

        superuser = User.objects.create(
            username='superuser',
            is_superuser=True)

        def _mocked_authenticated_request(user):
            request = self.factory.get('/child/')
            request.user = user
            return request

        m = DynamicListDisplayLinksChildAdmin(Child, admin.site)
        request = _mocked_authenticated_request(superuser)
        response = m.changelist_view(request)
        for i in range(1, 10):
            self.assertContains(response, '<a href="%s/">%s</a>' % (i, i))

        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        self.assertEqual(list_display, ('parent', 'name', 'age'))
        self.assertEqual(list_display_links, ['age'])