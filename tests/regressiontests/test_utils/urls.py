from django.conf.urls import patterns

import views


urlpatterns = patterns('',
    (r'^test_utils/get_person/(\d+)/$', views.get_person),
)
