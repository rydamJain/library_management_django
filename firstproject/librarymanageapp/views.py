import os
from django.shortcuts import render,redirect
from django.contrib import messages,auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, JsonResponse
from librarymanageapp.customexceptions import *
from librarymanageapp.models import Book,IssuedBook,ReturnedBook,PendingIssueRequest
from datetime import datetime
import logging
import logging.handlers

logger = logging.getLogger(__name__)
def delete_logs():
    handler_to_delete_log = logging.handlers.RotatingFileHandler('debug.log', maxBytes=1000000, backupCount=5)
    logger.addHandler(handler_to_delete_log)
    if os.path.exists('debug.log'):
        with open('debug.log', 'r+') as file_object:
            lines = file_object.readlines()
            if len(lines) > 600:
                file_object.seek(0)
                file_object.truncate()

def fine_calculation(request):
    try:
        if not request:
            raise RequestNotFoundException("Request Data not found")
        books = IssuedBook.objects.filter(student_id = request.user.id)
        fine = 0
        try:
            if not books:
                raise BookNotFoundException("No Book Present")
            else:
                for book in books:
                    fine += book.fine
        except BookNotFoundException as error_msg :
            logger.exception(str(error_msg))
    except RequestNotFoundException as error_msg :
            logger.exception(str(error_msg))
            return HttpResponseBadRequest("No Internet Connection")
    return fine


def send_book_return_notification(request):
    issued_books = IssuedBook.objects.filter(student_id=request.user.id)
    current_date = datetime.today().date()
    try:
        if not issued_books:
            raise BookNotFoundException("No Book Present")
        else:
            for book in issued_books:  
                if (book.to_be_return_date <= current_date):
                    fine = (current_date - book.to_be_return_date).days * 5
                    message = 'This is a reminder that you have {} book due for return. Please return it at your earliest convenience. Your fine will be Rs{}.'.format(book.book_name, fine)
                    messages.warning(request, message)
                    book.fine = fine
                    book.save()
    except BookNotFoundException as error_msg :
        logger.exception(str(error_msg))
           
def search_books(request):
    query = request.GET.get('query_var', '')
    books = Book.objects.filter(name__icontains=query) | Book.objects.filter(author__icontains=query)
    results = []
    for book in books:
        results.append({'name': book.name, 'author': book.author})
    return JsonResponse({'results': results})

def loginpage(request):
    delete_logs()
    if request.method == 'POST':
        try:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username = username, password = password)
            if user is not None:
                login(request, user)
                send_book_return_notification(request)
                try:
                    fine = fine_calculation(request)
                    if fine is None:
                        raise FineCalculationException(search_error_message("fine_message"))
                except FineCalculationException as error_msg:
                    logger.exception("Fine calculation exception:%s", str(error_msg))
                    fine = error_msg.fine
                    raise RequestNotFoundException("no internet connection") 
                return render(request,'home.html',{"username":username,"fine":fine})
            else:
                logger.info("Incorrect credentials. Use correct credentials")
                messages.info(request,"Incorrect credentials")
        except RequestNotFoundException as error_message:
            logger.exception("Error occurred  during user login :%s", str(error_message))
            messages.error(request, str(error_message))
        return render(request,'loginpage.html')
    else:
        username = " "
        return render(request,'loginpage.html',{"username":username})

@login_required(login_url = loginpage)
def home(request):
    try:
        username = request.user.username
        fine = fine_calculation(request)
        if fine is None:
            raise FineCalculationException(search_error_message("fine_message"))
        if username is None:
            raise UsernameNotFound("No username provided")
    except UsernameNotFound as error_message:
        logger.exception("Username Not Found: %s",str(error_message))
        username = error_message.username
    # send_book_return_notification(request) 
    except FineCalculationException as error_msg :
        fine = error_msg.fine
        logger.exception(str(error_msg))
    return render(request, 'home.html', {'username': username,"fine":fine})


def logout(request):
    try:
        auth.logout(request)
    except AttributeError:
        return HttpResponseBadRequest("Invalid request")
    return render(request, 'logout.html')


def register_post_data(request):
    try:
        if not request:
            raise RequestNotFoundException("Request Data not found")
        else:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            username = request.POST.get('username')
            new_user_details={ "first_name":first_name,"last_name":last_name,"email":email,"password":password,"confirm_password":confirm_password,"username":username}
            return new_user_details
    except RequestNotFoundException as error_msg :
        logger.exception(str(error_msg))
        return HttpResponseBadRequest("Connect to internet")

def register(request):
    if request.method == 'POST':
        new_user = register_post_data(request)
        try:
            if new_user['password'] != new_user['confirm_password']:
                raise ValidationError("Passwords do not match")
            if User.objects.filter(username=new_user['username']).exists():
                raise ValidationError("This user already exists")
            if User.objects.filter(email=new_user['email']).exists():
                raise ValidationError("This email id already exists")
            new_user.pop("confirm_password")
            user = User.objects.create_user(
                **new_user
            )
            user.save()
            logger.info("User created successfully")
            messages.success(request, "User created successfully")
            return redirect("/librarymanageapp/loginpage")
        except ValidationError as error_of_validation:
            logger.error(str(error_of_validation))
            return redirect("/librarymanageapp")
    else:
        return render(request, 'register.html')
    
@login_required(login_url=loginpage)
def add_book(request):
    try:
        username = request.user.username
        if not username:
            raise UnboundLocalError(search_error_message("username_error"))
    except UnboundLocalError as error_msg:
        username=" "
        logger.exception(error_msg)
    finally:
        if request.method == "POST":
            create_book(request.POST)
            logger.info("Book added successfully")
            # messages.info(request, "book added successfully")
            return render(request, "add_book.html")
    return render(request, "add_book.html", {"username": username,"categories":create_category_list()})

def create_book(book_data):
    isbn = book_data['book_isbn']
    if Book.objects.filter(isbn=isbn):
        present_book = Book.objects.get(isbn=isbn)
        present_book.quantity += int(book_data['quantity'])
        present_book.save()
    else:
        book = Book.objects.create(
            name=book_data['name'],
            author=book_data['author'],
            isbn=isbn,
            quantity=book_data['quantity'],
            price=book_data['price'],
            category=book_data['category']
        )
        book.save()

def delete_book(request):
    username=request.user.username
    if request.method == "POST":
        book_id = int(request.POST['book_id'])
        quantity = request.POST['quantity']
        book=Book.objects.get(id=book_id)
        book.quantity= book.quantity-int(quantity)
        book.save()
        if(book.quantity<=0):
            book.delete()
        books=Book.objects.all()
        return render(request,"view_books.html", {'books':books,"username":username})
    books=Book.objects.all()
    return render(request,"view_books.html", {'books':books,"username":username})

def create_category_list():
    category_selected=set(Book.objects.values_list('category'))
    categories=list(category_selected)
    category_selected= [category_word[0].capitalize() for category_word in categories]
    return category_selected

def create_unique_book_list():
    unique_book_row=set(IssuedBook.objects.values_list('book_id','book_name'))
    print("hhhhhhhhhhhh",unique_book_row)
    books=list(unique_book_row)
    print("dfdfbhsbfhdbfh",books)
    unique_book_row= [book[0] for book in books]
    unique_book_name_row= [book[1] for book in books]
    print(unique_book_name_row)
    return unique_book_row,unique_book_name_row

@login_required(login_url = loginpage)
def view_books(request):
    username=request.user.username
    if request.method == "POST":
        category_select = request.POST['category']
        books=Book.objects.filter(category=category_select)
        return render(request, "view_books.html", {'books':books,"username":username,'categories':create_category_list})
    books = Book.objects.all()
    return render(request, "view_books.html", {'books':books,"username":username,'categories':create_category_list})

@login_required(login_url = loginpage)
def user_details(request):
    username=request.user.username
    users_details_table=User.objects.all()
    return render(request, "user_details.html", {'users_details_table':users_details_table,"username":username})

def delete_user(request):
    username=request.user.username
    if request.method == "POST":
        user_detail_id = int(request.POST['user_detail_id'])
        user=User.objects.get(id=user_detail_id)
        user.delete()
    users_details_table=User.objects.all()
    return render(request, "user_details.html", {'users_details_table':users_details_table,"username":username})


@login_required(login_url=loginpage)
def view_issued_books(request):
    username=request.user.username
    if request.user.is_superuser:
        books = IssuedBook.objects.all()
    else:
        books = IssuedBook.objects.filter(student_id=request.user.id).all()
    return render(request, "view_issued_books.html", {'books':books,"username":username})

@login_required(login_url=loginpage)
def view_return_books(request):
    username=request.user.username
    if request.user.is_superuser:
        books = ReturnedBook.objects.all()
    else:
        books = ReturnedBook.objects.filter(student_id=request.user.id).all()
    return render(request, "view_return_books.html", {'books':books,"username":username})

def update_book_quantity(book_id):
    book = Book.objects.get(id=book_id)
    try:
        book.quantity -= 1
        if (book.quantity < 0):
            raise QuantityValueError(search_error_message("quantity_message"))
    except QuantityValueError as error_message:
        book.quantity = error_message.quantity
        logger.exception(str(error_message))
    book.save()

def add_pending_request(pending_data):
    fine = fine_calculation(pending_data)
    try:
        issued_book = PendingIssueRequest.objects.create(
            book_name=pending_data.POST['book_name'],
            book_id=pending_data.POST['book_id'], 
            student_id=pending_data.user.id,
            fine=fine
        )
        issued_book.save()
    except KeyError as missing_key_error:
        print(f"KeyError: {str(missing_key_error)}")
       
    except Exception as other_error:
        print(f"Error: {str(other_error)}")


@login_required(login_url=loginpage)
def generate_book_requests(request):
    try:
        username = request.user.username
        if request.method == "POST":
            book_list = pending_request_post(request)
            return render(request, "view_books.html", {'username': username,"books": book_list})
        else:
            issue_request_list = PendingIssueRequest.objects.all()
            return render(request, "requests.html", {'username': username,"issue_request_list":issue_request_list})
    except ValueError as missing_value_error:
        logger.error("Book id is missing : %s",str(missing_value_error))
        return render(request,'home.html')
    except Exception as other_error:
        logger.error("Something went wrong : %s",str(other_error))
        return render(request,'home.html')

def pending_request_post(request):
    student_id = request.user.id
    issued_book_id = request.POST.get('book_id')
    if not issued_book_id:
        raise ValueError("Book ID is missing from the request")
    else:
        if Book.objects.filter(id=issued_book_id).exists():
            if not PendingIssueRequest.objects.filter(book_id=issued_book_id, student_id=student_id).exists():
                add_pending_request(request)
                update_book_quantity(issued_book_id)
                book_list = Book.objects.all()
                messages.info(request, "Book request sent successfully")
                return book_list
            else:
                book_list = Book.objects.all()
                messages.info(request, "Request to issue book has already sent")
                return book_list

@login_required(login_url=loginpage)
def admin_issue_book(request):
    username = request.user.username
    students = User.objects.all()
    if request.method == "POST":
        issued_book_id = request.POST['book_id']
        if Book.objects.filter(id=issued_book_id).exists():
            view_layout = issued_successfully(request, issued_book_id)
            messages.info(request, view_layout[0])
            return render(request, "issue_book.html", {'username': username, "books": view_layout[1],"students":students})
        else:
            book_list = Book.objects.all()
            try:
                if not book_list:
                    raise BookNotFoundException("Book is not available in Library")
            except BookNotFoundException as error_msg:
                book_list=[]
                logger.exception(str(error_msg))
            finally:
                messages.info(request, "Book not available")
            return render(request, "issue_book.html", {'username': username,"books": book_list,"students":students})
    else:
        books = Book.objects.all()
        return render(request, "issue_book.html", {'username': username,"books":books,"students":students})


def issued_successfully(request,issued_book_id):
    if not IssuedBook.objects.filter(book_id=issued_book_id, student_id=request.POST['student_id']).exists():
        create_issued_book(request.POST)
        update_book_quantity(issued_book_id)
        book_list = Book.objects.all()
        msg="Book Issued Successfully"
        return (msg, book_list )
    else:
        book_list = Book.objects.all()
        msg= "Book has already been issued to you"
        return (msg, book_list)
    

def delete_from_issued_list(return_book_id,student_id):
    book=Book.objects.get(id=return_book_id)
    issue_book=IssuedBook.objects.get(student_id=student_id,book_id=return_book_id)
    issue_book.delete()
    try:
        book.quantity += 1
        if book.quantity < 0:
            raise QuantityValueError(search_error_message("quantity_message"))
    except QuantityValueError as error_msg:
        book.quantity = error_msg.quantity
        logger.exception(str(error_msg))
    book.save()

@login_required(login_url=loginpage)
def return_book(request):
    username=request.user.username
    unique_books,unique_book_name=create_unique_book_list()
    students=User.objects.all()
    if request.method == "POST":
        book_name=request.POST['book_name']
        student_id = request.POST['student_id']
        return_book_id=int(request.POST['book_id'])
        return_book_details = {'book_id': return_book_id, 'student_id': student_id, 'book_name': book_name}
        if IssuedBook.objects.filter(**return_book_details):
            delete_from_issued_list(return_book_id,student_id)
            return_book = ReturnedBook.objects.create(**return_book_details)
            return_book.save()
            messages.info(request,"book returned successfully")
            logger.info("book returned successfully")
            return render( request, "home.html",{'username': username,"students":students} )
        else:
            messages.info(request,"this is not in the list of issued books")
            logger.info("this is not in the list of issued books")
    return render(request, "return_book.html",{'username': username,"books":unique_books,"students":students,"names":unique_book_name})

def create_issued_book(issued_book_data):
    issued_books_details={ "book_id":issued_book_data['book_id'],"student_id":issued_book_data['student_id'],"book_name":issued_book_data['book_name'],"fine":0}
    issued_book = IssuedBook.objects.create(
                 **issued_books_details
               )
    issued_book.save()

def delete_from_pending(pending_data):
    pending_book = PendingIssueRequest.objects.filter(
                    student_id=pending_data['student_id'],
                    book_id=pending_data['book_id']
                    )
    pending_book.delete()

def issue_book(request):
    username = request.user.username
    if request.method == "POST":
        create_issued_book(request.POST)
        delete_from_pending(request.POST)
        issue_request_list=PendingIssueRequest.objects.all()
        return render(request, "requests.html", {'username': username,"issue_request_list":issue_request_list})
    else:
        issue_request_list=IssuedBook.objects.all()
        return render(request, "view_issued_books.html",{'username': username,"issue_request_list":issue_request_list})

def reject(request):
    username = request.user.username
    if request.method == "POST":
        try:
            student_id =  request.POST['student_id']
            issued_book_id = request.POST['book_id']
            if not (student_id and issued_book_id):
                raise RequestNotFoundException("Check Internet Connection. Data not found")
            pending_book = PendingIssueRequest.objects.filter(student_id=student_id,book_id = issued_book_id)
            book=Book.objects.get(id = issued_book_id)
            if book.quantity < 0:
                raise QuantityValueError(search_error_message("quantity_message"))
            else:
                book.quantity += 1
            pending_book.delete()
            book.save()
            issue_request_list=PendingIssueRequest.objects.all()
        except RequestNotFoundException as error_msg:
            student_id = error_msg.student_id
            issued_book_id = error_msg.book_id
            logger.exception(str(error_msg))
        except QuantityValueError as error_msg:
            book.quantity = error_msg.quantity
            logger.exception(str(error_msg))
        finally:
            messages.info(request,"Request declined Successfully")
        return render(request, "requests.html", {'username': username,"issue_request_list":issue_request_list})
    
def instructions(request):
    username = request.user.username
    try:
        if not username:
            raise UsernameNotFound(search_error_message("username_error"))
    except UsernameNotFound as error_msg:
            username=error_msg.username
            logger.exception(str(error_msg))
    return render(request, "instructions.html", {'username': username})
    
def pay_fine(request):
    username = request.user.username
    try:
        if not username:
            raise UsernameNotFound(search_error_message("username_error"))
    except UsernameNotFound as error_msg:
            username=error_msg.username
            logger.exception(str(error_msg))
    finally:
        messages.info(request,"Fine Paid Sccessfully")
    return render(request,'home.html', {'username': username})

def search_error_message(error):
    with open('C:/itt/firstproject/librarymanageapp/exception_messages.txt', 'r') as file:
        for line in file:
            if error in line:
                key, value = line.strip().split('=')
                if key.strip() == error:
                    return value.strip()