"""
View Helper Utilities
Common helper functions for views
"""

import logging

logger = logging.getLogger(__name__)


def refresh_main_window_ui(widget):
    """
    Refresh main window UI after data changes
    
    Args:
        widget: Current widget (self in view classes)
    """
    try:
        parent = widget.parent()
        while parent is not None:
            if hasattr(parent, 'refresh_ui_for_data_change'):
                parent.refresh_ui_for_data_change()
                logger.info("Main window UI refreshed after data change")
                return True
            parent = parent.parent()
        logger.warning("MainWindow not found in parent hierarchy")
        return False
    except Exception as e:
        logger.error(f"Error refreshing main window UI: {e}")
        return False
