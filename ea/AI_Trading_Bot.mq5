//+------------------------------------------------------------------+
//|                                              AI_Trading_Bot.mq5 |
//|                                  Copyright 2024, AI Trading Bot |
//|                                             https://example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, AI Trading Bot"
#property link      "https://example.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

//--- Input Parameters
input string   API_ENDPOINT = "http://localhost:8000/api/v1/market-analysis/screenshot";
input string   API_KEY = "";
input int      SCREENSHOT_INTERVAL = 5;           // Minutes between screenshots
input bool     ENABLE_AUTO_SCREENSHOTS = true;    // Enable automatic screenshot capture
input bool     ENABLE_SIGNAL_EXECUTION = true;    // Enable automatic signal execution
input ulong    MAGIC_NUMBER = 1001;               // Magic number for trades
input double   MAX_RISK_PERCENT = 2.0;            // Maximum risk per trade
input int      MAX_DAILY_TRADES = 50;             // Maximum trades per day
input double   MAX_DAILY_LOSS = 25.0;             // Maximum daily loss in USD
input bool     ENABLE_TELEGRAM_ALERTS = true;     // Enable Telegram notifications
input bool     ENABLE_PARTIAL_TP = true;          // Enable partial take profit
input bool     ENABLE_TRAILING_STOP = true;       // Enable trailing stop

//--- Global Variables
datetime lastScreenshotTime = 0;
int screenshotCounter = 0;
int dailyTradeCount = 0;
double dailyLoss = 0.0;
datetime lastTradeTime = 0;
bool isConnected = false;
string lastError = "";

//--- Chart Template Settings
string chartTemplate = "SMC_Liquidity_Template.tpl";
string screenshotPath = "Screenshots\\";

//--- Trading Objects
CTrade trade;
CPositionInfo positionInfo;
COrderInfo orderInfo;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("AI Trading Bot EA Initialized (MT5)");
   
   // Initialize trading objects
   trade.SetExpertMagicNumber(MAGIC_NUMBER);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_FOK);
   trade.SetTypeFillingBySymbol(Symbol());
   
   // Create screenshot directory if it doesn't exist
   if(!FolderCreate(screenshotPath))
   {
      Print("Warning: Could not create screenshot directory");
   }
   
   // Apply chart template
   if(!ChartApplyTemplate(0, chartTemplate))
   {
      Print("Warning: Could not apply chart template");
   }
   
   // Set up chart indicators
   SetupChartIndicators();
   
   // Reset daily counters
   ResetDailyCounters();
   
   // Test API connection
   TestAPIConnection();
   
   // Set up timer for periodic operations
   EventSetTimer(60); // Check every minute
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("AI Trading Bot EA Deinitialized. Reason: ", reason);
   
   // Close all open positions if emergency stop
   if(reason == REASON_PROGRAM || reason == REASON_REMOVE)
   {
      CloseAllPositions();
   }
   
   // Remove timer
   EventKillTimer();
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check if it's time for screenshot
   if(ENABLE_AUTO_SCREENSHOTS && IsTimeForScreenshot())
   {
      CaptureAndSendScreenshot();
   }
   
   // Check for incoming signals
   if(ENABLE_SIGNAL_EXECUTION)
   {
      CheckForSignals();
   }
   
   // Update daily counters
   UpdateDailyCounters();
   
   // Check risk limits
   CheckRiskLimits();
   
   // Manage open positions
   ManageOpenPositions();
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Check for signals every minute
   if(ENABLE_SIGNAL_EXECUTION)
   {
      CheckForSignals();
   }
   
   // Update performance metrics
   UpdatePerformanceMetrics();
}

//+------------------------------------------------------------------+
//| Check if it's time for screenshot                               |
//+------------------------------------------------------------------+
bool IsTimeForScreenshot()
{
   datetime currentTime = TimeCurrent();
   
   // Check if enough time has passed since last screenshot
   if(currentTime - lastScreenshotTime >= SCREENSHOT_INTERVAL * 60)
   {
      // Check if market is active
      if(IsMarketActive())
      {
         return true;
      }
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Check if market is active                                        |
//+------------------------------------------------------------------+
bool IsMarketActive()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Avoid taking screenshots during low liquidity periods
   // Skip 22:00-02:00 UTC (low liquidity)
   if(dt.hour >= 22 || dt.hour < 2)
      return false;
   
   // Skip during news events (simplified check)
   if(IsHighImpactNewsTime())
      return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| Check if it's high impact news time                             |
//+------------------------------------------------------------------+
bool IsHighImpactNewsTime()
{
   // This is a simplified check - in production, integrate with news API
   // For now, avoid trading during major session overlaps
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // London-New York overlap: 13:00-17:00 UTC
   if(dt.hour >= 13 && dt.hour < 17)
      return false;
   
   // Asian session: 00:00-08:00 UTC
   if(dt.hour >= 0 && dt.hour < 8)
      return false;
   
   return false;
}

//+------------------------------------------------------------------+
//| Capture and send screenshot                                      |
//+------------------------------------------------------------------+
void CaptureAndSendScreenshot()
{
   string symbol = Symbol();
   string timeframe = GetTimeframeString();
   datetime timestamp = TimeCurrent();
   
   // Capture screenshot
   string filename = CaptureScreenshot(symbol, timeframe, timestamp);
   
   if(filename != "")
   {
      // Send to API
      if(SendScreenshotToAPI(filename, symbol, timeframe, timestamp))
      {
         lastScreenshotTime = timestamp;
         screenshotCounter++;
         Print("Screenshot captured and sent successfully: ", filename);
      }
      else
      {
         Print("Failed to send screenshot: ", lastError);
      }
   }
   else
   {
      Print("Failed to capture screenshot");
   }
}

//+------------------------------------------------------------------+
//| Capture screenshot of current chart                              |
//+------------------------------------------------------------------+
string CaptureScreenshot(string symbol, string timeframe, datetime timestamp)
{
   string filename = StringFormat("%s%s_%s_%s.png", 
                                 screenshotPath, 
                                 symbol, 
                                 timeframe, 
                                 TimeToString(timestamp, TIME_DATE|TIME_MINUTES));
   
   // Ensure chart is properly set up
   ChartRedraw(0);
   
   // Wait a moment for chart to render
   Sleep(1000);
   
   // Capture screenshot
   if(ChartScreenShot(0, filename, 1920, 1080, ALIGN_RIGHT))
   {
      return filename;
   }
   
   return "";
}

//+------------------------------------------------------------------+
//| Send screenshot to API                                           |
//+------------------------------------------------------------------+
bool SendScreenshotToAPI(string filename, string symbol, string timeframe, datetime timestamp)
{
   // Read screenshot file
   int fileHandle = FileOpen(filename, FILE_READ|FILE_BIN);
   if(fileHandle == INVALID_HANDLE)
   {
      lastError = "Could not open screenshot file";
      return false;
   }
   
   // Get file size
   long fileSize = FileGetSize(fileHandle);
   if(fileSize == 0)
   {
      lastError = "Screenshot file is empty";
      FileClose(fileHandle);
      return false;
   }
   
   // Read file content
   uchar fileContent[];
   ArrayResize(fileContent, (int)fileSize);
   FileReadArray(fileHandle, fileContent);
   FileClose(fileHandle);
   
   // Convert to base64 using the native CryptEncode function
   uchar base64Result[];
   if(CryptEncode(CRYPT_BASE64, fileContent, NULL, base64Result) <= 0)
   {
      lastError = "Base64 encoding failed. Error: " + IntegerToString(GetLastError());
      return false;
   }

   // Convert the uchar array result to a string
   string base64Data = CharArrayToString(base64Result);
   
   // Prepare market context
   string marketContext = GetMarketContext(symbol);
   
   // Create JSON payload
   string jsonPayload = CreateScreenshotPayload(symbol, timeframe, timestamp, base64Data, marketContext);
   
   // Send HTTP request
   string headers = "Content-Type: application/json\r\n";
   if(API_KEY != "")
      headers += "Authorization: Bearer " + API_KEY + "\r\n";
   
   char postData[];
   // Use StringToUtf8 instead of StringToCharArray for better JSON compatibility
   StringToUtf8(jsonPayload, postData);
   
   char response[];
   string response_headers;

   ResetLastError();
   int result = WebRequest("POST", API_ENDPOINT, headers, 5000, postData, response, response_headers);
   
   if(result == 200)
   {
      return true;
   }
   else
   {
      lastError = "HTTP request failed. Code: " + IntegerToString(result) + ", LastError: " + IntegerToString(GetLastError());
      return false;
   }
}

//+------------------------------------------------------------------+
//| Get market context for screenshot                                |
//+------------------------------------------------------------------+
string GetMarketContext(string symbol)
{
   double currentPrice = SymbolInfoDouble(symbol, SYMBOL_BID);
   string session = GetCurrentSession();
   string volatilityLevel = GetVolatilityLevel(symbol);
   string newsImpact = GetNewsImpact();
   
   return StringFormat("{\"current_price\":%.5f,\"session\":\"%s\",\"volatility_level\":\"%s\",\"news_impact\":\"%s\"}", 
                      currentPrice, session, volatilityLevel, newsImpact);
}

//+------------------------------------------------------------------+
//| Get current trading session                                      |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   if(dt.hour >= 0 && dt.hour < 8)
      return "asian";
   else if(dt.hour >= 8 && dt.hour < 16)
      return "london";
   else if(dt.hour >= 13 && dt.hour < 21)
      return "newyork";
   else
      return "overnight";
}

//+------------------------------------------------------------------+
//| Get volatility level                                             |
//+------------------------------------------------------------------+
string GetVolatilityLevel(string symbol)
{
   double atr[];
   ArraySetAsSeries(atr, true);
   
   int atrHandle = iATR(symbol, PERIOD_H1, 14);
   if(atrHandle != INVALID_HANDLE)
   {
      if(CopyBuffer(atrHandle, 0, 0, 1, atr) > 0)
      {
         double atrPercent = (atr[0] / SymbolInfoDouble(symbol, SYMBOL_BID)) * 100;
         
         if(atrPercent < 0.1)
            return "low";
         else if(atrPercent < 0.3)
            return "normal";
         else if(atrPercent < 0.5)
            return "high";
         else
            return "extreme";
      }
   }
   
   return "normal";
}

//+------------------------------------------------------------------+
//| Get news impact level                                            |
//+------------------------------------------------------------------+
string GetNewsImpact()
{
   // Simplified news impact detection
   // In production, integrate with news API
   return "low";
}

//+------------------------------------------------------------------+
//| Create screenshot payload JSON                                   |
//+------------------------------------------------------------------+
string CreateScreenshotPayload(string symbol, string timeframe, datetime timestamp, string imageData, string marketContext)
{
   string timestampStr = TimeToString(timestamp, TIME_DATE|TIME_SECONDS);
   
   return StringFormat("{\"symbol\":\"%s\",\"timeframe\":\"%s\",\"timestamp\":\"%s\",\"image_data\":\"%s\",\"market_context\":%s}", 
                      symbol, timeframe, timestampStr, imageData, marketContext);
}

//+------------------------------------------------------------------+
//| Check for incoming signals                                       |
//+------------------------------------------------------------------+
void CheckForSignals()
{
   // This function would poll the API for signals or receive webhooks
   // For now, we'll implement a simple polling mechanism
   
   static datetime lastSignalCheck = 0;
   datetime currentTime = TimeCurrent();
   
   // Check for signals every minute
   if(currentTime - lastSignalCheck >= 60)
   {
      // Poll API for signals
      string signals = PollForSignals();
      
      if(signals != "")
      {
         ProcessSignals(signals);
      }
      
      lastSignalCheck = currentTime;
   }
}

//+------------------------------------------------------------------+
//| Poll API for signals                                             |
//+------------------------------------------------------------------+
string PollForSignals()
{
   string headers = "Content-Type: application/json\r\n";
   if(API_KEY != "")
      headers += "Authorization: Bearer " + API_KEY + "\r\n";
   
   char response[];
   char postData[];
   
   int result = WebRequest("GET", API_ENDPOINT + "/signals", headers, 5000, postData, response, headers);
   
   if(result == 200)
   {
      return CharArrayToString(response);
   }
   
   return "";
}

//+------------------------------------------------------------------+
//| A simple helper to find a value for a key in a JSON string.      |
//| This is not a full JSON parser. It's for a specific structure.   |
//+------------------------------------------------------------------+
string ParseJsonValue(string json, string key)
{
    string search_key = "\"" + key + "\":";
    int key_pos = StringFind(json, search_key);
    if(key_pos < 0) return "";

    int value_start = key_pos + StringLen(search_key);
    int value_end = -1;
    string value = "";

    // Trim leading spaces
    while(StringGetCharacter(json, value_start) == ' ' || StringGetCharacter(json, value_start) == '\n')
        value_start++;

    // Check if value is a string (starts with ")
    if(StringGetCharacter(json, value_start) == '"')
    {
        value_start++;
        value_end = StringFind(json, "\"", value_start);
        if(value_end < 0) return "";
        value = StringSubstr(json, value_start, value_end - value_start);
    }
    // Check if value is an array or object (starts with [ or {)
    else if(StringGetCharacter(json, value_start) == '[' || StringGetCharacter(json, value_start) == '{')
    {
        char open_char = StringGetCharacter(json, value_start);
        char close_char = (open_char == '[') ? ']' : '}';
        int bracket_level = 1;
        for(int i = value_start + 1; i < StringLen(json); i++)
        {
            if(StringGetCharacter(json, i) == open_char) bracket_level++;
            if(StringGetCharacter(json, i) == close_char) bracket_level--;
            if(bracket_level == 0)
            {
                value_end = i;
                break;
            }
        }
        if(value_end < 0) return "";
        value = StringSubstr(json, value_start, value_end - value_start + 1);
    }
    // Otherwise, assume it's a number or boolean
    else
    {
        value_end = StringFind(json, ",", value_start);
        int brace_end = StringFind(json, "}", value_start);
        if (value_end < 0 || (brace_end >= 0 && brace_end < value_end)) value_end = brace_end;
        if (value_end < 0) return "";
        value = StringSubstr(json, value_start, value_end - value_start);
    }

    return StringTrim(value);
}

//+------------------------------------------------------------------+
//| Process incoming signals using the custom JSON parser            |
//+------------------------------------------------------------------+
void ProcessSignals(string signalsJson)
{
    string signals_array_str = ParseJsonValue(signalsJson, "signals");
    if(signals_array_str == "") return;

    // This is a simplified loop for one signal in the array for now
    string signal_object = StringSubstr(signals_array_str, 1, StringLen(signals_array_str) - 2); // Strip [ and ]

    if(StringLen(signal_object) < 10) return; // Not a real object

    string signal_symbol = ParseJsonValue(signal_object, "symbol");

    // Only process signals for the current chart symbol
    if(signal_symbol != Symbol()) return;

    // Extract all required fields from the signal
    string signal_type = ParseJsonValue(signal_object, "type");
    string entry_style = ParseJsonValue(signal_object, "entry_style");
    string entry_zone_str = ParseJsonValue(signal_object, "entry_zone");
    string sl_str = ParseJsonValue(signal_object, "sl");
    string tp_arr_str = ParseJsonValue(signal_object, "tp");

    // --- Parse numeric and array values ---
    double stop_loss = StringToDouble(sl_str);

    // Parse the first TP from the array string e.g., "[3336.0, 3330.5]"
    int first_comma = StringFind(tp_arr_str, ",");
    if(first_comma < 0) first_comma = StringFind(tp_arr_str, "]");
    string tp1_str = StringSubstr(tp_arr_str, 1, first_comma - 1);
    double take_profit = StringToDouble(tp1_str);

    // Parse entry zone array e.g., "[1955.0, 1956.0]"
    int zone_comma = StringFind(entry_zone_str, ",");
    string ez1_str = StringSubstr(entry_zone_str, 1, zone_comma - 1);
    string ez2_str = StringSubstr(entry_zone_str, zone_comma + 1, StringFind(entry_zone_str, "]") - zone_comma - 1);
    double entry_zone_low = StringToDouble(ez1_str);
    double entry_zone_high = StringToDouble(ez2_str);


    if(signal_type == "BUY")
    {
        ExecuteBuySignal(entry_style, entry_zone_low, entry_zone_high, stop_loss, take_profit);
    }
    else if(signal_type == "SELL")
    {
        ExecuteSellSignal(entry_style, entry_zone_low, entry_zone_high, stop_loss, take_profit);
    }
}

//+------------------------------------------------------------------+
//| Execute buy signal with parsed data                              |
//+------------------------------------------------------------------+
void ExecuteBuySignal(string style, double ez_low, double ez_high, double stopLoss, double takeProfit)
{
    if(!CanOpenNewPosition()) return;
    if(stopLoss <= 0 || takeProfit <= 0 || ez_high <= 0) return;

    double lotSize = CalculateLotSize(stopLoss);
    if(lotSize <= 0) return;

    string result_msg = "";
    bool success = false;

    if(style == "market")
    {
        double price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
        success = trade.Buy(lotSize, Symbol(), price, stopLoss, takeProfit, "AI Market Buy");
        result_msg = "Market Buy order placed.";
    }
    else if(style == "limit")
    {
        // For a Buy Limit, we want to buy at a price lower than current market price.
        // We use the lower of the two entry zone prices.
        double price = MathMin(ez_low, ez_high);
        success = trade.BuyLimit(lotSize, price, Symbol(), stopLoss, takeProfit, 0, 0, "AI Limit Buy");
        result_msg = "Buy Limit order placed at " + DoubleToString(price, _Digits);
    }
    else if(style == "stop")
    {
        // For a Buy Stop, we want to buy at a price higher than current market price.
        // We use the higher of the two entry zone prices.
        double price = MathMax(ez_low, ez_high);
        success = trade.BuyStop(lotSize, price, Symbol(), stopLoss, takeProfit, 0, 0, "AI Stop Buy");
        result_msg = "Buy Stop order placed at " + DoubleToString(price, _Digits);
    }

    if(success)
    {
        Print(result_msg);
        dailyTradeCount++;
        lastTradeTime = TimeCurrent();
        if(ENABLE_TELEGRAM_ALERTS)
            SendTelegramAlert("BUY " + style, trade.ResultPrice(), stopLoss, takeProfit, lotSize);
    }
    else
    {
        Print("Buy order failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Execute sell signal with parsed data                             |
//+------------------------------------------------------------------+
void ExecuteSellSignal(string style, double ez_low, double ez_high, double stopLoss, double takeProfit)
{
    if(!CanOpenNewPosition()) return;
    if(stopLoss <= 0 || takeProfit <= 0 || ez_high <= 0) return;

    double lotSize = CalculateLotSize(stopLoss);
    if(lotSize <= 0) return;

    string result_msg = "";
    bool success = false;

    if(style == "market")
    {
        double price = SymbolInfoDouble(Symbol(), SYMBOL_BID);
        success = trade.Sell(lotSize, Symbol(), price, stopLoss, takeProfit, "AI Market Sell");
        result_msg = "Market Sell order placed.";
    }
    else if(style == "limit")
    {
        // For a Sell Limit, we want to sell at a price higher than current market price.
        // We use the higher of the two entry zone prices.
        double price = MathMax(ez_low, ez_high);
        success = trade.SellLimit(lotSize, price, Symbol(), stopLoss, takeProfit, 0, 0, "AI Limit Sell");
        result_msg = "Sell Limit order placed at " + DoubleToString(price, _Digits);
    }
    else if(style == "stop")
    {
        // For a Sell Stop, we want to sell at a price lower than current market price.
        // We use the lower of the two entry zone prices.
        double price = MathMin(ez_low, ez_high);
        success = trade.SellStop(lotSize, price, Symbol(), stopLoss, takeProfit, 0, 0, "AI Stop Sell");
        result_msg = "Sell Stop order placed at " + DoubleToString(price, _Digits);
    }

    if(success)
    {
        Print(result_msg);
        dailyTradeCount++;
        lastTradeTime = TimeCurrent();
        if(ENABLE_TELEGRAM_ALERTS)
            SendTelegramAlert("SELL " + style, trade.ResultPrice(), stopLoss, takeProfit, lotSize);
    }
    else
    {
        Print("Sell order failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Check if can open new position                                   |
//+------------------------------------------------------------------+
bool CanOpenNewPosition()
{
   // Check daily trade limit
   if(dailyTradeCount >= MAX_DAILY_TRADES)
   {
      Print("Daily trade limit reached");
      return false;
   }
   
   // Check daily loss limit
   if(dailyLoss <= -MAX_DAILY_LOSS)
   {
      Print("Daily loss limit reached");
      return false;
   }
   
   // Check open positions
   if(CountOpenPositions() >= 10)
   {
      Print("Maximum open positions reached");
      return false;
   }
   
   return true;
}

//+------------------------------------------------------------------+
//| Count open positions                                             |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == Symbol() && positionInfo.Magic() == MAGIC_NUMBER)
         {
            count++;
         }
      }
   }
   
   return count;
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk                                |
//+------------------------------------------------------------------+
double CalculateLotSize(double stopLoss)
{
   double accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = accountBalance * MAX_RISK_PERCENT / 100;
   
   double stopLossPoints = MathAbs(stopLoss - SymbolInfoDouble(Symbol(), SYMBOL_BID));
   double tickValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
   
   if(tickValue > 0 && stopLossPoints > 0)
   {
      double lotSize = riskAmount / (stopLossPoints * tickValue);
      lotSize = NormalizeDouble(lotSize, 2);
      
      // Ensure lot size is within limits
      double minLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
      double maxLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
      
      if(lotSize < minLot) lotSize = minLot;
      if(lotSize > maxLot) lotSize = maxLot;
      
      return lotSize;
   }
   
   return 0;
}

// Obsolete parsing functions removed. Logic is now handled in ProcessSignals.

//+------------------------------------------------------------------+
//| Send Telegram alert                                              |
//+------------------------------------------------------------------+
void SendTelegramAlert(string action, double entry, double sl, double tp, double lot)
{
   // This would integrate with Telegram Bot API
   // For now, just print to log
   Print("Telegram Alert: ", action, " ", Symbol(), " Entry: ", entry, " SL: ", sl, " TP: ", tp, " Lot: ", lot);
}

//+------------------------------------------------------------------+
//| Setup chart indicators                                           |
//+------------------------------------------------------------------+
void SetupChartIndicators()
{
   // Add ATR indicator
   int atrHandle = iATR(Symbol(), PERIOD_CURRENT, 14);
   
   // Add volume profile (if available)
   // Add support/resistance levels
   
   Print("Chart indicators setup completed");
}

//+------------------------------------------------------------------+
//| Get timeframe string                                             |
//+------------------------------------------------------------------+
string GetTimeframeString()
{
   ENUM_TIMEFRAMES period = Period();
   
   switch(period)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
      default: return "M1";
   }
}

//+------------------------------------------------------------------+
//| Reset daily counters                                             |
//+------------------------------------------------------------------+
void ResetDailyCounters()
{
   static datetime lastResetDay = 0;
   datetime currentDay = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));
   
   if(currentDay != lastResetDay)
   {
      dailyTradeCount = 0;
      dailyLoss = 0.0;
      lastResetDay = currentDay;
      Print("Daily counters reset");
   }
}

//+------------------------------------------------------------------+
//| Update daily counters                                            |
//+------------------------------------------------------------------+
void UpdateDailyCounters()
{
   // Update daily loss calculation
   dailyLoss = CalculateDailyLoss();
}

//+------------------------------------------------------------------+
//| Calculate daily loss                                             |
//+------------------------------------------------------------------+
double CalculateDailyLoss()
{
   double totalLoss = 0.0;
   
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong dealTicket = HistoryDealGetTicket(i);
      if(dealTicket > 0)
      {
         if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) == Symbol() && 
            HistoryDealGetInteger(dealTicket, DEAL_MAGIC) == MAGIC_NUMBER)
         {
            datetime dealTime = (datetime)HistoryDealGetInteger(dealTicket, DEAL_TIME);
            if(TimeDay(dealTime) == TimeDay(TimeCurrent()))
            {
               totalLoss += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
            }
         }
      }
   }
   
   return totalLoss;
}

//+------------------------------------------------------------------+
//| Check risk limits                                                |
//+------------------------------------------------------------------+
void CheckRiskLimits()
{
   // Check if daily loss limit exceeded
   if(dailyLoss <= -MAX_DAILY_LOSS)
   {
      Print("Daily loss limit exceeded. Closing all positions.");
      CloseAllPositions();
   }
   
   // Check if too many consecutive losses
   if(GetConsecutiveLosses() >= 4)
   {
      Print("Too many consecutive losses. Pausing trading.");
      // Implement trading pause logic
   }
}

//+------------------------------------------------------------------+
//| Get consecutive losses                                           |
//+------------------------------------------------------------------+
int GetConsecutiveLosses()
{
   int consecutiveLosses = 0;
   
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong dealTicket = HistoryDealGetTicket(i);
      if(dealTicket > 0)
      {
         if(HistoryDealGetString(dealTicket, DEAL_SYMBOL) == Symbol() && 
            HistoryDealGetInteger(dealTicket, DEAL_MAGIC) == MAGIC_NUMBER)
         {
            if(HistoryDealGetDouble(dealTicket, DEAL_PROFIT) < 0)
            {
               consecutiveLosses++;
            }
            else
            {
               break;
            }
         }
      }
   }
   
   return consecutiveLosses;
}

//+------------------------------------------------------------------+
//| Close all positions                                              |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == Symbol() && positionInfo.Magic() == MAGIC_NUMBER)
         {
            if(trade.PositionClose(positionInfo.Ticket()))
            {
               Print("Position closed: Ticket ", positionInfo.Ticket());
            }
            else
            {
               Print("Failed to close position: ", trade.ResultRetcodeDescription());
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage open positions                                            |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(positionInfo.Symbol() == Symbol() && positionInfo.Magic() == MAGIC_NUMBER)
         {
            // Check for partial TP
            if(ENABLE_PARTIAL_TP)
               CheckPartialTakeProfit();
            
            // Check for trailing stop
            if(ENABLE_TRAILING_STOP)
               CheckTrailingStop();
            
            // Check for breakeven
            CheckBreakeven();
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check partial take profit                                        |
//+------------------------------------------------------------------+
void CheckPartialTakeProfit()
{
   // Implement partial take profit logic
   // Close 50% of position when R:R reaches 1.5
}

//+------------------------------------------------------------------+
//| Check trailing stop                                               |
//+------------------------------------------------------------------+
void CheckTrailingStop()
{
   // Implement trailing stop logic
   // Start trailing after R:R reaches 1.0
}

//+------------------------------------------------------------------+
//| Check breakeven                                                  |
//+------------------------------------------------------------------+
void CheckBreakeven()
{
   // Implement breakeven logic
   // Move SL to entry when R:R reaches 1.0
}

//+------------------------------------------------------------------+
//| Update performance metrics                                       |
//+------------------------------------------------------------------+
void UpdatePerformanceMetrics()
{
   // Update various performance metrics
   // This could include win rate, profit factor, etc.
}

//+------------------------------------------------------------------+
//| Test API connection                                              |
//+------------------------------------------------------------------+
void TestAPIConnection()
{
   string headers = "Content-Type: application/json\r\n";
   char response[];
   char postData[];
   
   int result = WebRequest("GET", API_ENDPOINT + "/health", headers, 5000, postData, response, headers);
   
   if(result == 200)
   {
      isConnected = true;
      Print("API connection test successful");
   }
   else
   {
      isConnected = false;
      Print("API connection test failed: ", result);
   }
}

// The incorrect Base64Encode function has been removed.
// The native MQL5 CryptEncode(CRYPT_BASE64,...) is now used instead.
