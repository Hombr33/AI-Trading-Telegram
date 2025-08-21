import base64
import datetime
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Trading Bot API",
    version="1.0.0",
    description="API for the AI Trading Bot system, integrating with MT5 and OpenAI.",
)

# --- Pydantic Models for Data Validation ---

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


@app.get("/health", status_code=200)
async def health_check():
    """
    Health check endpoint to confirm the API is running.
    This is used by the EA to test the connection.
    """
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}


@app.post("/api/v1/market-analysis/screenshot", status_code=201)
async def receive_screenshot(payload: ScreenshotPayload):
    """
    Receives a screenshot from the MT5 EA, decodes it, and saves it.
    This is the primary endpoint for the EA to submit market data for analysis.
    """
    logger.info(f"Received screenshot for {payload.symbol} on timeframe {payload.timeframe}")

    try:
        # Decode the Base64 image data
        image_bytes = base64.b64decode(payload.image_data)

        # Generate a unique filename
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"uploads/{payload.symbol}_{payload.timeframe}_{now}.png"

        # Save the image file
        with open(filename, "wb") as f:
            f.write(image_bytes)

        logger.info(f"Successfully saved screenshot to {filename}")

        # In the next phase, this will trigger the AI analysis
        # For now, we just confirm receipt and save the file.
        return {
            "message": "Screenshot received and saved successfully",
            "filename": filename,
        }

    except base64.binascii.Error as e:
        logger.error(f"Failed to decode Base64 image: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Base64 data: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing the screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


@app.get("/api/v1/market-analysis/signals", response_model=SignalListResponse)
async def get_signals():
    """
    Provides trading signals to the MT5 EA.
    For now, it returns a hardcoded mock signal for testing purposes.
    The EA will poll this endpoint periodically.
    """
    logger.info("Signal endpoint was called by a client.")

    # This is a mock signal. In the future, this will come from a database
    # or a live signal generation process.
    mock_signal = {
        "signals": [
            {
                "symbol": "XAUUSD",
                "bias": "BEARISH",
                "setups": [
                    {
                        "type": "SELL",
                        "entry_zone": [1955.0, 1956.0],
                        "entry_style": "limit",
                        "sl": 1960.0,
                        "tp": [1950.0, 1945.0],
                        "confidence": 75,
                        "notes": "Mock signal for testing."
                    }
                ]
            }
        ]
    }
    return mock_signal
