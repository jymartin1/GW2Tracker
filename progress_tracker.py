import threading
import time
import uuid
from typing import Dict, Optional

class ProgressTracker:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def create_task(self, legendary_name: str) -> str:
        """Create a new progress tracking task"""
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = {
                'legendary_name': legendary_name,
                'progress': 0,
                'message': 'Initializing...',
                'step': None,
                'substep': None,
                'complete': False,
                'success': False,
                'error': None,
                'result': None,
                'created_at': time.time()
            }
        return task_id
    
    def update_progress(self, task_id: str, progress: int, message: str, 
                       step: Optional[str] = None, substep: Optional[str] = None):
        """Update progress for a task"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update({
                    'progress': progress,
                    'message': message,
                    'step': step,
                    'substep': substep
                })
    
    def complete_task(self, task_id: str, success: bool, result: Optional[Dict] = None, error: Optional[str] = None):
        """Mark a task as complete"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].update({
                    'progress': 100,
                    'complete': True,
                    'success': success,
                    'result': result,
                    'error': error,
                    'message': 'Complete!' if success else f'Error: {error}'
                })
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task"""
        with self.lock:
            return self.tasks.get(task_id, None)
    
    def cleanup_old_tasks(self, max_age: int = 3600):
        """Remove tasks older than max_age seconds"""
        current_time = time.time()
        with self.lock:
            expired_tasks = [
                task_id for task_id, task in self.tasks.items()
                if current_time - task['created_at'] > max_age
            ]
            for task_id in expired_tasks:
                del self.tasks[task_id]

# Global progress tracker instance
progress_tracker = ProgressTracker()