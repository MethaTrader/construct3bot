import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete

from config import load_config
from database.models import Base, User, Product, Category, Purchase

# Load config for database URL
config = load_config()
DATABASE_URL = config.database_url

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# Logger
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database by creating all tables"""
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

async def get_session() -> AsyncSession:
    """Get a new session"""
    async with async_session() as session:
        return session

# User methods
async def get_or_create_user(telegram_id: int, user_data: dict) -> User:
    """Get user by telegram_id or create if not exists"""
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
            await update_user_activity(session, user.id)
        
        return user

async def update_user_activity(session: AsyncSession, user_id: int):
    """Update user's last activity timestamp"""
    stmt = update(User).where(User.id == user_id).values(last_active=datetime.utcnow())
    await session.execute(stmt)
    await session.commit()

async def get_user_balance(telegram_id: int) -> float:
    """Get user balance by telegram_id"""
    async with async_session() as session:
        query = select(User.balance).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        balance = result.scalar_one_or_none()
        return balance or 0.0

async def update_user_balance(telegram_id: int, new_balance: float) -> bool:
    """Update user balance"""
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

async def get_user_by_username(username: str) -> User:
    """Get user by username"""
    async with async_session() as session:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        return result.scalars().first()

# Product methods
async def get_all_products(available_only: bool = True):
    """Get all products, optionally filtered by availability"""
    async with async_session() as session:
        try:
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
    async with async_session() as session:
        # Use joinedload to eagerly load the category relationship
        from sqlalchemy.orm import joinedload
        query = select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
        result = await session.execute(query)
        return result.scalars().first()

async def get_products_by_category(category_id: int, available_only: bool = True):
    """Get products by category ID"""
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

async def add_product(product_data: dict) -> Product:
    """Add a new product"""
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


async def update_product(product_id: int, product_data: dict) -> bool:
    """Update a product"""
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

async def delete_product(product_id: int) -> bool:
    """Delete a product"""
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

# Category methods
async def get_all_categories():
    """Get all categories"""
    async with async_session() as session:
        query = select(Category)
        result = await session.execute(query)
        return result.scalars().all()

async def get_category(category_id: int):
    """Get category by ID"""
    async with async_session() as session:
        query = select(Category).where(Category.id == category_id)
        result = await session.execute(query)
        return result.scalars().first()

async def add_category(name: str) -> Category:
    """Add a new category"""
    async with async_session() as session:
        category = Category(name=name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        logger.info(f"Added new category: {category.name}")
        return category

# Purchase methods
async def create_purchase(user_id: int, product_id: int, purchase_price: float):
    """Create a purchase record"""
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

async def get_user_purchases(telegram_id: int):
    """Get all purchases for a user"""
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

async def get_total_users_count() -> int:
    """Get total number of users in the database"""
    async with async_session() as session:
        from sqlalchemy import func
        query = select(func.count()).select_from(User)
        result = await session.execute(query)
        return result.scalar() or 0

async def get_new_users_count(since_date: datetime) -> int:
    """Get number of new users since a given date"""
    async with async_session() as session:
        from sqlalchemy import func
        query = select(func.count()).select_from(User).where(User.created_at >= since_date)
        result = await session.execute(query)
        return result.scalar() or 0

async def get_active_users_count(since_date: datetime) -> int:
    """Get number of active users since a given date"""
    async with async_session() as session:
        from sqlalchemy import func
        query = select(func.count()).select_from(User).where(User.last_active >= since_date)
        result = await session.execute(query)
        return result.scalar() or 0

async def get_total_purchases_count() -> int:
    """Get total number of purchases"""
    async with async_session() as session:
        from sqlalchemy import func
        query = select(func.count()).select_from(Purchase)
        result = await session.execute(query)
        return result.scalar() or 0

async def get_recent_purchases_data(since_date: datetime) -> list:
    """Get data about purchases since a given date"""
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