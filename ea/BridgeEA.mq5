//+------------------------------------------------------------------+
//|                                                    BridgeEA.mq5 |
//|                                  Copyright 2025, AI Trading Bot |
//|                                             https://example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, AI Trading Bot"
#property link      "https://example.com"
#property version   "1.10"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\SymbolInfo.mqh>

#define INT_MAX 2147483647

//--- Input Parameters
input string   BRIDGE_TOKEN = "";                    // Bridge authentication token
input string   API_ENDPOINT = "http://127.0.0.1:8000"; // API endpoint
input int      HEARTBEAT_INTERVAL = 5;               // Heartbeat interval (seconds)
input int      POSITION_SNAPSHOT_INTERVAL = 30;      // Position snapshot interval (seconds)
input int      SCREENSHOT_INTERVAL = 300;            // Screenshot interval (seconds) - 5 minutes
input bool     ENABLE_TICK_STREAMING = true;         // Enable tick streaming
input bool     ENABLE_SCREENSHOT_ANALYSIS = true;    // Enable screenshot analysis
input bool     ENABLE_AUTO_RECONNECT = true;         // Enable auto-reconnection
input int      MAX_RETRY_ATTEMPTS = 3;               // Maximum retry attempts
input int      RETRY_DELAY_MS = 250;                 // Retry delay in milliseconds
input bool     ENABLE_ORDER_EXECUTION = true;        // Enable order execution from Python
input bool     ENABLE_TRAILING_MANAGEMENT = true;    // Enable trailing stop management

//--- Global Variables
datetime lastHeartbeatTime = 0;
datetime lastPositionSnapshotTime = 0;
datetime lastScreenshotTime = 0;
datetime lastTickTime = 0;
bool isConnected = false;
int retryCount = 0;
string lastError = "";
string terminalId = "";
string accountNumber = "";
string screenshotPath = "";

//--- Trading Objects
CTrade trade;
CPositionInfo positionInfo;
COrderInfo orderInfo;
CSymbolInfo symbolInfo;

//--- HTTP Request Objects
string headers = "";

//--- Order Execution Variables
bool orderExecutionEnabled = true;
bool trailingManagementEnabled = true;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("BridgeEA MT5 Initialized");

    // Initialize trading objects
    trade.SetExpertMagicNumber(1001);
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);

    // Get terminal and account information
    terminalId = TerminalInfoString(TERMINAL_NAME);
    accountNumber = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));

    // Initialize screenshot path
    screenshotPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\Screenshots\\";

    // Set up headers for authentication
    headers = "Content-Type: application/json\r\n";
    if(BRIDGE_TOKEN != "")
    {
        headers += "Authorization: Bearer " + BRIDGE_TOKEN + "\r\n";
    }

    // Test connection
    TestConnection();

    Print("Screenshot path: " + screenshotPath);
    Print("Order execution enabled: " + (ENABLE_ORDER_EXECUTION ? "Yes" : "No"));
    Print("Trailing management enabled: " + (ENABLE_TRAILING_MANAGEMENT ? "Yes" : "No"));

    // Set up timer for periodic operations
    EventSetTimer(1); // Check every second

    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("BridgeEA MT5 Deinitialized");

    // Remove timer
    EventKillTimer();
}



//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Send heartbeat
   if(TimeCurrent() - lastHeartbeatTime >= HEARTBEAT_INTERVAL)
   {
      SendHeartbeat();
      lastHeartbeatTime = TimeCurrent();
   }

   // Send position snapshot
   if(TimeCurrent() - lastPositionSnapshotTime >= POSITION_SNAPSHOT_INTERVAL)
   {
      SendPositionSnapshot();
      lastPositionSnapshotTime = TimeCurrent();
   }

   // Send tick data if enabled
   if(ENABLE_TICK_STREAMING && (TimeCurrent() - lastTickTime) >= 1)
   {
      SendTickData();
      lastTickTime = TimeCurrent();
   }

   // Check for incoming orders from Python
   if(ENABLE_ORDER_EXECUTION)
   {
      CheckForIncomingOrders();
   }

   // Manage trailing stops if enabled
   if(ENABLE_TRAILING_MANAGEMENT)
   {
      ManageTrailingStops();
   }

   // Take and send screenshot for AI analysis
   if(ENABLE_SCREENSHOT_ANALYSIS && (TimeCurrent() - lastScreenshotTime >= SCREENSHOT_INTERVAL))
   {
      TakeAndSendScreenshot();
      lastScreenshotTime = TimeCurrent();
   }

   // Test connection periodically
   if(TimeCurrent() % 300 == 0) // Every 5 minutes
   {
      TestConnection();
   }
}

//+------------------------------------------------------------------+
//| Test connection to Python API                                   |
//+------------------------------------------------------------------+
void TestConnection()
{
    string url = API_ENDPOINT + "/api/v1/bridge/heartbeat";
    string postData = CreateHeartbeatData();

    int result = MakeWebRequest("POST", url, headers, postData, 5000);

    if(result == 200)
    {
        if(!isConnected)
        {
            isConnected = true;
            retryCount = 0;
            Print("Connection established with Python API");
        }
    }
    else
    {
        if(isConnected)
        {
            isConnected = false;
            Print("Connection lost with Python API. Result code: ", result);

            if(ENABLE_AUTO_RECONNECT)
            {
                HandleReconnection();
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Send heartbeat to Python API                                    |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
    if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/heartbeat";
    string postData = CreateHeartbeatData();

    int result = MakeWebRequest("POST", url, headers, postData, 5000);

    if(result != 200)
    {
        Print("Heartbeat send failed with code: ", result);
        isConnected = false;
    }
}

//+------------------------------------------------------------------+
//| Send tick data to Python API                                    |
//+------------------------------------------------------------------+
void SendTickData()
{
    if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/tick_data";
    string postData = CreateTickData();

    int result = MakeWebRequest("POST", url, headers, postData, 5000);

    if(result != 200)
    {
        Print("Tick data send failed with code: ", result);
    }
}

//+------------------------------------------------------------------+
//| Send position snapshot to API                                   |
//+------------------------------------------------------------------+
void SendPositionSnapshot()
{
   if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/position_snapshot";
   string postData = CreatePositionSnapshotData();

   int result = MakeWebRequest("POST", url, headers, postData, 5000);

   if(result != 200)
   {
      Print("Position snapshot send failed with code: ", result);
   }
}

//+------------------------------------------------------------------+
//| Check for incoming orders from Python (FIXED)                   |
//+------------------------------------------------------------------+
void CheckForIncomingOrders()
{
    if(!isConnected) return;

    // First authenticate with POST request
    string authUrl = API_ENDPOINT + "/api/v1/bridge/pending_orders";
    string authData = CreateHeartbeatData(); // Use heartbeat as authentication

    int authResult = MakeWebRequest("POST", authUrl, headers, authData, 5000);

    if(authResult == 200)
    {
        // Now get orders with GET request (fallback)
        string getUrl = API_ENDPOINT + "/api/v1/bridge/pending_orders";
        char empty[];  // Empty array for GET request
        char result_data[];
        string response_headers;

        int getResult = WebRequest("GET", getUrl, headers, 5000, empty, result_data, response_headers);

        if(getResult == 200)
        {
            string response = CharArrayToString(result_data);
            if(response != "" && StringFind(response, "orders") >= 0)
            {
                ProcessIncomingOrders(response);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Process incoming orders from Python                              |
//+------------------------------------------------------------------+
void ProcessIncomingOrders(string response)
{
   // This is a simplified parser - in production use a proper JSON library

   if(StringFind(response, "\"type\":\"order\"") >= 0)
   {
      Print("Processing incoming order from Python");

      // Extract order details (simplified parsing)
      string symbol = ExtractValue(response, "symbol");
      string action = ExtractValue(response, "action");
      string orderType = ExtractValue(response, "order_type");
      string volStr = ExtractValue(response, "volume");
      string priceStr = ExtractValue(response, "price");
      string slStr = ExtractValue(response, "stop_loss");
      string tpStr = ExtractValue(response, "take_profit");

      // Convert strings to appropriate types
      double volume = StringToDouble(volStr);
      double price = StringToDouble(priceStr);
      double sl = StringToDouble(slStr);
      double tp = StringToDouble(tpStr);

      // Execute the order
      ExecuteOrder(symbol, action, orderType, volume, price, sl, tp);
   }
   else if(StringFind(response, "\"type\":\"signal\"") >= 0)
   {
      Print("Processing trading signal from Python");

      // Extract signal details
      string symbol = ExtractValue(response, "symbol");
      string bias = ExtractValue(response, "bias");

      // Process signal (could trigger order execution)
      ProcessTradingSignal(symbol, bias);
   }
}

//+------------------------------------------------------------------+
//| Execute order received from Python                               |
//+------------------------------------------------------------------+
void ExecuteOrder(string symbol, string action, string orderType,
                 double volume, double price, double sl, double tp)
{
   if(!ENABLE_ORDER_EXECUTION) return;

   Print("Executing order: ", symbol, " ", action, " ", orderType, " ", volume);

   // Set symbol info
   if(!symbolInfo.Name(symbol))
   {
      Print("Symbol not found: ", symbol);
      return;
   }

   // Determine order type
   ENUM_ORDER_TYPE mt5OrderType;
   if(orderType == "BUY")
      mt5OrderType = ORDER_TYPE_BUY;
   else if(orderType == "SELL")
      mt5OrderType = ORDER_TYPE_SELL;
   else if(orderType == "BUYLIMIT")
      mt5OrderType = ORDER_TYPE_BUY_LIMIT;
   else if(orderType == "SELLLIMIT")
      mt5OrderType = ORDER_TYPE_SELL_LIMIT;
   else if(orderType == "BUYSTOP")
      mt5OrderType = ORDER_TYPE_BUY_STOP;
   else if(orderType == "SELLSTOP")
      mt5OrderType = ORDER_TYPE_SELL_STOP;
   else
   {
      Print("Unsupported order type: ", orderType);
      return;
   }

   // Execute the order
   bool success = false;

   if(mt5OrderType == ORDER_TYPE_BUY || mt5OrderType == ORDER_TYPE_SELL)
   {
      // Market order
      if(mt5OrderType == ORDER_TYPE_BUY)
         success = trade.Buy(volume, symbol, 0, sl, tp, "AI_ORDER");
      else
         success = trade.Sell(volume, symbol, 0, sl, tp, "AI_ORDER");
   }
   else
   {
      // Pending order
      success = trade.OrderOpen(symbol, mt5OrderType, volume, price, sl, tp, ORDER_TIME_GTC, 0, "AI_ORDER");
   }

   if(success)
   {
      Print("Order executed successfully: ", trade.ResultOrder());
      SendOrderConfirmation(symbol, action, orderType, volume, "EXECUTED");
   }
   else
   {
      Print("Order execution failed: ", trade.ResultRetcodeDescription());
      SendOrderConfirmation(symbol, action, orderType, volume, "FAILED");
   }
}

//+------------------------------------------------------------------+
//| Process trading signal from Python                               |
//+------------------------------------------------------------------+
void ProcessTradingSignal(string symbol, string bias)
{
   Print("Processing signal: ", symbol, " ", bias);

   // This could trigger automated order execution based on signal
   // For now, just log the signal

   // Send signal acknowledgment
   SendSignalAcknowledgment(symbol, bias);
}

//+------------------------------------------------------------------+
//| Manage trailing stops for open positions                         |
//+------------------------------------------------------------------+
void ManageTrailingStops()
{
   if(!ENABLE_TRAILING_MANAGEMENT) return;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(positionInfo.SelectByIndex(i))
      {
         // Check if position has trailing stop enabled
         if(positionInfo.Comment() != "" && StringFind(positionInfo.Comment(), "TRAILING") >= 0)
         {
            UpdateTrailingStop(positionInfo.Ticket(), positionInfo.Symbol(),
                             positionInfo.PositionType(), positionInfo.PriceOpen(),
                             positionInfo.StopLoss(), positionInfo.TakeProfit());
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Update trailing stop for a position                              |
//+------------------------------------------------------------------+
void UpdateTrailingStop(ulong ticket, string symbol, ENUM_POSITION_TYPE type,
                       double openPrice, double currentSL, double currentTP)
{
   double currentPrice = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(symbol, SYMBOL_BID) : SymbolInfoDouble(symbol, SYMBOL_ASK);

   // Calculate new stop loss based on trailing rules
   double newSL = currentSL;
   bool shouldUpdate = false;

   if(type == POSITION_TYPE_BUY)
   {
      // For long positions, trail up
      double trailPrice = currentPrice - 200 * Point(); // 200 points trailing distance

      if(trailPrice > currentSL + 50 * Point()) // Only move if significantly higher
      {
         newSL = trailPrice;
         shouldUpdate = true;
      }
   }
   else
   {
      // For short positions, trail down
      double trailPrice = currentPrice + 200 * Point(); // 200 points trailing distance

      if(trailPrice < currentSL - 50 * Point()) // Only move if significantly lower
      {
         newSL = trailPrice;
         shouldUpdate = true;
      }
   }

   // Update stop loss if needed
   if(shouldUpdate)
   {
      if(trade.PositionModify(ticket, newSL, currentTP))
      {
         Print("Trailing stop updated for position ", ticket, " to ", newSL);
      }
      else
      {
         Print("Failed to update trailing stop for position ", ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Send order confirmation to Python                                |
//+------------------------------------------------------------------+
void SendOrderConfirmation(string symbol, string action, string orderType,
                          double volume, string status)
{
   if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/order_confirmation";
   string postData = CreateOrderConfirmationData(symbol, action, orderType, volume, status);

   int result = MakeWebRequest("POST", url, headers, postData, 5000);

   if(result != 200)
   {
      Print("Order confirmation send failed with code: ", result);
   }
}

//+------------------------------------------------------------------+
//| Send signal acknowledgment to Python                             |
//+------------------------------------------------------------------+
void SendSignalAcknowledgment(string symbol, string bias)
{
   if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/signal_ack";
   string postData = CreateSignalAckData(symbol, bias);

   int result = MakeWebRequest("POST", url, headers, postData, 5000);

   if(result != 200)
   {
      Print("Signal acknowledgment send failed with code: ", result);
   }
}

//+------------------------------------------------------------------+
//| Create order confirmation data JSON                              |
//+------------------------------------------------------------------+
string CreateOrderConfirmationData(string symbol, string action, string orderType,
                                  double volume, string status)
{
   string json = "{";
   json += "\"type\":\"order_confirmation\",";
   json += "\"symbol\":\"" + symbol + "\",";
   json += "\"action\":\"" + action + "\",";
   json += "\"order_type\":\"" + orderType + "\",";
   json += "\"volume\":" + DoubleToString(volume, 2) + ",";
   json += "\"status\":\"" + status + "\",";
   json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Create signal acknowledgment data JSON                           |
//+------------------------------------------------------------------+
string CreateSignalAckData(string symbol, string bias)
{
   string json = "{";
   json += "\"type\":\"signal_ack\",";
   json += "\"symbol\":\"" + symbol + "\",";
   json += "\"bias\":\"" + bias + "\",";
   json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Extract JSON value (IMPROVED)                                   |
//+------------------------------------------------------------------+
string ExtractValue(string json, string key)
{
    string searchStr = "\"" + key + "\":\"";
    int start = StringFind(json, searchStr);
    if(start >= 0)
    {
        start += StringLen(searchStr);
        int end = StringFind(json, "\"", start);
        if(end > start)
        {
            return StringSubstr(json, start, end - start);
        }
    }

    // Try numeric value format
    searchStr = "\"" + key + "\":";
    start = StringFind(json, searchStr);
    if(start >= 0)
    {
        start += StringLen(searchStr);
        int end = start;

        // Find end of numeric value
        while(end < StringLen(json))
        {
            string charStr = StringSubstr(json, end, 1);
            if(charStr == "," || charStr == "}" || charStr == " " || charStr == "\n" || charStr == "\r")
                break;
            end++;
        }

        if(end > start)
        {
            return StringSubstr(json, start, end - start);
        }
    }

    return "";
}

//+------------------------------------------------------------------+
//| Create heartbeat data JSON                                       |
//+------------------------------------------------------------------+
string CreateHeartbeatData()
{
   string json = "{";
   json += "\"terminal_id\":\"" + terminalId + "\",";
   json += "\"platform\":\"MT5\",";
   json += "\"account\":\"" + accountNumber + "\",";
   json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Create tick data JSON                                            |
//+------------------------------------------------------------------+
string CreateTickData()
{
   string json = "{";
   json += "\"symbol\":\"" + Symbol() + "\",";
   json += "\"bid\":" + DoubleToString(SymbolInfoDouble(Symbol(), SYMBOL_BID), Digits()) + ",";
   json += "\"ask\":" + DoubleToString(SymbolInfoDouble(Symbol(), SYMBOL_ASK), Digits()) + ",";
   json += "\"time\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Create position snapshot data JSON                               |
//+------------------------------------------------------------------+
string CreatePositionSnapshotData()
{
   string json = "{";
   json += "\"positions\":[";

   bool firstPosition = true;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(positionInfo.SelectByIndex(i))
      {
         if(!firstPosition) json += ",";

         json += "{";
         json += "\"ticket\":\"" + IntegerToString(positionInfo.Ticket()) + "\",";
         json += "\"symbol\":\"" + positionInfo.Symbol() + "\",";
         json += "\"type\":\"" + (positionInfo.PositionType() == POSITION_TYPE_BUY ? "BUY" : "SELL") + "\",";
         json += "\"volume\":" + DoubleToString(positionInfo.Volume(), 2) + ",";
         json += "\"price_open\":" + DoubleToString(positionInfo.PriceOpen(), Digits()) + ",";
         json += "\"sl\":" + (positionInfo.StopLoss() > 0 ? DoubleToString(positionInfo.StopLoss(), Digits()) : "null") + ",";
         json += "\"tp\":" + (positionInfo.TakeProfit() > 0 ? DoubleToString(positionInfo.TakeProfit(), Digits()) : "null") + ",";
         json += "\"profit\":" + DoubleToString(positionInfo.Profit(), 2) + ",";
         json += "\"swap\":" + DoubleToString(positionInfo.Swap(), 2) + ",";
         json += "\"commission\":" + DoubleToString(positionInfo.Commission(), 2) + ",";
         long openTimeRaw = positionInfo.Time();
         datetime openTime = (datetime)openTimeRaw;
         json += "\"time_open\":\"" + TimeToString(openTime, TIME_DATE|TIME_SECONDS) + "\"";
         json += "}";

         firstPosition = false;
      }
   }

   json += "],";
   json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Handle reconnection logic                                        |
//+------------------------------------------------------------------+
void HandleReconnection()
{
   if(retryCount < MAX_RETRY_ATTEMPTS)
   {
      retryCount++;
      Print("Attempting reconnection ", retryCount, "/", MAX_RETRY_ATTEMPTS);

      // Wait before retrying
      Sleep(RETRY_DELAY_MS * retryCount);

      TestConnection();
   }
   else
   {
      Print("Maximum reconnection attempts reached");
   }
}

//+------------------------------------------------------------------+
//| Take screenshot and send to API for AI analysis                 |
//+------------------------------------------------------------------+
void TakeAndSendScreenshot()
{
   // Create filename with timestamp
   string timestamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES);
   StringReplace(timestamp, ".", "_");
   StringReplace(timestamp, ":", "_");
   StringReplace(timestamp, " ", "_");

   string filename = "chart_" + Symbol() + "_" + timestamp + ".gif";
   string fullPath = screenshotPath + filename;

   // Take screenshot
   if(ChartScreenShot(0, fullPath, 1920, 1080, ALIGN_RIGHT))
   {
      Print("Screenshot taken: " + filename);

      // Send screenshot to API
      SendScreenshotToAPI(fullPath, filename);
   }
   else
   {
      Print("Failed to take screenshot");
   }
}

//+------------------------------------------------------------------+
//| Send screenshot to API for AI analysis                          |
//+------------------------------------------------------------------+
void SendScreenshotToAPI(string filePath, string filename)
{
   if(!isConnected) return;

    string url = API_ENDPOINT + "/api/v1/bridge/screenshot_analysis";

   // Read file and convert to base64
   string base64Data = "";
   if(ReadFileAsBase64(filePath, base64Data))
   {
      string postData = CreateScreenshotAnalysisData(base64Data, filename);

      int result = MakeWebRequest("POST", url, headers, postData, 10000);

      if(result == 200)
      {
         Print("Screenshot sent successfully for AI analysis");
      }
      else
      {
         Print("Screenshot send failed with code: ", result);
      }
   }
   else
   {
      Print("Failed to read screenshot file");
   }
}

//+------------------------------------------------------------------+
//| Create screenshot analysis data JSON                             |
//+------------------------------------------------------------------+
string CreateScreenshotAnalysisData(string base64Image, string filename)
{
   string json = "{";
   json += "\"symbol\":\"" + Symbol() + "\",";
   json += "\"timeframe\":\"" + EnumToString(Period()) + "\",";
   json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",";
   json += "\"image_data\":\"" + base64Image + "\",";
   json += "\"filename\":\"" + filename + "\",";
   json += "\"market_context\":{";
   json += "\"current_price\":" + DoubleToString(SymbolInfoDouble(Symbol(), SYMBOL_BID), (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS)) + ",";
   json += "\"spread\":" + DoubleToString(SymbolInfoInteger(Symbol(), SYMBOL_SPREAD), 0) + ",";
   json += "\"volume\":" + DoubleToString(SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_REAL), 2) + ",";
   json += "\"session\":\"" + GetCurrentSession() + "\",";
   json += "\"account_balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
   json += "\"account_equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + "";
   json += "}";
   json += "}";

   return json;
}

//+------------------------------------------------------------------+
//| Read file and convert to Base64                                 |
//+------------------------------------------------------------------+
bool ReadFileAsBase64(string filePath, string &base64Data)
{
   // Extract just the filename from the full path
   string filename = "";
   int lastSlash = StringFind(filePath, "\\", StringLen(filePath) - 1);
   if(lastSlash >= 0)
   {
      filename = StringSubstr(filePath, lastSlash + 1);
   }
   else
   {
      filename = filePath;
   }

   int fileHandle = FileOpen(filename, FILE_READ|FILE_BIN);
   if(fileHandle == INVALID_HANDLE)
   {
      Print("Failed to open file: " + filename + ", Error: " + IntegerToString(GetLastError()));
      return false;
   }

   // Get file size
   ulong fileSizeLong = FileSize(fileHandle);
   if(fileSizeLong > 2147483647) // Max int value
   {
      Print("File too large to process");
      return false;
   }
   int fileSize = (int)fileSizeLong;
   if(fileSize <= 0)
   {
      FileClose(fileHandle);
      Print("File is empty or invalid size: " + filename);
      return false;
   }

   // Read file data
   uchar fileData[];
   ArrayResize(fileData, fileSize);

   uint bytesRead = FileReadArray(fileHandle, fileData, 0, fileSize);
   if(bytesRead > INT_MAX)
   {
      Print("File too large to process");
      return false;
   }
   FileClose(fileHandle);

   if(bytesRead != fileSize)
   {
      Print("Failed to read complete file. Expected: " + IntegerToString(fileSize) + ", Read: " + IntegerToString(bytesRead));
      return false;
   }

   // Convert to base64 (simplified - in real implementation you'd use proper base64 encoding)
   base64Data = "";
   for(int i = 0; i < fileSize; i++)
   {
      base64Data += IntegerToString(fileData[i], 16);
   }

   Print("File read successfully. Size: " + IntegerToString(fileSize) + " bytes");
   return true;
}

//+------------------------------------------------------------------+
//| Get current trading session                                     |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   datetime currentTime = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(currentTime, dt);

   int hour = dt.hour;

   // Determine session based on hour (GMT)
   if(hour >= 0 && hour < 8)
      return "Asian";
   else if(hour >= 8 && hour < 16)
      return "London";
   else if(hour >= 16 && hour < 24)
      return "NewYork";
   else
      return "Overlap";
}

//+------------------------------------------------------------------+
//| Helper function to make web requests                             |
//+------------------------------------------------------------------+
int MakeWebRequest(string method, string url, string request_headers, string postData, int timeout)
{
   char post[];
   StringToCharArray(postData, post);
   char result[];
   string response_headers;
   return WebRequest(method, url, request_headers, timeout, post, result, response_headers);
}

//+------------------------------------------------------------------+
//| Get connection status                                            |
//+------------------------------------------------------------------+
bool IsConnected()
{
   return isConnected;
}

//+------------------------------------------------------------------+
//| Get bridge error message                                         |
//+------------------------------------------------------------------+
string GetBridgeError()
{
   return lastError;
}
