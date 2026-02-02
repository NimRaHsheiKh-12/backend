"""
Utility for parsing user messages to identify intent and extract task information
"""
import re
from typing import List, Dict, NamedTuple
from enum import Enum

from .task_enums import TaskAction


class IntentResult(NamedTuple):
    action: TaskAction
    confidence: float  # 0.0 to 1.0


class MessageParser:
    def __init__(self):
        # Define patterns for different intents
        self.create_patterns = [
            r"(add|create|make|new)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+to\s+my\s+list",
            r"(add|create|make|new)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+(?:to\s+my\s+)?(?:task|todo|to-do)\s+list",
            r"(add|create|make|new)\s+(.+)",
            r"i\s+need\s+to\s+(.+)",
            r"don'?t\s+forget\s+to\s+(.+)",
            r"remind\s+me\s+to\s+(.+)"
        ]

        self.read_patterns = [
            r"(show|display|list|view|see|what.*have|what.*got)\s+(?:my\s+)?(?:tasks|todos|to-dos|list|task)",
            r"(what|which)\s+(?:tasks|todos|to-dos)\s+(?:do\s+i\s+have|are\s+on\s+my\s+list)",
            r"my\s+(?:current\s+)?(?:tasks|todos|to-dos)",
            r"help\s+me\s+organize",
            r"what\s+should\s+i\s+do",
            r"show\s+(?:my\s+)?tasks",  # Explicit pattern for "show my tasks" / "show tasks"
            r"list\s+(?:my\s+)?tasks",  # Explicit pattern for "list my tasks" / "list tasks"
        ]

        self.complete_patterns = [
            r"(complete|finish|done|completed|finished)\s+(?:the\s+)?(.+?)",
            r"(mark|set)\s+(?:the\s+)?(.+?)\s+(?:as\s+)?(complete|done|finished)",
            r"i\s+(?:have\s+)?(completed|finished|done)\s+(?:the\s+)?(.+?)",
            r"cross\s+(?:the\s+)?(.+?)\s+off\s+(?:my\s+)?(?:list|tasks)"
        ]

        self.update_patterns = [
            r"(change|update|edit|modify)\s+(?:the\s+)?(.+?)\s+(?:to|as)\s+(.+)",
            r"(update|change|edit|modify)\s+(?:the\s+)?(.+?)",
            r"rename\s+(?:the\s+)?(.+?)\s+(?:to|as)\s+(.+)"
        ]

        self.delete_patterns = [
            r"(delete|remove|eliminate|get rid of)\s+(?:the\s+)?(.+?)",
            r"(delete|remove|eliminate|get rid of)\s+(?:task|todo|to-do)\s+(?:named|called|titled)\s+(.+?)"
        ]

    def parse_intent(self, message: str, current_tasks: List[Dict]) -> IntentResult:
        """
        Parse the user's message to determine the intent
        """
        try:
            if not message:
                return IntentResult(action=TaskAction.NONE, confidence=0.1)

            message_lower = message.lower().strip()

            # Check for complete intent first (before update/delete since "complete" might contain "update" or "delete" keywords)
            for pattern in self.complete_patterns:
                if re.search(pattern, message_lower):
                    return IntentResult(action=TaskAction.COMPLETE, confidence=0.95)

            # Check for create intent (before update/delete since "create" might contain other keywords)
            for pattern in self.create_patterns:
                if re.search(pattern, message_lower):
                    return IntentResult(action=TaskAction.CREATE, confidence=0.95)

            # Check for read/view intent
            for pattern in self.read_patterns:
                if re.search(pattern, message_lower):
                    return IntentResult(action=TaskAction.READ, confidence=0.95)

            # Check for update intent
            for pattern in self.update_patterns:
                if re.search(pattern, message_lower):
                    return IntentResult(action=TaskAction.UPDATE, confidence=0.95)

            # Check for delete intent
            for pattern in self.delete_patterns:
                if re.search(pattern, message_lower):
                    return IntentResult(action=TaskAction.DELETE, confidence=0.95)

            # If no regex patterns matched, try simple keyword matching
            # But only if no other patterns were detected
            if "complete" in message_lower or "done" in message_lower or "finish" in message_lower:
                return IntentResult(action=TaskAction.COMPLETE, confidence=0.8)

            if "add" in message_lower or "create" in message_lower or "new" in message_lower:
                return IntentResult(action=TaskAction.CREATE, confidence=0.8)

            if "show" in message_lower or "list" in message_lower or "view" in message_lower or "see" in message_lower:
                return IntentResult(action=TaskAction.READ, confidence=0.8)

            if "update" in message_lower or "edit" in message_lower or "change" in message_lower:
                return IntentResult(action=TaskAction.UPDATE, confidence=0.8)

            if "delete" in message_lower or "remove" in message_lower:
                return IntentResult(action=TaskAction.DELETE, confidence=0.8)

            # Default to no specific action
            return IntentResult(action=TaskAction.NONE, confidence=0.5)
        except Exception as e:
            import traceback
            print(f"Error in parse_intent: {str(e)}")
            print(traceback.format_exc())
            # Return a safe default
            return IntentResult(action=TaskAction.NONE, confidence=0.1)

    def extract_task_title(self, message: str) -> str:
        """
        Extract the task title from a message
        """
        try:
            if not message:
                return ""

            message_lower = message.lower().strip()

            # Look for patterns that indicate a new task
            for pattern in self.create_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Return the captured group that represents the task
                    groups = match.groups()
                    # Usually the second group is the task title
                    if len(groups) > 1:
                        extracted_title = groups[1].strip()
                    elif len(groups) == 1:
                        extracted_title = groups[0].strip()
                    else:
                        extracted_title = message.strip()

                    # Remove leading/trailing quotes if present
                    extracted_title = extracted_title.strip("'\"")

                    return extracted_title.capitalize()

            # If no match, return the original message as a fallback
            # Also strip quotes from the fallback
            clean_message = message.strip().strip("'\"")
            return clean_message.capitalize()
        except Exception as e:
            import traceback
            print(f"Error in extract_task_title: {str(e)}")
            print(traceback.format_exc())
            return message.strip().capitalize() if message else ""

    def find_task_by_title(self, message: str, tasks: List[Dict]) -> Dict:
        """
        Find a task in the list based on the title mentioned in the message
        """
        try:
            if not message or not tasks:
                return None

            message_lower = message.lower()

            # Look for patterns that indicate which task to operate on
            for pattern in self.complete_patterns + self.update_patterns + self.delete_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    # Extract the task title from the message
                    groups = match.groups()
                    # Usually the second group is the task title
                    if len(groups) > 1:
                        task_title = groups[1].strip()
                    elif len(groups) == 1:
                        task_title = groups[0].strip()
                    else:
                        continue

                    # Strip quotes from the extracted task title to match with task list
                    task_title = task_title.strip("'\"")

                    # Find the task in the list
                    for task in tasks:
                        if 'title' in task and task_title.lower() in task['title'].lower():
                            return task

            # If no specific task found, return None
            return None
        except Exception as e:
            import traceback
            print(f"Error in find_task_by_title: {str(e)}")
            print(traceback.format_exc())
            return None

    def extract_updated_task_title(self, message: str) -> str:
        """
        Extract the new task title from an update message
        """
        try:
            if not message:
                return None

            message_lower = message.lower()

            # Look for patterns that indicate an update with a new title
            for pattern in self.update_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    groups = match.groups()
                    # Usually the third group is the new title
                    if len(groups) > 2:
                        return groups[2].strip().capitalize()
                    elif len(groups) > 1:
                        # If there are only 2 groups, the second might be the new title
                        return groups[1].strip().capitalize()

            # If no match, return None
            return None
        except Exception as e:
            import traceback
            print(f"Error in extract_updated_task_title: {str(e)}")
            print(traceback.format_exc())
            return None