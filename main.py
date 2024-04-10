import streamlit as st
import pandas as pd
import sqlite3

# Connect to the SQLite database (create it if it doesn't exist)
conn = sqlite3.connect('library.db')
c = conn.cursor()

# Create table if it doesn't exist (improved for clarity)
c.execute('''CREATE TABLE IF NOT EXISTS books (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT NOT NULL UNIQUE,
             author TEXT NOT NULL,
             isbn TEXT UNIQUE,
             quantity INTEGER NOT NULL DEFAULT 1,
             description TEXT
             )''')
conn.commit()

# Function to check for book title redundancy
def book_title_exists(title):
    c.execute("SELECT COUNT(*) FROM books WHERE title = ?", (title,))
    count = c.fetchone()[0]
    return count > 0

# Function to check for ISBN redundancy
def isbn_exists(isbn):
    if isbn:  # Check only if ISBN is provided
        c.execute("SELECT COUNT(*) FROM books WHERE isbn = ?", (isbn,))
        count = c.fetchone()[0]
        return count > 0

# Function to fetch all books
def fetch_all_books():
    c.execute("SELECT * FROM books")
    return c.fetchall()

# Function to add a new book to the database
def add_book(title, author, isbn, quantity, description):
    if not book_title_exists(title) and (not isbn or not isbn_exists(isbn)):
        c.execute("INSERT INTO books (title, author, isbn, quantity, description) VALUES (?, ?, ?, ?, ?)", (title, author, isbn, quantity, description))
        conn.commit()
        st.success("Book added successfully!")
    else:
        error_message = ""
        if book_title_exists(title):
            error_message += "Title already exists. "
        if isbn and isbn_exists(isbn):
            error_message += "ISBN already exists. "
        st.error(error_message + "Please choose unique values.")

# Function to update an existing book
def update_book(title, new_title, new_author, new_isbn, new_quantity, new_description):
    # Find the book by the title entered for update
    c.execute("SELECT * FROM books WHERE title = ?", (title,))
    selected_book = c.fetchone()

    if selected_book:  # If a book with the entered title exists
        if (not book_title_exists(new_title) or new_title == title) and (not new_isbn or not isbn_exists(new_isbn) or new_isbn == selected_book[3]):
            c.execute("""UPDATE books SET title = ?, author = ?, isbn = ?, quantity = ?, description = ? WHERE id = ?""", (new_title, new_author, new_isbn, new_quantity, new_description, selected_book[0]))
            conn.commit()
            st.success("Book updated successfully!")
        else:
            error_message = ""
            if book_title_exists(new_title) and new_title != title:
                error_message += "New title already exists. "
            if new_isbn and isbn_exists(new_isbn) and new_isbn != selected_book[3]:
                error_message += "New ISBN already exists. "
            st.error(error_message + "Please choose unique values or values that haven't changed.")
    else:
        st.error("Book with the entered title not found!")


# Function to delete a book by ID
def delete_book_by_title(title):
    c.execute("DELETE FROM books WHERE title = ?", (title,))
    rows_deleted = c.rowcount  # Get the number of rows deleted
    conn.commit()
    if rows_deleted > 0:
        st.success(f"Book '{title}' deleted successfully!")
    else:
        st.error(f"Book with title '{title}' not found!")

# Streamlit app layout and functionality
st.title("Library Management System")

# Use sidebar for CRUD options
selected_operation = st.sidebar.selectbox("CRUD Operation", ["Create", "Read", "Update", "Delete"])

# Create operation (in sidebar)
if selected_operation == "Create":
    st.subheader("Add New Book")
    new_book_title = st.text_input("Book Title", key="title")
    new_book_author = st.text_input("Author", key="author")
    new_book_isbn = st.text_input("ISBN (Optional)", key="isbn")
    new_book_quantity = st.number_input("Quantity", min_value=1, key="quantity")
    new_book_description = st.text_area("Description (Optional)", key="description")
    if st.button("Add Book", key="add_button"):
        add_book(new_book_title, new_book_author, new_book_isbn, new_book_quantity, new_book_description)

# Read operation (display all books)
if selected_operation == "Read":
    st.subheader("All Books")
    books = fetch_all_books()  # Fetch all books

    if books:
        # Convert fetched data to a Pandas DataFrame
        df = pd.DataFrame(books, columns=["ID", "Title", "Author", "ISBN", "Quantity", "Description"])
        st.dataframe(df)  # Display DataFrame in Streamlit
    else:
        st.info("No books found in the library.")



if selected_operation == "Update":
    st.subheader("Update Book")
    update_title = st.text_input("Enter Title of Book to Update", key="update_title")
    st.write("**Note:** This title must exactly match the book you want to update.")

    if update_title:  # If a title is entered for update
        c.execute("SELECT * FROM books WHERE title = ?", (update_title,))
        selected_book = c.fetchone()

        if selected_book:  # If a book with the entered title exists
            st.write("Current Details:")
            st.write(f"Title: {selected_book[1]}")
            st.write(f"Author: {selected_book[2]}")
            st.write(f"ISBN: {selected_book[3] if selected_book[3] else 'Not Available'}")  # Display ISBN if available
            st.write(f"Quantity: {selected_book[4]}")
            st.write(f"Description: {selected_book[5] if selected_book[5] else 'No Description'}")  # Display description if available

            # Update form elements with pre-filled data
            new_title = st.text_input("Update Title", value=selected_book[1], key="new_title")
            new_author = st.text_input("Update Author", value=selected_book[2], key="new_author")
            new_isbn = st.text_input("Update ISBN (Optional)", value=selected_book[3] if selected_book[3] else "", key="new_isbn")
            new_quantity = st.number_input("Update Quantity", min_value=1, value=selected_book[4], key="new_quantity")
            new_description = st.text_area("Update Description (Optional)", value=selected_book[5] if selected_book[5] else "", key="new_description")

            if st.button("Update Book", key="update_button"):
                update_book(update_title, new_title, new_author, new_isbn, new_quantity, new_description)
        else:
            st.error("Book with the entered title not found!")


# Delete operation (select book by ID, confirmation button)
if selected_operation == "Delete":
    st.subheader("Delete Book")
    delete_title = st.text_input("Enter Title of Book to Delete", key="delete_title")
    st.write("**Note:** This title must exactly match the book you want to delete.")

    if delete_title:  # If a title is entered for deletion
        delete_book_by_title(delete_title)

# Close the database connection
conn.close()
