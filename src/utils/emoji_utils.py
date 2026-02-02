"""
Emoji utility module for Taskie's friendly interactions
"""
import random


def get_random_positive_emoji() -> str:
    """
    Returns a random positive emoji to make interactions more friendly
    """
    positive_emojis = [
        "😊", "👍", "👏", "🎉", "✨", "🌟", "💯", "🙌", "👌", "😍",
        "🤩", "😎", "🤗", "🥰", "🥳", "🎊", "🎈", "🏆", "💪", "💖"
    ]
    return random.choice(positive_emojis)


def get_task_status_emoji(is_completed: bool) -> str:
    """
    Returns an appropriate emoji based on task completion status
    """
    if is_completed:
        return "✅"
    else:
        return "📝"


def get_priority_emoji(priority: str) -> str:
    """
    Returns an appropriate emoji based on task priority
    """
    priority_map = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }
    return priority_map.get(priority.lower(), "⚪")


def get_category_emoji(category: str) -> str:
    """
    Returns an appropriate emoji based on task category
    """
    category_map = {
        "work": "💼",
        "personal": "🏠",
        "study": "📚",
        "custom": "⚙️"
    }
    return category_map.get(category.lower(), "📋")