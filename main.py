from typing import Annotated
from fastapi import FastAPI
from pydantic import BaseModel, Field, validator
import re

app = FastAPI()


def validate_isbn(isbn: str) -> str:
    # Remove hyphens and spaces
    clean_isbn = re.sub(r'[-\s]', '', isbn)
    
    # Check if it's ISBN-10 or ISBN-13
    if len(clean_isbn) == 10:
        # ISBN-10 validation
        if not re.match(r'^\d{9}[\dX]$', clean_isbn):
            raise ValueError('Invalid ISBN-10 format')
        # Calculate check digit
        check_sum = sum(int(digit) * (10 - i) for i, digit in enumerate(clean_isbn[:9]))
        check_digit = (11 - (check_sum % 11)) % 11
        expected = 'X' if check_digit == 10 else str(check_digit)
        if clean_isbn[9] != expected:
            raise ValueError('Invalid ISBN-10 check digit')
    elif len(clean_isbn) == 13:
        # ISBN-13 validation
        if not re.match(r'^\d{13}$', clean_isbn):
            raise ValueError('Invalid ISBN-13 format')
        # Calculate check digit
        check_sum = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(clean_isbn[:12]))
        check_digit = (10 - (check_sum % 10)) % 10
        if int(clean_isbn[12]) != check_digit:
            raise ValueError('Invalid ISBN-13 check digit')
    else:
        raise ValueError('ISBN must be 10 or 13 digits')
    
    return isbn


class Author(BaseModel):
    name: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Smith",
                }
            ]
        }
    }

class Book(BaseModel):
    author: Author
    isbn: str = Field(
        examples=["978-0-306-40615-7"]
    )
    
    @validator('isbn')
    def validate_isbn_field(cls, v):
        return validate_isbn(v)


# In-memory database:
books: list[Book] = []

# Match this endpoint: GET /books/{book_id}
@app.get("/book/{book_id}")
def get_book(book_id: int):
    return books[book_id]


# Match thisd endpoint: GET /books?skip=0&limit=10&author=optional
@app.get("/books")
def list_books(skip:int=0, limit:int =10, author: str=None):
    result = []
    for book in books[skip : skip + limit]:
        # If author was provided then skip if the book's author does not match
        if author is not None:
            if book.author != author:
                continue

        result.append(book)
    return result

# Match this endpoint: POST /books  # with request body
@app.post("/books")
def create_book(book: Book):
    books.append(book)
    return book
