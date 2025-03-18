"""Configuration management for the supplier project."""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class SupplierConfig:
    """Configuration for supplier research."""
    topic: str
    country: str

    @classmethod
    def validate_inputs(cls, inputs: Dict[str, Any]) -> 'SupplierConfig':
        """Validate and create config from input dictionary."""
        required_fields = {'topic', 'country'}
        missing_fields = required_fields - set(inputs.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate topic
        if not isinstance(inputs['topic'], str) or not inputs['topic'].strip():
            raise ValueError("Topic must be a non-empty string")
        
        # Validate country
        if not isinstance(inputs['country'], str) or not inputs['country'].strip():
            raise ValueError("Country must be a non-empty string")
        
        return cls(
            topic=inputs['topic'].strip(),
            country=inputs['country'].strip()
        )

# Default configuration
DEFAULT_CONFIG = {
    'topic': 'Garmin',
    'country': 'USA'
} 