from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    # 유저 ID도 고유 문자열로 관리하려면 String
    user_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    conversations = relationship("Conversation", back_populates="owner")

class Conversation(Base):
    __tablename__ = "conversations"
    conv_id = Column(String(50), primary_key=True, index=True) # IP 주소 등 저장
    user_id = Column(String(50), ForeignKey("users.user_id")) # User의 PK와 타입이 같아야 함
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    msg_id = Column(Integer, primary_key=True, index=True) # 메시지는 자동번호(Integer)가 편할 수 있음
    conv_id = Column(String(50), ForeignKey("conversations.conv_id"))
    role = Column(Enum('user', 'assistant'), nullable=False) # Enum도 MySQL에서 길이를 요구할 수 있음
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
