"""
Dieses Modul enthält Services für die Anwendung.
"""

from typing import List as _List, Any as _Any

from app.services.llm import get_llm_options, generate_completion  # re-export

__all__: _List[_Any] = [
	"get_llm_options",
	"generate_completion",
]
