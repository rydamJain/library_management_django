from django.urls import path
from . import views
from django.core.exceptions import ViewDoesNotExist
# from django.contrib.auth.views import LogoutView

try:
    urlpatterns=[
    path('', views.home),
    path('loginpage', views.loginpage, name="loginpage"),
    path('logoutpage', views.logout, name="logoutpage"),
    path('register', views.register, name="register"),
    path('user', views.user_details, name="user"),
    path('returnbook', views.return_book, name="returnbook"),
    path('addbook', views.add_book, name="addbook"),
    path('requests', views.generate_book_requests),
    path('reject', views.reject),
    path('deletebook', views.delete_book,name="deletebook"),
    path('deleteuser', views.delete_user),
    path('issuebook', views.issue_book),
    path('adminissuebook', views.admin_issue_book),
    path('viewbooks', views.view_books),
    path('payfine', views.pay_fine),
    path('instructions', views.instructions, name="instruct"),
    path('search',views.search_books),
    path('view-issued-books', views.view_issued_books),
    path('view-return-books', views.view_return_books),
]
except ViewDoesNotExist:
    print('The View does not exist in views.py')
    