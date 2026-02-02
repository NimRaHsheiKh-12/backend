"""
Enums for task-related actions in the TaskBox Chatbot Assistant
"""
from enum import Enum


class TaskAction(Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    COMPLETE = "COMPLETE"
    NONE = "NONE"