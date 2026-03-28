"""
Quality Metrics Tracking.

Tracks validator pass rates, tool success rates, 
and autonomous completion rates.
"""

from typing import Dict, List, Any
from app.utils.logger import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)

class QualityMetrics:
    def __init__(self):
        # We store these metrics per conversation or daily summary in DB
        # For simplicity, we just provide calculation utilities here.
        self.metrics = []
        
    def calculate_tool_success_rate(self, tool_results: Dict[str, Any]) -> float:
        """Returns the percentage of executed tools that succeeded vs errored."""
        if not tool_results:
            return 100.0
            
        total = 0
        errors = 0
        for k, v in tool_results.items():
            if k.endswith("_error"):
                errors += 1
            elif k not in ("recommendations", "system_note"): 
                # Count successful execution keys
                total += 1
                
        real_total = total + errors
        if real_total == 0:
            return 100.0
            
        rate = ((real_total - errors) / real_total) * 100
        logger.info(f"QUALITY_METRIC [Tool Success]: {rate:.1f}%")
        return rate
        
    def calculate_validation_pass_rate(self, validation_runs: List[bool]) -> float:
        """Percentage of review nodes that passed without failures."""
        if not validation_runs:
            return 100.0
            
        passed = sum(1 for v in validation_runs if v)
        rate = (passed / len(validation_runs)) * 100
        logger.info(f"QUALITY_METRIC [Validator Pass]: {rate:.1f}%")
        return rate

quality_metrics = QualityMetrics()
