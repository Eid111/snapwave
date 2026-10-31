# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional

class BaseResolver:
    """Base class for custom video stream resolvers."""
    
    def can_handle(self, url: str) -> bool:
        raise NotImplementedError

    def resolve(self, url: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
