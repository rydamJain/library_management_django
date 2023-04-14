from django.test import TestCase, TransactionTestCase, Client
from django.urls import resolve, reverse
from django.contrib.auth import authenticate
from librarymanageapp.customexceptions import QuantityValueError
from librarymanageapp.views import add_book, instructions, return_book, update_book_quantity, user_details, view_issued_books
from .models import User,Book
from unittest.mock import Mock

class UrlsTests(TestCase):
    def test_loginpage(self):
        response = self.client.get(reverse('loginpage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loginpage.html')

    def test_user_details(self):
        url = reverse('user')
        self.assertEquals(resolve(url).func, user_details)

    def test_admin_return_book_page(self):
        url = reverse('returnbook')
        self.assertEquals(resolve(url).func, return_book)

    def test_add_book_page(self):
        url = reverse('addbook')
        self.assertEquals(resolve(url).func, add_book)

    def test_instructions_page(self):
        url = reverse('instruct')
        self.assertEquals(resolve(url).func, instructions)

class DatabaseTests(TransactionTestCase):
    databases = ['default']
    def test_register(self, new_user_details={ "first_name":'shreya',"last_name":'Gupta',"email":'shreya@gmail.com',
                    "password":"Shreya@2001","confirm_password":"Shreya@2001","username":'shreya'}):
        response = self.client.post(reverse('register'), new_user_details)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='shreya').exists())

class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client = Client()
        self.client.login(username=self.username, password=self.password)

    def test_logout_view(self):
        response = self.client.get(reverse('logoutpage'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(authenticate(username=self.username, password=self.password))

    def tearDown(self):
        self.client.logout()


class DeleteBookViewTestCase(TestCase):
    def setUp(self,book_details={"isbn":123,"price":400,"category":"fun","name":"Test Book", "author":"Test Author", "quantity":2}):
        self.book = Book.objects.create(**book_details)
        
    def test_delete_book(self):
        data = {'book_id': self.book.id, 'quantity': 1}
        response = self.client.post(reverse('deletebook'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Book.objects.filter(id=self.book.id).exists())
        updated_book = Book.objects.get(id=self.book.id)
        self.assertEqual(updated_book.quantity, 1)
    
class QuantityTest():
    def mock_book():
        book = Mock(Book)
        book.quantity = 2
        return book

    def test_update_book_quantity(mock_book):
        update_book_quantity(mock_book.id)
        assert mock_book.quantity == 1
       
    def test_update_book_quantity_zero_quantity(self,mock_book):
        mock_book.quantity = -1
        with self.assertraises(QuantityValueError) as exc_info:
            update_book_quantity(mock_book.id)
        assert str(exc_info.value) == 'Exception: Book quantity can not be negative'
        assert mock_book.quantity == 0
        

class view_test(TestCase):
    def test_view_issued_books_superuser(self):
        request = Mock(user=Mock(is_superuser=True))
        response = view_issued_books(request)
        assert response.status_code == 200

    def test_view_issued_books_student(self):
        request = Mock(user=Mock(is_superuser=False, id=123))
        response = view_issued_books(request)
        assert response.status_code == 200
