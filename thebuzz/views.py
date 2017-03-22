from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.forms import UserCreationForm
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.template import Context, loader
from .models import Post, Comment, Profile, Img, ListField 
from .forms import PostForm, CommentForm, ProfileForm
from django.core.urlresolvers import reverse
import CommonMark, imghdr
from django.db import transaction
from django.contrib.auth import logout
from django.views.generic.edit import DeleteView
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Q
import dateutil.parser
import json
import requests
from django.db.models import Lookup
from itertools import chain


#------------------------------------------------------------------
# SIGNING UP

def register(request):
    profileForm = ""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = make_password(form.cleaned_data['password1'], salt=None, hasher='default')
            user = User.objects.create(username=username, password=password)

            profile = Profile.objects.get(user_id=user.id)
            profileForm = ProfileForm(request.POST, instance=profile)
            profileForm.save()

            return HttpResponseRedirect('/register/complete')

    else:
        form = UserCreationForm()
        profileForm = ProfileForm()
    token = {}
    token.update(csrf(request))
    token['form'] = form
    token['profileForm'] = profileForm

    return render_to_response('registration/registration_form.html', token)

def registration_complete(request):
    return render_to_response('registration/registration_complete.html')

#for showing the home page/actually logging in
#3 ways to get here:
#-logged in
#-already logged in, used a cookie
#-registered
#edited code from here to log a user in (https://www.fir3net.com/Web-Development/Django/django.html)
@login_required(login_url = '/login/')
def homePage(request):
	 #if this person has just logged in
    if request.method == 'POST': #for testing purposes only
        
        # get the person i want to follow
        friend = User.objects.get(username = request.POST['befriend'])
        friend_profile = Profile.objects.get(pk=friend.id)

        # follow that person
        request.user.profile.follow(friend_profile)
        friend_profile.add_user_following_me(request.user.profile)

    users = User.objects.all() #for testing purposes only
    
    # get all the people I am currently following
    following = request.user.profile.get_all_following()

    # get all the people that are following me, that I am not friends with yet
    followers = request.user.profile.get_all_followers()

    friends = request.user.profile.get_all_friends()

    return render(request, 'friends/friends.html',{'users': users, 'following': following, 'followers': followers, 'friends': friends  })
		

	 #else: #change this later to account for the other 2 cases ******
	 #	return render_to_response('registration/login.html')

# END LOGIN VIEWS------------------------------------------------------------------------------------------

# PROFILE VIEWS
@login_required(login_url = '/login/')
def profile(request, profile_id):
    #profile_id = profile_id.replace('-', '')
    print "profile_id:" + str(profile_id)

    profile = Profile.objects.get(id=profile_id )
    

    return render(request, 'profile/profile.html', {'profile': profile} )



@login_required(login_url = '/login/')
@transaction.atomic
def edit_profile(request, profile_id):
    if request.method == 'POST':
	print 'Here'
	print profile_id
        profile = Profile.objects.get(id =profile_id) #user_id=request.user.id)
        form = ProfileForm(request.POST, instance=profile)
        form.save()

        return render(request, 'profile/profile.html', {'profile': profile} ) #redirect('profile')
    else:
	print 'here instead'
	print profile_id
        profile = Profile.objects.get(id = profile_id ) #user_id=request.user.id)
        form = ProfileForm(instance=profile)

    return render(request, 'profile/edit_profile_form.html', {'form': form})
# END PROFILE VIEWS



# ------------ FRIENDS VIEWS ---------------------
def friends (request):
        if request.method == 'POST': #for testing purposes only

            # get the person i want to follow
            friend = User.objects.get(username = request.POST['befriend'])
            print "friend id: " + str(friend.id)
            friend_profile = Profile.objects.get(user_id=friend.id)

            # follow that person
            request.user.profile.follow(friend_profile)
            friend_profile.add_user_following_me(request.user.profile)

        users = User.objects.all() #for testing purposes only

        # get all the people I am currently following
        following = request.user.profile.get_all_following()

        # get all the people that are following me, that I am not friends with yet
        followers = request.user.profile.get_all_followers()

        friends = request.user.profile.get_all_friends()

        return render(request, 'friends/friends.html',{'users': users, 'following': following, 'followers': followers, 'friends': friends  })

def add_friends (request):
    if request.method == 'POST':
        #TODO: Retrieve form data and save to model
        return redirect('friends')
    else:
        #TODO: Retrieve set correct form
        form = ""

    return render(request, 'profile/edit_profile_form.html', {'form': form})

def delete_friend (request, profile_id):

    friend = Profile.objects.get(pk=profile_id)
    request.user.profile.unfriend(friend)
    return HttpResponseRedirect(reverse('friends'))

# ----------- END FRIENDS VIEWS -------------



# POSTS AND COMMENTS
#parts of code from http://pythoncentral.io/writing-simple-views-for-your-first-python-django-application/
@login_required(login_url = '/login/')
def posts(request):
    two_days_ago = datetime.utcnow() - timedelta(days=2)

    post_list = []

    author = request.user.profile
    
    #a = User.objects.get(pk=author.user.id)

    # get all public posts
    posts = Post.objects.all().exclude(visibility__in=['PRIVATE', 'FRIENDS', 'FOAF'])
    print("POSTS: " + str(posts))
    for post in posts:
        post_list.append(post)

    # get all my private posts
    posts = Post.objects.filter(associated_author=author)
    for post in posts:
        post_list.append(post)

    # get friends post of friends
    friends  = author.get_all_friends()
    if len(friends) > 0:
        for friend in friends:
            # get all posts for friends
            # get all posts of the friend that are not private
            posts = Post.objects.filter(associated_author=friend.id).exclude(visibility='PRIVATE')

            for post in posts:
                post_list.append(post)


            # get all posts for friends of friends
            foafs = friend.get_all_friends()
            if len(foafs) > 0:
                for foaf in foafs:
                    # get all posts of the foaf that are not private or only for friends
                    foaf_posts = Post.objects.filter(associated_author=foaf.id).exclude(visibility__in=['PRIVATE', 'FRIENDS'])

                    for foaf_post in foaf_posts:
                        post_list.append(foaf_post)

	    
        


	#possible_posts_list = Post.objects.filter(visibility__exact='PUBLIC').all() | ( Post.objects.filter(visibility__exact='PRIVATE').all() & Post.objects.filter(associated_author__exact=request.user).all() ) | Post.objects.filter(visibleTo__contains=request.user)


	#template = loader.get_template('index.html')

    
    createGithubPosts(author)

    context = {}

    context = {
        'post_list': set(post_list) # make sure values in list are distinct     
    }

    #print "post_list: " + str(post_list)

    return render(request, 'posts/posts.html', context)



def createGithubPosts(user):
#get github activity of myself - and create posts to store in the database.....create a seperate function for this and have it called??
    #make a GET request to github for my github name, if I have one
    if(user.github != ''):

	#first get the most recent github post, so we can stop if we hit this time or later
	postQuery = Post.objects.filter(title = "Github Activity", associated_author = user).order_by('-published').first()

	#print postQuery.published

        rurl = 'https://api.github.com/users/' + user.github + '/events'
        resp = requests.get(rurl) #gets newest to oldest events
	jdata = resp.json()
	#print jdata[0]
	avatars = []
	gtitle = "Github Activity"
	contents = []
	pubtime = []
	#print (jdata[0]['payload'])
	count = 0
	#get the data
        for item in jdata:
	        
	    if(postQuery is not None):
		    cmpareDate = dateutil.parser.parse(item['created_at'])
	            #print cmpareDate
		    #print " compare "
		    #print postQuery.published	
		    if(cmpareDate<=postQuery.published): #is the latest github post newer than the retrieved ones?dont create duplicates
                        #print "continue"
			continue

            avatars.append(item['actor']['avatar_url']) #TODO:implement this after images with text is fixed
	    pubtime.append(item['created_at'])

	    if( "commits" in item['payload'] ):
	    #if there is commit data
		    contents.append(item['type'] + " by " + item['actor']['display_login'] +" (" + item['payload']['commits'][0]['author']['email'] + ")" + " in <a href = 'https://github.com/" + item['repo']['name'] + "'> " + item['repo']['name'] + "</a> <br/> \"" + item['payload']['commits'][0]['message'] + "\"")
	 #           count += 1
	    else:
	    #there is no commit data
		    contents.append(item['type'] + " by " + item['actor']['display_login'] + " in <a href = 'https://github.com/" + item['repo']['name'] + "'> " + item['repo']['name'] + "</a> <br/>")
	#            count += 1

        #print count

	#make posts for the database
	for i in range(0,len(contents)):
	    lilavatar = "<img src='" + avatars[i] + "'/>"
	    
	    post = Post.objects.create(title = gtitle,
                                       content= lilavatar + "<p>" + contents[i] , 
                                       published=pubtime[i],
				       associated_author = user,
				       source = 'http://127.0.0.1:8000/',#request.META.get('HTTP_REFERER'), TODO: fix me
				       origin = 'huh',
				       description = contents[i][0:97] + '...',
				       visibility = 'PUBLIC',
				       visibleTo = '',
                                       ) 
            myImg = Img.objects.create(associated_post = post,
					 myImg = lilavatar )
                     


#code from http://pythoncentral.io/writing-simple-views-for-your-first-python-django-application/
@login_required(login_url = '/login/')
def post_detail(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        # If no Post has id post_id, we raise an HTTP 404 error.
        raise Http404

    try :
        comments  = Comment.objects.filter(associated_post=post_id)
    except Comment.DoesNotExist:
        comments = Comment.objects

    displayName = Profile.objects.get(id=post.associated_author.id).displayName
    return render(request, 'posts/detail.html', {'post': post, 'comments': comments, 'post_author': displayName})


@login_required(login_url = '/login/')
def add_comment(request, post_id):

    post = get_object_or_404(Post, pk=post_id)
    author = Profile.objects.get(user_id=request.user.id)

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.content = form.cleaned_data['content']
            comment.author = Profile.objects.get(pk=author.id)
            comment.associated_post = post
            comment.date_created = timezone.now()
            comment.save()


            return HttpResponseRedirect(reverse('post_detail', kwargs={'post_id': str(post.id) }))
    else:
        form = CommentForm()

    return render(request, 'posts/add_comment.html', {'form': form, 'post': post})


#code from http://pythoncentral.io/how-to-use-python-django-forms/
#CommonMark code help from: https://pypi.python.org/pypi/CommonMark
@login_required(login_url = '/login/')
def post_form_upload(request):
    if request.method == 'GET':
        form = PostForm()
	print 'am I here?'
    else:
        # A POST request: Handle Form Upload
        form = PostForm(request.POST, request.FILES) # Bind data from request.POST into a PostForm
	print 'or am i here?'

	parser = CommonMark.Parser()
	renderer = CommonMark.HtmlRenderer()

        # If data is valid, proceeds to create a new post and redirect the user
        if form.is_valid():
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
	    ast = parser.parse(content)
	    html = renderer.render(ast)
            published = timezone.now()
	    image = form.cleaned_data['image_upload']
	    visibility = form.cleaned_data['choose_Post_Visibility']
	    visible_to = ''#[]

	    if(visibility == 'PRIVATE'):
	      #glean the users by commas for now
	      entries = form.cleaned_data['privacy_textbox']
	      #visible_to = form.cleaned_data['privacy_textbox']
	      entries = entries.split(',')

	      for item in entries:
		visible_to += item
                #visible_to.append(item)


	    if image:
	      #create Posts and Img objects here!
	      #cType = imghdr.what(image.name)
	      #if(cType == 'png'):
	      #  contentType = 'image/png;base64'
	      #elif(cType == 'jpeg'):
	      #	contentType = 'image/jpeg;base64'
	      imgItself = "<img src=\'" + "/images/" + image.name + "\'/>"
              post = Post.objects.create(title = title,
                                       content=html + "<p>" + imgItself,
                                       published=published,
				       associated_author = request.user,
				       source = request.META.get('HTTP_REFERER'),
				       origin = 'huh',
				       description = content[0:97] + '...',
				       visibility = visibility,
				       visibleTo = visible_to,
                                       ) #json.dumps(visible_to)
              myImg = Img.objects.create(associated_post = post,
					 myImg = image )
	      #can't make a whole new post for images, will look funny. Try this??

	    else:
	      #create a Post without an image here!
	      post = Post.objects.create(title = title,
                                       content=html ,
                                       published=published,
				       associated_author = request.user.profile,
				       source = request.META.get('HTTP_REFERER'),
				       origin = 'huh',
				       description = content[0:97] + '...',
				       visibility = visibility,
				       visibleTo = visible_to,
                                       ) #json.dumps(visible_to)

	    return HttpResponseRedirect(reverse('post_detail',
                                                kwargs={'post_id': str(post.id) }))

    return render(request, 'posts/post_form_upload.html', {
        'form': form,
    })

#again parts of code from
#http://pythoncentral.io/writing-views-to-upload-posts-for-your-first-python-django-application/
# NOT WORKING
def post_upload(request):
	if request.method =='GET':

		two_days_ago = datetime.utcnow() - timedelta(days=2)

		latest_posts_list = Post.objects.filter(date_created__gt=two_days_ago).all()

		#template = loader.get_template('index.html')

		context = {

		'post_upload': latest_posts_list

		}

		return render(request, 'posts/post_form_upload.html', context)
	elif request.method == 'POST':
		#fix after GET is working...
		post = Post.objects.create(content=request.POST['posted_text'],
			date_created=datetime.utcnow() )
		return HttpResponseRedirect(reverse('post_detail', kwargs={'post_id': post.id}))

def DeletePost(request, post_id):
   post = get_object_or_404(Post, pk=post_id).delete()
   return HttpResponseRedirect(reverse('posts'))


# Based on http://www.django-rest-framework.org/tutorial/quickstart/
from rest_framework import viewsets
from .serializers import PostSerializer, CommentSerializer
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

# END POSTS AND COMMENTS


#CUSTOM QUERY STUFF ------------------------------------------------
#from django.db.models.fields import Field
#Field.register_lookup(Is_My_Friend)


#class Is_My_Friend(Lookup):
#    lookup_name = 'is_my_friend'

#    def as_sql(self, compiler, connection):
#        lhs, lhs_params = self.process_lhs(compiler, connection)
#        rhs, rhs_params = self.process_rhs(compiler, connection)
#        params = lhs_params + rhs_params
#        return '%s <> %s' % (lhs, rhs), params

#END OF CUSTOM QUERY STUFF -----------------------------------------

