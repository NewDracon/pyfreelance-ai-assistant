from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Импортируем модели, чтобы они были зарегистрированы в Base
from .order import Order
from .analysis import OrderAnalysis
from .bot_user import BotUser

__all__ = ["Base", "Order", "OrderAnalysis", "BotUser"]