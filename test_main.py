# File: test_main.py
# Path: fastapi-study/test_main.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Book Inventory API"
    assert "documentation" in response.json()


def test_create_book():
    """Test creating a new book."""
    response = client.post(
        "/books",
        json={
            "title": "Test Book",
            "author": {"name": "Test Author"},
            "isbn": "978-0-306-40615-7"
        }
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"
    assert response.json()["author"]["name"] == "Test Author"


def test_get_book():
    """Test retrieving a specific book."""
    # First create a book
    create_response = client.post(
        "/books",
        json={
            "title": "Another Test Book",
            "author": {"name": "Another Author"},
            "isbn": "978-1-234-56789-7"
        }
    )

    # Get the book (it should be at index 1 after previous test)
    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Another Test Book"


def test_get_nonexistent_book():
    """Test getting a book that doesn't exist returns 404."""
    response = client.get("/books/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_books():
    """Test listing books with pagination."""
    response = client.get("/books")
    assert response.status_code == 200
    assert "books" in response.json()
    assert "total" in response.json()
    assert isinstance(response.json()["books"], list)


def test_list_books_with_author_filter():
    """Test filtering books by author."""
    response = client.get("/books?author=Test Author")
    assert response.status_code == 200
    books = response.json()["books"]
    assert all(book["author"]["name"] == "Test Author" for book in books)


def test_protected_endpoint_without_token():
    """Test that protected endpoint requires authentication."""
    response = client.get("/books/protected/summary")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_protected_endpoint_with_token():
    """Test protected endpoint with a token."""
    response = client.get(
        "/books/protected/summary",
        headers={"Authorization": "Bearer fake-token-for-testing"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "total_books" in response.json()


def test_invalid_isbn():
    """Test that invalid ISBN is rejected."""
    response = client.post(
        "/books",
        json={
            "title": "Invalid ISBN Book",
            "author": {"name": "Some Author"},
            "isbn": "123-456"  # Invalid ISBN
        }
    )
    assert response.status_code == 422  # Validation error
