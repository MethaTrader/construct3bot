import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.pool import NullPool

from config import load_config
from database.models import Base, User, Product, Category, Purchase, Newsletter

# Load config for database URL
config = load_config()
DATABASE_URL = config.database_url

# Create async engine with optimized settings
# Using NullPool to prevent connection pooling issues in asyncio applications
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,  # Set to False to reduce logging overhead
    poolclass=NullPool,  # Use NullPool to avoid connection issues
    future=True
)

# Create async session factory
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Logger
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database by creating all tables"""
    try:
        async with engine.begin() as conn:
            # Create all tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_session() -> AsyncSession:
    """Get a new session"""
    async with async_session() as session:
        return session

# User methods
async def get_or_create_user(telegram_id: int, user_data: dict) -> User:
    """Get user by telegram_id or create if not exists"""
    try:
        async with async_session() as session:
            # Check if user exists
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            # Create user if not exists
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name'),
                    last_name=user_data.get('last_name')
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"Created new user: {user.telegram_id}")
            else:
                # Update last active
                user.last_active = datetime.utcnow()
                await session.commit()
            
            return user
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        # Return a minimal user object to prevent cascading errors
        return User(
            telegram_id=telegram_id,
            username=user_data.get('username'),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            balance=0.0
        )

async def update_user_activity(session: AsyncSession, user_id: int):
    """Update user's last activity timestamp"""
    try:
        stmt = update(User).where(User.id == user_id).values(last_active=datetime.utcnow())
        await session.execute(stmt)
        await session.commit()
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")
        # Don't raise the exception as this is a non-critical operation

async def get_user_balance(telegram_id: int) -> float:
    """Get user balance by telegram_id"""
    try:
        async with async_session() as session:
            query = select(User.balance).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            balance = result.scalar_one_or_none()
            return balance or 0.0
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        return 0.0  # Return default balance to prevent errors

async def update_user_balance(telegram_id: int, new_balance: float) -> bool:
    """Update user balance"""
    try:
        async with async_session() as session:
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            if user:
                user.balance = new_balance
                user.last_active = datetime.utcnow()
                await session.commit()
                return True
            return False
    except Exception as e:
        logger.error(f"Error updating user balance: {e}")
        return False

async def add_user_balance(telegram_id: int, amount: float) -> tuple:
    """Add amount to user balance and return success status with old and new balance"""
    try:
        async with async_session() as session:
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            user = result.scalars().first()
            
            if not user:
                logger.error(f"User {telegram_id} not found in database")
                return False, 0, 0
            
            current_balance = user.balance
            new_balance = current_balance + amount
            user.balance = new_balance
            user.last_active = datetime.utcnow()
            
            await session.commit()
            logger.info(f"Updated balance for user {telegram_id}: {current_balance} -> {new_balance}")
            return True, current_balance, new_balance
    except Exception as e:
        logger.error(f"Error adding user balance: {e}")
        return False, 0, 0

async def get_user_by_username(username: str) -> User:
    """Get user by username"""
    try:
        async with async_session() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None

# Product methods
async def get_all_products(available_only: bool = True):
    """Get all products, optionally filtered by availability"""
    try:
        async with async_session() as session:
            if available_only:
                query = select(Product).where(Product.available == True)
            else:
                query = select(Product)
            
            result = await session.execute(query)
            products = result.scalars().all()
            # Log the number of products found for debugging
            logger.info(f"Retrieved {len(products)} products (available_only={available_only})")
            return products
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return []

async def get_product(product_id: int):
    """Get product by ID with category eagerly loaded"""
    try:
        async with async_session() as session:
            # Use joinedload to eagerly load the category relationship
            from sqlalchemy.orm import joinedload
            query = select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
            result = await session.execute(query)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return None

async def get_products_by_category(category_id: int, available_only: bool = True):
    """Get products by category ID"""
    try:
        async with async_session() as session:
            if available_only:
                query = select(Product).where(
                    Product.category_id == category_id,
                    Product.available == True
                )
            else:
                query = select(Product).where(Product.category_id == category_id)
            
            result = await session.execute(query)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting products by category: {e}")
        return []

async def add_product(product_data: dict) -> Product:
    """Add a new product"""
    try:
        async with async_session() as session:
            product = Product(
                title=product_data.get('title'),
                short_description=product_data.get('short_description'),
                price=product_data.get('price'),
                file_id=product_data.get('file_id'),
                preview_image_id=product_data.get('preview_image_id'),
                available=product_data.get('available', True),
                category_id=product_data.get('category_id')
            )
            session.add(product)
            await session.commit()
            await session.refresh(product)
            logger.info(f"Added new product: {product.title}")
            return product
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        return None

async def update_product(product_id: int, product_data: dict) -> bool:
    """Update a product"""
    try:
        async with async_session() as session:
            query = select(Product).where(Product.id == product_id)
            result = await session.execute(query)
            product = result.scalars().first()
            
            if not product:
                return False
            
            # Update product attributes
            if 'title' in product_data:
                product.title = product_data['title']
            if 'short_description' in product_data:
                product.short_description = product_data['short_description']
            if 'price' in product_data:
                product.price = product_data['price']
            if 'file_id' in product_data:
                product.file_id = product_data['file_id']
            if 'preview_image_id' in product_data:
                product.preview_image_id = product_data['preview_image_id']
            if 'available' in product_data:
                product.available = product_data['available']
            if 'category_id' in product_data:
                product.category_id = product_data['category_id']
            
            await session.commit()
            logger.info(f"Updated product: {product.title}")
            return True
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return False

async def delete_product(product_id: int) -> bool:
    """Delete a product"""
    try:
        async with async_session() as session:
            query = select(Product).where(Product.id == product_id)
            result = await session.execute(query)
            product = result.scalars().first()
            
            if not product:
                return False
            
            # Log product name before deleting
            product_name = product.title
            
            # Delete the product
            await session.delete(product)
            await session.commit()
            
            logger.info(f"Deleted product: {product_name}")
            return True
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        return False

# Category methods
async def get_all_categories():
    """Get all categories"""
    try:
        async with async_session() as session:
            query = select(Category)
            result = await session.execute(query)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []

async def get_category(category_id: int):
    """Get category by ID"""
    try:
        async with async_session() as session:
            query = select(Category).where(Category.id == category_id)
            result = await session.execute(query)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting category: {e}")
        return None

async def add_category(name: str) -> Category:
    """Add a new category"""
    try:
        async with async_session() as session:
            category = Category(name=name)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            logger.info(f"Added new category: {category.name}")
            return category
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        return None

# Purchase methods
async def create_purchase(user_id: int, product_id: int, purchase_price: float):
    """Create a purchase record"""
    try:
        async with async_session() as session:
            # First check if the product is available
            product_query = select(Product).where(
                Product.id == product_id,
                Product.available == True
            )
            product_result = await session.execute(product_query)
            product = product_result.scalars().first()
            
            if not product:
                return None
            
            # Get the user
            user_query = select(User).where(User.telegram_id == user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalars().first()
            
            if not user:
                return None
            
            # Check if balance is sufficient
            if user.balance < purchase_price:
                return None
            
            # Update balance
            user.balance -= purchase_price
            
            # Create purchase
            purchase = Purchase(
                user_id=user.id,
                product_id=product_id,
                purchase_price=purchase_price
            )
            
            session.add(purchase)
            await session.commit()
            await session.refresh(purchase)
            
            return purchase
    except Exception as e:
        logger.error(f"Error creating purchase: {e}")
        return None

async def get_user_purchases(telegram_id: int):
    """Get all purchases for a user"""
    try:
        async with async_session() as session:
            # First get the user's ID
            user_query = select(User.id).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_query)
            user_id = user_result.scalar_one_or_none()
            
            if not user_id:
                return []
            
            # Get purchases with product details
            query = select(Purchase, Product).join(Product).where(Purchase.user_id == user_id)
            result = await session.execute(query)
            
            purchases = []
            for purchase, product in result:
                purchases.append({
                    "id": purchase.id,
                    "product_id": product.id,
                    "title": product.title,
                    "purchase_date": purchase.purchase_date,
                    "purchase_price": purchase.purchase_price,
                    "file_id": product.file_id
                })
            
            return purchases
    except Exception as e:
        logger.error(f"Error getting user purchases: {e}")
        return []

async def get_total_users_count() -> int:
    """Get total number of users in the database"""
    try:
        async with async_session() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(User)
            result = await session.execute(query)
            return result.scalar() or 0
    except Exception as e:
        logger.error(f"Error getting total users count: {e}")
        return 0

async def get_new_users_count(since_date: datetime) -> int:
    """Get number of new users since a given date"""
    try:
        async with async_session() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(User).where(User.created_at >= since_date)
            result = await session.execute(query)
            return result.scalar() or 0
    except Exception as e:
        logger.error(f"Error getting new users count: {e}")
        return 0

async def get_active_users_count(since_date: datetime) -> int:
    """Get number of active users since a given date"""
    try:
        async with async_session() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(User).where(User.last_active >= since_date)
            result = await session.execute(query)
            return result.scalar() or 0
    except Exception as e:
        logger.error(f"Error getting active users count: {e}")
        return 0

async def get_total_purchases_count() -> int:
    """Get total number of purchases"""
    try:
        async with async_session() as session:
            from sqlalchemy import func
            query = select(func.count()).select_from(Purchase)
            result = await session.execute(query)
            return result.scalar() or 0
    except Exception as e:
        logger.error(f"Error getting total purchases count: {e}")
        return 0

async def get_recent_purchases_data(since_date: datetime) -> list:
    """Get data about purchases since a given date"""
    try:
        async with async_session() as session:
            query = select(Purchase).where(Purchase.purchase_date >= since_date)
            result = await session.execute(query)
            purchases = result.scalars().all()
            
            purchase_data = []
            for purchase in purchases:
                purchase_data.append({
                    "id": purchase.id,
                    "user_id": purchase.user_id,
                    "product_id": purchase.product_id,
                    "purchase_date": purchase.purchase_date,
                    "purchase_price": purchase.purchase_price
                })
            
            return purchase_data
    except Exception as e:
        logger.error(f"Error getting recent purchases data: {e}")
        return []

async def create_newsletter(newsletter_data: dict) -> Newsletter:
    """Create a new newsletter"""
    try:
        async with async_session() as session:
            newsletter = Newsletter(
                title=newsletter_data.get('title'),
                message_text=newsletter_data.get('message_text'),
                photo_id=newsletter_data.get('photo_id'),
                file_id=newsletter_data.get('file_id'),
                file_name=newsletter_data.get('file_name'),
                button_text=newsletter_data.get('button_text'),
                button_url=newsletter_data.get('button_url'),
                status="draft"
            )
            session.add(newsletter)
            await session.commit()
            await session.refresh(newsletter)
            logger.info(f"Created new newsletter: {newsletter.title}")
            return newsletter
    except Exception as e:
        logger.error(f"Error creating newsletter: {e}")
        return None

async def get_all_newsletters():
    """Get all newsletters ordered by created_at descending"""
    try:
        async with async_session() as session:
            query = select(Newsletter).order_by(Newsletter.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting newsletters: {e}")
        return []

async def get_newsletter(newsletter_id: int):
    """Get newsletter by ID"""
    try:
        async with async_session() as session:
            query = select(Newsletter).where(Newsletter.id == newsletter_id)
            result = await session.execute(query)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting newsletter: {e}")
        return None

async def update_newsletter(newsletter_id: int, newsletter_data: dict) -> bool:
    """Update a newsletter"""
    try:
        async with async_session() as session:
            query = select(Newsletter).where(Newsletter.id == newsletter_id)
            result = await session.execute(query)
            newsletter = result.scalars().first()
            
            if not newsletter:
                return False
            
            # Update newsletter attributes
            if 'title' in newsletter_data:
                newsletter.title = newsletter_data['title']
            if 'message_text' in newsletter_data:
                newsletter.message_text = newsletter_data['message_text']
            if 'photo_id' in newsletter_data:
                newsletter.photo_id = newsletter_data['photo_id']
            if 'file_id' in newsletter_data:
                newsletter.file_id = newsletter_data['file_id']
            if 'file_name' in newsletter_data:
                newsletter.file_name = newsletter_data['file_name']
            if 'button_text' in newsletter_data:
                newsletter.button_text = newsletter_data['button_text']
            if 'button_url' in newsletter_data:
                newsletter.button_url = newsletter_data['button_url']
            if 'status' in newsletter_data:
                newsletter.status = newsletter_data['status']
            if 'sent_at' in newsletter_data:
                newsletter.sent_at = newsletter_data['sent_at']
            if 'recipients_count' in newsletter_data:
                newsletter.recipients_count = newsletter_data['recipients_count']
            if 'success_count' in newsletter_data:
                newsletter.success_count = newsletter_data['success_count']
            if 'error_count' in newsletter_data:
                newsletter.error_count = newsletter_data['error_count']
            if 'send_time' in newsletter_data:
                newsletter.send_time = newsletter_data['send_time']
            
            await session.commit()
            logger.info(f"Updated newsletter: {newsletter.title}")
            return True
    except Exception as e:
        logger.error(f"Error updating newsletter: {e}")
        return False

async def delete_newsletter(newsletter_id: int) -> bool:
    """Delete a newsletter"""
    try:
        async with async_session() as session:
            query = select(Newsletter).where(Newsletter.id == newsletter_id)
            result = await session.execute(query)
            newsletter = result.scalars().first()
            
            if not newsletter:
                return False
            
            # Log newsletter name before deleting
            newsletter_title = newsletter.title
            
            # Delete the newsletter
            await session.delete(newsletter)
            await session.commit()
            
            logger.info(f"Deleted newsletter: {newsletter_title}")
            return True
    except Exception as e:
        logger.error(f"Error deleting newsletter: {e}")
        return False

async def get_all_users_telegram_ids() -> list:
    """Get telegram IDs of all users for the newsletter"""
    try:
        async with async_session() as session:
            query = select(User.telegram_id)
            result = await session.execute(query)
            return [telegram_id for telegram_id, in result.all()]
    except Exception as e:
        logger.error(f"Error getting user IDs: {e}")
        return []

async def mark_newsletter_as_sent(newsletter_id: int, stats: dict) -> bool:
    """Mark a newsletter as sent with statistics"""
    try:
        async with async_session() as session:
            query = select(Newsletter).where(Newsletter.id == newsletter_id)
            result = await session.execute(query)
            newsletter = result.scalars().first()
            
            if not newsletter:
                return False
            
            newsletter.status = "sent"
            newsletter.sent_at = datetime.utcnow()
            newsletter.recipients_count = stats.get("recipients_count", 0)
            newsletter.success_count = stats.get("success_count", 0)
            newsletter.error_count = stats.get("error_count", 0)
            newsletter.send_time = stats.get("send_time", 0.0)
            
            await session.commit()
            logger.info(f"Marked newsletter as sent: {newsletter.title}")
            return True
    except Exception as e:
        logger.error(f"Error marking newsletter as sent: {e}")
        return False