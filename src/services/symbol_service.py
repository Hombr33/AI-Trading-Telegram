"""Symbol service for managing symbol mappings."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.models.symbol_mappings import SymbolMapping
from src.core.logging import get_logger

logger = get_logger(__name__)

class SymbolService:
    """Service for managing symbol mappings."""

    def __init__(self, session: AsyncSession):
        """Initialize the symbol service.
        
        Args:
            session: The database session.
        """
        self.session = session

    async def get_all_mappings(self) -> List[SymbolMapping]:
        """Get all symbol mappings.
        
        Returns:
            List of symbol mappings.
        """
        result = await self.session.execute(select(SymbolMapping))
        return result.scalars().all()

    async def get_mapping(self, standard_symbol: str) -> Optional[SymbolMapping]:
        """Get a symbol mapping by standard symbol.
        
        Args:
            standard_symbol: The standard symbol to look up.
            
        Returns:
            The symbol mapping if found, None otherwise.
        """
        result = await self.session.execute(
            select(SymbolMapping).where(SymbolMapping.standard_symbol == standard_symbol.upper())
        )
        return result.scalars().first()

    async def create_mapping(
        self, 
        standard_symbol: str,
        broker_symbol: str,
        broker_name: str,
        description: Optional[str] = None
    ) -> SymbolMapping:
        """Create a new symbol mapping.
        
        Args:
            standard_symbol: The standard symbol (e.g., EURUSD).
            broker_symbol: The broker's symbol (e.g., EURUSDm).
            broker_name: The name of the broker.
            description: Optional description of the mapping.
            
        Returns:
            The created symbol mapping.
        """
        mapping = SymbolMapping(
            standard_symbol=standard_symbol.upper(),
            broker_symbol=broker_symbol,
            broker_name=broker_name,
            description=description
        )
        self.session.add(mapping)
        await self.session.commit()
        return mapping

    async def update_mapping(
        self,
        standard_symbol: str,
        broker_symbol: Optional[str] = None,
        broker_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing symbol mapping.
        
        Args:
            standard_symbol: The standard symbol to update.
            broker_symbol: The new broker symbol.
            broker_name: The new broker name.
            description: The new description.
            
        Returns:
            True if the mapping was updated, False otherwise.
        """
        update_data = {}
        if broker_symbol is not None:
            update_data["broker_symbol"] = broker_symbol
        if broker_name is not None:
            update_data["broker_name"] = broker_name
        if description is not None:
            update_data["description"] = description

        if not update_data:
            return False

        result = await self.session.execute(
            update(SymbolMapping)
            .where(SymbolMapping.standard_symbol == standard_symbol.upper())
            .values(**update_data)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def delete_mapping(self, standard_symbol: str) -> bool:
        """Delete a symbol mapping.
        
        Args:
            standard_symbol: The standard symbol to delete.
            
        Returns:
            True if the mapping was deleted, False otherwise.
        """
        result = await self.session.execute(
            delete(SymbolMapping).where(SymbolMapping.standard_symbol == standard_symbol.upper())
        )
        await self.session.commit()
        return result.rowcount > 0

    def map_symbol(self, standard_symbol: str, broker_name: str) -> str:
        """Map a standard symbol to a broker symbol.
        
        Args:
            standard_symbol: The standard symbol to map.
            broker_name: The name of the broker.
            
        Returns:
            The broker symbol if found, otherwise returns the standard symbol.
        """
        result = self.session.execute(
            select(SymbolMapping).where(
                SymbolMapping.standard_symbol == standard_symbol.upper(),
                SymbolMapping.broker_name == broker_name
            )
        ).first()
        return result.broker_symbol if result else standard_symbol
