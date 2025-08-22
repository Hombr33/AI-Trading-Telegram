from pydantic import BaseModel, Field

# --- Pydantic Models for API Data Validation ---


class MarketContext(BaseModel):
    current_price: float
    session: str
    volatility_level: str
    news_impact: str


class ScreenshotPayload(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str  # MQL5 sends a string timestamp
    image_data: str = Field(..., description="Base64 encoded screenshot data")
    market_context: MarketContext


class SignalSetup(BaseModel):
    type: str  # "BUY" or "SELL"
    entry_zone: list[float]
    entry_style: str
    sl: float
    tp: list[float]
    confidence: int
    notes: str


class SignalResponse(BaseModel):
    symbol: str
    bias: str
    setups: list[SignalSetup]


class SignalListResponse(BaseModel):
    signals: list[SignalResponse]
