from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


from router import router

urlpatterns = [
    # Examples:
    #url(r'^$', 'socialdistribution.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^posts/', include('posts.urls', namespace='posts')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^posts/(?P<post_id>\d+)/detail.html$', 'posts.views.post_detail', name='post_detail'),	

    url(r'^posts/form_upload.html$', 'posts.views.post_form_upload', name='post_form_upload'),

 
    url(r'^register/$', 'authors.views.register', name='register'),
    url(r'^register/complete/$', 'authors.views.registration_complete', name='registration_complete'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^home/$', 'authors.views.homePage', name='homePage'),
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),

    
    url(r'^posts/(?P<post_id>\d+)/add_comment.html$', 'posts.views.add_comment', name='add_comment'),
    
    url(r'^api/', include(router.urls))

]

