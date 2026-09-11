"""
Parser factory and registry for managing store-specific parsers.
Automatically discovers and registers parsers based on store chain type.
"""
from typing import Dict, Type, Optional, List
from loguru import logger

from app.parsers.base import BaseParser, ParseError
from app.db.models import StoreChain, Store
from app.config import settings


# Import all available parsers
from app.parsers.pyaterochka_parser import PyaterochkaParser
from app.parsers.magnit_parser import MagnitParser


class ParserRegistry:
    """
    Registry for parser classes mapped to store chains.
    New parsers are automatically registered here.
    """
    
    _parsers: Dict[str, Type[BaseParser]] = {}
    
    @classmethod
    def register(cls, chain_name: str, parser_class: Type[BaseParser]):
        """
        Register a parser class for a specific store chain.
        
        Args:
            chain_name: Store chain identifier (matches StoreChain enum value)
            parser_class: Parser class that implements BaseParser
        """
        cls._parsers[chain_name] = parser_class
        logger.info(f"Registered parser '{parser_class.__name__}' for chain '{chain_name}'")
    
    @classmethod
    def get_parser_class(cls, chain: str) -> Optional[Type[BaseParser]]:
        """
        Get parser class for a specific store chain.
        
        Args:
            chain: Store chain identifier
            
        Returns:
            Parser class or None if not found
        """
        return cls._parsers.get(chain.lower())
    
    @classmethod
    def list_parsers(cls) -> List[str]:
        """List all registered parser chain names."""
        return list(cls._parsers.keys())
    
    @classmethod
    def is_supported(cls, chain: str) -> bool:
        """Check if a parser exists for the given chain."""
        return chain.lower() in cls._parsers


# Initialize registry with built-in parsers
def init_registry():
    """Initialize the parser registry with all available parsers."""
    ParserRegistry.register(StoreChain.PYATEROCHKA.value, PyaterochkaParser)
    ParserRegistry.register(StoreChain.MAGNIT.value, MagnitParser)
    # Add more parsers here as they are implemented:
    # ParserRegistry.register(StoreChain.CHIZHIK.value, ChizhikParser)
    # ParserRegistry.register(StoreChain.KB.value, KBParser)
    
    logger.info(f"Parser registry initialized with {len(ParserRegistry.list_parsers())} parsers: "
                f"{ParserRegistry.list_parsers()}")


class ParserFactory:
    """
    Factory for creating parser instances.
    Handles parser instantiation and configuration.
    """
    
    def __init__(self):
        self._sessions: Dict[int, BaseParser] = {}  # Cache parsers by store_id
    
    def create_parser(self, store: Store) -> BaseParser:
        """
        Create a parser instance for a specific store.
        
        Args:
            store: Store database model instance
            
        Returns:
            Configured parser instance
            
        Raises:
            ParseError: If no parser is available for this store's chain
        """
        chain_value = store.chain.value
        
        # Get parser class from registry
        parser_class = ParserRegistry.get_parser_class(chain_value)
        
        if parser_class is None:
            raise ParseError(
                f"No parser available for store chain '{chain_value}'. "
                f"Supported chains: {ParserRegistry.list_parsers()}"
            )
        
        # Create parser instance
        parser = parser_class(
            store_id=store.id,
            catalog_url=store.catalog_url,
        )
        
        logger.debug(f"Created parser '{parser_class.__name__}' for store {store.id} ({store.name})")
        return parser
    
    async def get_parser(self, store: Store) -> BaseParser:
        """
        Get or create a parser instance for a store.
        Reuses existing parser instances when possible.
        
        Args:
            store: Store database model instance
            
        Returns:
            Configured parser instance
        """
        if store.id in self._sessions:
            return self._sessions[store.id]
        
        parser = self.create_parser(store)
        self._sessions[store.id] = parser
        return parser
    
    async def close_parser(self, store_id: int):
        """
        Close and cleanup parser for a specific store.
        
        Args:
            store_id: Database ID of the store
        """
        if store_id in self._sessions:
            parser = self._sessions[store_id]
            if hasattr(parser, 'close'):
                await parser.close()
            del self._sessions[store_id]
    
    async def close_all(self):
        """Close all active parser instances."""
        for store_id in list(self._sessions.keys()):
            await self.close_parser(store_id)


# Global factory instance
parser_factory = ParserFactory()


async def get_parser_for_store(store: Store) -> BaseParser:
    """
    Convenience function to get a parser for a store.
    
    Args:
        store: Store database model instance
        
    Returns:
        Configured parser instance
    """
    return await parser_factory.get_parser(store)


async def cleanup_parsers():
    """Cleanup all parser resources. Call on application shutdown."""
    await parser_factory.close_all()
