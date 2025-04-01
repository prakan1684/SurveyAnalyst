import time
import uuid
from tinydb import TinyDB, Query
from datetime import datetime

class ChatHistoryManager:
    def __init__(self, db_path='chat_history.json'):
        """Initialize the chat history manager with TinyDB."""
        self.db = TinyDB(db_path)
        self.chats_table = self.db.table('chats')
        
    def create_new_chat(self, name=None):
        """Create a new chat session and return its ID."""
        chat_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Create a default name if none provided
        if not name:
            name = f"Chat {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')}"
            
        chat_data = {
            'id': chat_id,
            'name': name,
            'messages': [],
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        self.chats_table.insert(chat_data)
        return chat_id
    
    def get_chat(self, chat_id):
        """Get a specific chat by ID."""
        Chat = Query()
        result = self.chats_table.search(Chat.id == chat_id)
        return result[0] if result else None
    
    def get_all_chats(self):
        """Get all chats, sorted by updated_at (newest first)."""
        chats = self.chats_table.all()
        return sorted(chats, key=lambda x: x.get('updated_at', 0), reverse=True)
    
    def update_chat(self, chat_id, messages=None, name=None):
        """Update a chat's messages and/or name."""
        Chat = Query()
        chat = self.get_chat(chat_id)
        
        if not chat:
            return False
        
        update_data = {'updated_at': time.time()}
        
        if messages is not None:
            update_data['messages'] = messages
            
        if name is not None:
            update_data['name'] = name
            
        self.chats_table.update(update_data, Chat.id == chat_id)
        return True
    
    def delete_chat(self, chat_id):
        """Delete a chat by ID."""
        Chat = Query()
        return self.chats_table.remove(Chat.id == chat_id)
    
    def add_message_to_chat(self, chat_id, role, content, visualization=None):
        """Add a new message to a chat."""
        chat = self.get_chat(chat_id)
        
        if not chat:
            return False
            
        messages = chat.get('messages', [])
        
        # Create the new message
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time()
        }
        
        if visualization:
            message['visualization'] = visualization
            
        messages.append(message)
        
        # Auto-generate a name from the first user message if this is the first message
        if len(messages) == 1 and role == 'user' and not chat.get('name_customized', False):
            # Use the first 30 chars of the message as the chat name
            name = content[:30] + ('...' if len(content) > 30 else '')
            return self.update_chat(chat_id, messages=messages, name=name)
        
        return self.update_chat(chat_id, messages=messages)
    
    def rename_chat(self, chat_id, new_name):
        """Rename a chat and mark it as having a custom name."""
        Chat = Query()
        self.chats_table.update({
            'name': new_name, 
            'name_customized': True,
            'updated_at': time.time()
        }, Chat.id == chat_id)