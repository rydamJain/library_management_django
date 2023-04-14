class FineCalculationException(Exception):
    fine: int
    def __init__(self, message):
        self.fine = 0
        super().__init__(message)
        
class BookNotFoundException(Exception):...

class RequestNotFoundException(Exception):
    student_id: int
    book_id: int
    author: str
    category: str
    book_name: str
    def __init__(self, message):
        self.student_id = 0
        self.book_id = 0
        self.category = " "
        self.book_name = " "
        self.author = " "
        super().__init__(message)

class QuantityValueError(Exception):
    quantity: int
    def __init__(self, message):
        self.quantity = 0
        super().__init__(message)
        
class UsernameNotFound(Exception):
    username: str
    def __init__(self, message):
        self.username = " "
        super().__init__(message)