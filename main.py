# File: main.py
# Path: fastapi-study/main.py

from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
import re

app = FastAPI(
    title="Book Inventory API",
    description="Learning FastAPI with a book management system",
    version="0.1.0"
)

# Security setup (basic for now)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ================ Models ================

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


class BookDetail(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: Author
    isbn: str = Field(
        ...,
        examples=["978-0-306-40615-7"],
        description="ISBN-10 or ISBN-13 format"
    )

    @validator('isbn')
    def validate_isbn_field(cls, v):
        return validate_isbn(v)


class BookList(BaseModel):
    books: list[BookDetail]
    total: int
    skip: int
    limit: int


# ================ Validators ================

def validate_isbn(isbn: str) -> str:
    """Validate ISBN-10 or ISBN-13 format with check digit verification."""
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


# ================ Dependencies ================

class PaginationParams:
    """Common pagination parameters."""
    def __init__(self, skip: int = 0, limit: int = 10) -> None:
        self.skip = max(0, skip)  # Ensure non-negative
        self.limit = min(100, max(1, limit))  # Between 1-100


def get_db() -> str:
    """Database dependency - returns connection string for now."""
    return "postgresql://localhost/bookdb"  # Mock for now


# ================ Database ================

# In-memory database (will be replaced with real DB in Week 2)
books: list[BookDetail] = []


# ================ Endpoints ================

@app.get("/books", response_model=BookList)
def list_books(
    pagination: Annotated[PaginationParams, Depends()],
    db: Annotated[str, Depends(get_db)],
    author: Optional[str] = None,
) -> BookList:
    """
    List all books with optional filtering by author.

    - **skip**: Number of books to skip (pagination)
    - **limit**: Maximum number of books to return (max 100)
    - **author**: Filter by author name (exact match)
    """
    # Filter books by author if provided
    filtered_books = books
    if author:
        filtered_books = [book for book in books if book.author.name == author]

    # Apply pagination
    paginated_books = filtered_books[pagination.skip : pagination.skip + pagination.limit]

    return BookList(
        books=paginated_books,
        total=len(filtered_books),
        skip=pagination.skip,
        limit=pagination.limit
    )


@app.get("/books/{book_id}", response_model=BookDetail)
def get_book(book_id: int) -> BookDetail:
    """Get a specific book by ID."""
    if book_id < 0 or book_id >= len(books):
        raise HTTPException(
            status_code=404,
            detail=f"Book with id {book_id} not found"
        )
    return books[book_id]


@app.post("/books", response_model=BookDetail, status_code=201)
def create_book(book: BookDetail) -> BookDetail:
    """Create a new book."""
    books.append(book)
    return book


@app.put("/books/{book_id}", response_model=BookDetail)
def update_book(book_id: int, book: BookDetail) -> BookDetail:
    """Update an existing book."""
    if book_id < 0 or book_id >= len(books):
        raise HTTPException(
            status_code=404,
            detail=f"Book with id {book_id} not found"
        )
    books[book_id] = book
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int) -> None:
    """Delete a book."""
    if book_id < 0 or book_id >= len(books):
        raise HTTPException(
            status_code=404,
            detail=f"Book with id {book_id} not found"
        )
    books.pop(book_id)


# ================ Protected Endpoints ================

@app.get("/books/protected/summary")
async def get_protected_books(token: Annotated[str, Depends(oauth2_scheme)]):
    """Example protected endpoint - requires Bearer token."""
    return {
        "message": "You have access to protected book data!",
        "token_preview": token[:10] + "...",
        "total_books": len(books)
    }


# ================ Root Endpoint ================

@app.get("/")
def read_root():
    """Welcome endpoint."""
    return {
        "message": "Welcome to the Book Inventory API",
        "documentation": "/docs",
        "openapi_spec": "/openapi.json"
    }
