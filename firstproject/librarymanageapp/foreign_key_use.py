from django.db import models 
from django.contrib.auth.models import User
from datetime import datetime,timedelta
from librarymanageapp.models import Book

class IssuedBook(models.Model):
    student_id = models.ForeignKey(User) 
    book_id = models.ForeignKey(Book)
    issued_date = models.DateField(auto_now=True)
    to_be_return_date = models.DateField(default=to_be_return_date)
    fine=models.IntegerField()
    return_date=models.DateField(default=None)
    pending_request=models.BooleanField(default=False)

def to_be_return_date():
    return datetime.today() + timedelta(days=15)