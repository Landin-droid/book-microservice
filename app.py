from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
CORS(app)

# Конфигурация БД
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://bookuser:bookpass@db:5432/bookdb'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация Swagger
api = Api(
    app,
    version='1.0',
    title='Book Management API',
    description='A simple Book Management Microservice',
    doc='/swagger/',
    default='Books',
    default_label='Book operations'
)

db = SQLAlchemy(app)

# Настройка логирования
if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Модель для Swagger
book_model = api.model('Book', {
    'title': fields.String(required=True, description='Book title'),
    'author': fields.String(required=True, description='Book author'),
    'year': fields.Integer(required=True, description='Publication year'),
    'isbn': fields.String(required=True, description='ISBN number')
})

# Модель Book
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat()
        }

# Валидация данных
def validate_book_data(data, partial=False):
    errors = []

    if not partial or 'title' in data:
        if not data.get('title') or len(data.get('title', '').strip()) == 0:
            errors.append("Title is required")

    if not partial or 'author' in data:
        if not data.get('author') or len(data.get('author', '').strip()) == 0:
            errors.append("Author is required")

    if not partial or 'year' in data:
        if data.get('year') is not None:
            try:
                year = int(data['year'])
                if year < 0 or year > datetime.now().year:
                    errors.append(f"Year must be between 0 and {datetime.now().year}")
            except (ValueError, TypeError):
                errors.append("Year must be a valid integer")
        elif not partial:
            errors.append("Year is required")

    if not partial or 'isbn' in data:
        if not data.get('isbn') and not partial:
            errors.append("ISBN is required")

    return errors

# Namespace для книг
ns = api.namespace('books', description='Book operations')

# Инициализация БД
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")
    logger.info("Application started successfully")

# 1. GET /books - получить все книги
@ns.route('/')
class BookList(Resource):
    @ns.response(200, 'Success')
    @ns.response(500, 'Internal Server Error')
    def get(self):
        """Get all books"""
        try:
            books = Book.query.all()
            logger.info(f"Retrieved {len(books)} books")
            return {
                'books': [book.to_dict() for book in books],
                'total': len(books)
            }, 200
        except Exception as e:
            logger.error(f"Error getting books: {str(e)}")
            return {'error': 'Internal server error'}, 500

    # 2. POST /books - создать новую книгу
    @ns.expect(book_model)
    @ns.response(201, 'Book created')
    @ns.response(400, 'Validation error')
    @ns.response(409, 'ISBN conflict')
    @ns.response(500, 'Internal Server Error')
    def post(self):
        """Create a new book"""
        try:
            data = request.get_json()

            if not data:
                logger.warning("No JSON data provided")
                return {'error': 'No JSON data provided'}, 400

            errors = validate_book_data(data)
            if errors:
                logger.warning(f"Validation errors: {errors}")
                return {'errors': errors}, 400

            if Book.query.filter_by(isbn=data['isbn']).first():
                logger.warning(f"ISBN already exists: {data['isbn']}")
                return {'error': 'Book with this ISBN already exists'}, 409

            book = Book(
                title=data['title'],
                author=data['author'],
                year=data['year'],
                isbn=data['isbn']
            )

            db.session.add(book)
            db.session.commit()

            logger.info(f"Created book: {book.title} (ID: {book.id})")
            return {
                'message': 'Book created successfully',
                'book': book.to_dict()
            }, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating book: {str(e)}")
            return {'error': 'Internal server error'}, 500

# 3. GET/PUT/DELETE /books/<id>
@ns.route('/<int:book_id>')
@ns.param('book_id', 'The book identifier')
class BookResource(Resource):

    @ns.response(200, 'Success')
    @ns.response(404, 'Book not found')
    @ns.response(500, 'Internal Server Error')
    def get(self, book_id):
        """Get a book by ID"""
        try:
            book = Book.query.get(book_id)
            if not book:
                logger.warning(f"Book {book_id} not found")
                return {'error': 'Book not found'}, 404

            logger.info(f"Retrieved book: ID={book_id}")
            return {'book': book.to_dict()}, 200
        except Exception as e:
            logger.error(f"Error getting book {book_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500

    @ns.expect(book_model)
    @ns.response(200, 'Book updated')
    @ns.response(400, 'Validation error')
    @ns.response(404, 'Book not found')
    @ns.response(409, 'ISBN conflict')
    @ns.response(500, 'Internal Server Error')
    def put(self, book_id):
        """Update a book"""
        try:
            data = request.get_json()

            if not data:
                logger.warning(f"No JSON data for book {book_id}")
                return {'error': 'No JSON data provided'}, 400

            book = Book.query.get(book_id)
            if not book:
                logger.warning(f"Book {book_id} not found")
                return {'error': 'Book not found'}, 404

            errors = validate_book_data(data)
            if errors:
                logger.warning(f"Validation errors for book {book_id}: {errors}")
                return {'errors': errors}, 400

            existing_book = Book.query.filter(
                Book.isbn == data['isbn'],
                Book.id != book_id
            ).first()
            if existing_book:
                logger.warning(f"ISBN conflict for book {book_id}")
                return {'error': 'Another book with this ISBN already exists'}, 409

            book.title = data['title']
            book.author = data['author']
            book.year = data['year']
            book.isbn = data['isbn']

            db.session.commit()

            logger.info(f"Updated book ID {book_id}")
            return {
                'message': 'Book updated successfully',
                'book': book.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating book {book_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500

    @ns.response(200, 'Book deleted')
    @ns.response(404, 'Book not found')
    @ns.response(500, 'Internal Server Error')
    def delete(self, book_id):
        """Delete a book"""
        try:
            book = Book.query.get(book_id)
            if not book:
                logger.warning(f"Book {book_id} not found")
                return {'error': 'Book not found'}, 404

            db.session.delete(book)
            db.session.commit()

            logger.info(f"Deleted book ID {book_id}")
            return {'message': 'Book deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting book {book_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        Book.query.limit(1).all()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
