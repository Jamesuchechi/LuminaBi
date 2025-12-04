"""
APScheduler configuration and task scheduler.
Handles background tasks like data cleaning, insights generation, and report scheduling.
"""

import logging
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings

logger = logging.getLogger('scheduler')

scheduler = BackgroundScheduler()

def start_scheduler():
    """Initialize and start the background scheduler."""
    if scheduler.running:
        logger.warning('Scheduler is already running')
        return
    
    try:
        # Register scheduled tasks from settings
        for task_name, task_config in settings.SCHEDULED_TASKS.items():
            try:
                task_func_path = task_config.get('task')
                schedule_interval = task_config.get('schedule', timedelta(hours=1))
                
                # Import the task function dynamically
                module_path, func_name = task_func_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[func_name])
                task_func = getattr(module, func_name)
                
                # Add job to scheduler
                scheduler.add_job(
                    task_func,
                    IntervalTrigger(seconds=schedule_interval.total_seconds()),
                    id=task_name,
                    name=task_name,
                    replace_existing=True,
                )
                logger.info(f'Scheduled task registered: {task_name}')
            except Exception as e:
                logger.error(f'Failed to register task {task_name}: {e}')
        
        scheduler.start()
        logger.info('Background scheduler started successfully')
    except Exception as e:
        logger.error(f'Failed to start scheduler: {e}')


def stop_scheduler():
    """Stop the background scheduler gracefully."""
    if scheduler.running:
        try:
            scheduler.shutdown(wait=True)
            logger.info('Background scheduler stopped')
        except Exception as e:
            logger.error(f'Error stopping scheduler: {e}')


def get_scheduler_jobs():
    """Get list of all scheduled jobs."""
    return scheduler.get_jobs()


def pause_job(job_id):
    """Pause a specific scheduled job."""
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.pause()
            logger.info(f'Job paused: {job_id}')
            return True
        return False
    except Exception as e:
        logger.error(f'Error pausing job {job_id}: {e}')
        return False


def resume_job(job_id):
    """Resume a specific scheduled job."""
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.resume()
            logger.info(f'Job resumed: {job_id}')
            return True
        return False
    except Exception as e:
        logger.error(f'Error resuming job {job_id}: {e}')
        return False


def remove_job(job_id):
    """Remove a specific scheduled job."""
    try:
        scheduler.remove_job(job_id)
        logger.info(f'Job removed: {job_id}')
        return True
    except Exception as e:
        logger.error(f'Error removing job {job_id}: {e}')
        return False
