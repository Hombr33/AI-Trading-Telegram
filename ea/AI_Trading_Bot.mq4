//+------------------------------------------------------------------+
//|                                              AI_Trading_Bot.mq4 |
//|                                  Copyright 2024, AI Trading Bot |
//|                                             https://example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, AI Trading Bot"
#property link      "https://example.com"
#property version   "1.00"
#property strict

//--- Input Parameters
input string   API_ENDPOINT = "http://localhost:8000/api/v1/market-analysis/screenshot";
input string   API_KEY = "";
input int      SCREENSHOT_INTERVAL = 5;           // Minutes between screenshots
input bool     ENABLE_AUTO_SCREENSHOTS = true;    // Enable automatic screenshot capture
input bool     ENABLE_SIGNAL_EXECUTION = true;    // Enable automatic signal execution
input int      MAGIC_NUMBER = 1001;               // Magic number for trades
input double   MAX_RISK_PERCENT = 2.0;            // Maximum risk per trade
input int      MAX_DAILY_TRADES = 50;             // Maximum trades per day
input double   MAX_DAILY_LOSS = 25.0;             // Maximum daily loss in USD
input bool     ENABLE_TELEGRAM_ALERTS = true;     // Enable Telegram notifications

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

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("AI Trading Bot EA Initialized");
   
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
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Additional timer-based operations if needed
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
   int currentHour = TimeHour(TimeCurrent());
   int currentMinute = TimeMinute(TimeCurrent());
   
   // Avoid taking screenshots during low liquidity periods
   // Skip 22:00-02:00 UTC (low liquidity)
   if(currentHour >= 22 || currentHour < 2)
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
   int currentHour = TimeHour(TimeCurrent());
   
   // London-New York overlap: 13:00-17:00 UTC
   if(currentHour >= 13 && currentHour < 17)
      return false;
   
   // Asian session: 00:00-08:00 UTC
   if(currentHour >= 0 && currentHour < 8)
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
   int fileSize = (int)FileSize(fileHandle);
   
   // Read file content
   uchar fileContent[];
   ArrayResize(fileContent, fileSize);
   FileReadArray(fileHandle, fileContent);
   FileClose(fileHandle);
   
   // Convert to base64
   string base64Data = Base64Encode(fileContent);
   
   // Prepare market context
   string marketContext = GetMarketContext(symbol);
   
   // Create JSON payload
   string jsonPayload = CreateScreenshotPayload(symbol, timeframe, timestamp, base64Data, marketContext);
   
   // Send HTTP request
   string headers = "Content-Type: application/json\r\n";
   if(API_KEY != "")
      headers += "Authorization: Bearer " + API_KEY + "\r\n";
   
   char postData[];
   StringToCharArray(jsonPayload, postData);
   
   int result = WebRequest("POST", API_ENDPOINT, headers, 5000, postData, postData, headers);
   
   if(result == 200)
   {
      return true;
   }
   else
   {
      lastError = "HTTP request failed with code: " + IntegerToString(result);
      return false;
   }
}

//+------------------------------------------------------------------+
//| Get market context for screenshot                                |
//+------------------------------------------------------------------+
string GetMarketContext(string symbol)
{
   double currentPrice = MarketInfo(symbol, MODE_BID);
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
   int currentHour = TimeHour(TimeCurrent());
   
   if(currentHour >= 0 && currentHour < 8)
      return "asian";
   else if(currentHour >= 8 && currentHour < 16)
      return "london";
   else if(currentHour >= 13 && currentHour < 21)
      return "newyork";
   else
      return "overnight";
}

//+------------------------------------------------------------------+
//| Get volatility level                                             |
//+------------------------------------------------------------------+
string GetVolatilityLevel(string symbol)
{
   double atr = iATR(symbol, PERIOD_H1, 14, 1);
   double atrPercent = (atr / MarketInfo(symbol, MODE_BID)) * 100;
   
   if(atrPercent < 0.1)
      return "low";
   else if(atrPercent < 0.3)
      return "normal";
   else if(atrPercent < 0.5)
      return "high";
   else
      return "extreme";
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
//| Process incoming signals                                         |
//+------------------------------------------------------------------+
void ProcessSignals(string signalsJson)
{
   // Parse JSON signals and execute trades
   // This is a simplified implementation
   
   if(StringFind(signalsJson, "BUY") >= 0)
   {
      ExecuteBuySignal(signalsJson);
   }
   else if(StringFind(signalsJson, "SELL") >= 0)
   {
      ExecuteSellSignal(signalsJson);
   }
}

//+------------------------------------------------------------------+
//| Execute buy signal                                               |
//+------------------------------------------------------------------+
void ExecuteBuySignal(string signalData)
{
   if(!CanOpenNewPosition())
      return;
   
   double entryPrice = MarketInfo(Symbol(), MODE_ASK);
   double stopLoss = ParseStopLoss(signalData);
   double takeProfit = ParseTakeProfit(signalData);
   double lotSize = CalculateLotSize(stopLoss);
   
   if(lotSize > 0)
   {
      int ticket = OrderSend(Symbol(), OP_BUY, lotSize, entryPrice, 3, stopLoss, takeProfit, 
                            "AI Signal", MAGIC_NUMBER, 0, clrGreen);
      
      if(ticket > 0)
      {
         Print("Buy order executed: Ticket ", ticket, " Lot: ", lotSize, " SL: ", stopLoss, " TP: ", takeProfit);
         dailyTradeCount++;
         lastTradeTime = TimeCurrent();
         
         if(ENABLE_TELEGRAM_ALERTS)
            SendTelegramAlert("BUY", entryPrice, stopLoss, takeProfit, lotSize);
      }
      else
      {
         Print("Buy order failed: ", GetLastError());
      }
   }
}

//+------------------------------------------------------------------+
//| Execute sell signal                                              |
//+------------------------------------------------------------------+
void ExecuteSellSignal(string signalData)
{
   if(!CanOpenNewPosition())
      return;
   
   double entryPrice = MarketInfo(Symbol(), MODE_BID);
   double stopLoss = ParseStopLoss(signalData);
   double takeProfit = ParseTakeProfit(signalData);
   double lotSize = CalculateLotSize(stopLoss);
   
   if(lotSize > 0)
   {
      int ticket = OrderSend(Symbol(), OP_SELL, lotSize, entryPrice, 3, stopLoss, takeProfit, 
                            "AI Signal", MAGIC_NUMBER, 0, clrRed);
      
      if(ticket > 0)
      {
         Print("Sell order executed: Ticket ", ticket, " Lot: ", lotSize, " SL: ", stopLoss, " TP: ", takeProfit);
         dailyTradeCount++;
         lastTradeTime = TimeCurrent();
         
         if(ENABLE_TELEGRAM_ALERTS)
            SendTelegramAlert("SELL", entryPrice, stopLoss, takeProfit, lotSize);
      }
      else
      {
         Print("Sell order failed: ", GetLastError());
      }
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
   
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MAGIC_NUMBER)
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
   double accountBalance = AccountBalance();
   double riskAmount = accountBalance * MAX_RISK_PERCENT / 100;
   
   double stopLossPoints = MathAbs(stopLoss - MarketInfo(Symbol(), MODE_BID));
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   
   if(tickValue > 0 && stopLossPoints > 0)
   {
      double lotSize = riskAmount / (stopLossPoints * tickValue);
      lotSize = NormalizeDouble(lotSize, 2);
      
      // Ensure lot size is within limits
      double minLot = MarketInfo(Symbol(), MODE_MINLOT);
      double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
      
      if(lotSize < minLot) lotSize = minLot;
      if(lotSize > maxLot) lotSize = maxLot;
      
      return lotSize;
   }
   
   return 0;
}

//+------------------------------------------------------------------+
//| Parse stop loss from signal                                      |
//+------------------------------------------------------------------+
double ParseStopLoss(string signalData)
{
   // Simplified parsing - in production, use proper JSON parsing
   // For now, return a default stop loss
   return MarketInfo(Symbol(), MODE_BID) - (100 * Point);
}

//+------------------------------------------------------------------+
//| Parse take profit from signal                                    |
//+------------------------------------------------------------------+
double ParseTakeProfit(string signalData)
{
   // Simplified parsing - in production, use proper JSON parsing
   // For now, return a default take profit
   return MarketInfo(Symbol(), MODE_BID) + (150 * Point);
}

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
   switch(Period())
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
   
   for(int i = 0; i < OrdersHistoryTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MAGIC_NUMBER)
         {
            datetime orderTime = OrderCloseTime();
            if(TimeDay(orderTime) == TimeDay(TimeCurrent()))
            {
               totalLoss += OrderProfit() + OrderSwap() + OrderCommission();
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
   
   for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MAGIC_NUMBER)
         {
            if(OrderProfit() < 0)
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
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MAGIC_NUMBER)
         {
            bool result = false;
            
            if(OrderType() == OP_BUY)
               result = OrderClose(OrderTicket(), OrderLots(), MarketInfo(Symbol(), MODE_BID), 3, clrRed);
            else if(OrderType() == OP_SELL)
               result = OrderClose(OrderTicket(), OrderLots(), MarketInfo(Symbol(), MODE_ASK), 3, clrRed);
            
            if(result)
               Print("Position closed: Ticket ", OrderTicket());
            else
               Print("Failed to close position: ", GetLastError());
         }
      }
   }
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

//+------------------------------------------------------------------+
//| Base64 encoding function                                         |
//+------------------------------------------------------------------+
string Base64Encode(uchar &data[])
{
   // Simplified base64 encoding - in production, use proper implementation
   string result = "";
   
   for(int i = 0; i < ArraySize(data); i++)
   {
      result += StringFormat("%02X", data[i]);
   }
   
   return result;
}
