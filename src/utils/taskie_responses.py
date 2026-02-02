"""
Response formatting utilities for Taskie
"""
from typing import List, Dict
from .emoji_utils import get_task_status_emoji, get_priority_emoji, get_category_emoji


def format_task_response(tasks: List[Dict]) -> str:
    """
    Format a list of tasks into a friendly response string
    """
    if not tasks:
        return "You don't have any tasks on your list right now! Would you like to add one? 😊"
    
    response_parts = ["Here are your current tasks:"]
    
    for i, task in enumerate(tasks, 1):
        status_emoji = get_task_status_emoji(task.get('is_completed', False))
        priority_emoji = get_priority_emoji(task.get('priority', ''))
        category_emoji = get_category_emoji(task.get('category', ''))
        
        task_str = (
            f"{i}. {status_emoji} {task.get('title', 'Untitled Task')} "
            f"{priority_emoji}{category_emoji}"
        )
        
        if task.get('due_date'):
            task_str += f" 📅 {task['due_date']}"
            
        response_parts.append(task_str)
    
    return "\n".join(response_parts)