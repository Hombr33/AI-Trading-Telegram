"""Symbol service for managing symbol mappings."""

from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.models.symbol_mappings import SymbolMapping

logger = get_logger(__name__)


class SymbolService:
    """Service for managing symbol mappings."""

    def __init__(self, session: Session):
        """Initialize the symbol service.

        Args:
            session: The database session.
        """
        self.session = session

    def get_all_mappings(
        self, broker_name: Optional[str] = None
    ) -> List[SymbolMapping]:
        """Get all symbol mappings, optionally filtered by broker.

        Args:
            broker_name: Optional broker name to filter by.

        Returns:
            List of symbol mappings.
        """
        query = select(SymbolMapping)
        if broker_name:
            query = query.where(SymbolMapping.broker_name == broker_name)

        result = self.session.execute(query)
        return result.scalars().all()

    def get_mapping(
        self, standard_symbol: str, broker_name: str
    ) -> Optional[SymbolMapping]:
        """Get a symbol mapping by standard symbol and broker name.

        Args:
            standard_symbol: The standard symbol to look up.
            broker_name: The broker name to look up.

        Returns:
            The symbol mapping if found, None otherwise.
        """
        result = self.session.execute(
            select(SymbolMapping).where(
                SymbolMapping.standard_symbol == standard_symbol.upper(),
                SymbolMapping.broker_name == broker_name,
            )
        )
        return result.scalars().first()

    def create_mapping(
        self,
        standard_symbol: str,
        broker_symbol: str,
        broker_name: str,
        description: Optional[str] = None,
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
            description=description,
        )
        self.session.add(mapping)
        self.session.commit()
        return mapping

    def update_mapping(
        self,
        standard_symbol: str,
        broker_symbol: str,
        broker_name: str,
        description: Optional[str] = None,
    ) -> bool:
        """Update an existing symbol mapping.

        Args:
            standard_symbol: The standard symbol to update.
            broker_symbol: The new broker symbol.
            broker_name: The broker name.
            description: The new description.

        Returns:
            True if the mapping was updated, False otherwise.
        """
        result = self.session.execute(
            update(SymbolMapping)
            .where(
                SymbolMapping.standard_symbol == standard_symbol.upper(),
                SymbolMapping.broker_name == broker_name,
            )
            .values(broker_symbol=broker_symbol, description=description)
        )
        self.session.commit()
        return result.rowcount > 0

    def delete_mapping(self, standard_symbol: str, broker_name: str) -> bool:
        """Delete a symbol mapping.

        Args:
            standard_symbol: The standard symbol to delete.
            broker_name: The broker name.

        Returns:
            True if the mapping was deleted, False otherwise.
        """
        result = self.session.execute(
            delete(SymbolMapping).where(
                SymbolMapping.standard_symbol == standard_symbol.upper(),
                SymbolMapping.broker_name == broker_name,
            )
        )
        self.session.commit()
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
                SymbolMapping.broker_name == broker_name,
            )
        )
        mapping = result.scalars().first()
        return mapping.broker_symbol if mapping else standard_symbol
