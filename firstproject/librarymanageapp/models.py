from django.db import models 
from datetime import datetime,timedelta

class Book(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.PositiveIntegerField()
    quantity= models.IntegerField()
    price = models.FloatField()
    category= models.CharField(max_length=100)

def to_be_return_date():
    return datetime.today() + timedelta(days=15)

class IssuedBook(models.Model):
    student_id = models.CharField(max_length=100) 
    book_id = models.PositiveIntegerField()
    book_name = models.CharField(max_length=200)
    issued_date = models.DateField(auto_now=True)
    to_be_return_date = models.DateField(default=to_be_return_date)
    fine=models.IntegerField()
    
class ReturnedBook(models.Model):
    student_id = models.CharField(max_length=100) 
    book_id = models.PositiveIntegerField()
    book_name=models.CharField(max_length=200)
    return_date = models.DateField(auto_now=True)
   
class PendingIssueRequest(models.Model):
    student_id = models.CharField(max_length=100) 
    book_id = models.PositiveIntegerField()
    book_name = models.CharField(max_length=200)
    fine=models.IntegerField()

    
    
    
