//+------------------------------------------------------------------+
//|                                                    BridgeEA.mq4 |
//|                                  Copyright 2025, AI Trading Bot |
//|                                             https://example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, AI Trading Bot"
#property link      "https://example.com"
#property version   "1.00"
#property strict

//--- Input Parameters
extern string   BRIDGE_TOKEN = "";                    // Bridge authentication token
extern string   API_ENDPOINT = "http://127.0.0.1:8000"; // API endpoint
extern int      HEARTBEAT_INTERVAL = 5;               // Heartbeat interval (seconds)
extern int      POSITION_SNAPSHOT_INTERVAL = 30;      // Position snapshot interval (seconds)
extern int      SCREENSHOT_INTERVAL = 300;            // Screenshot interval (seconds) - 5 minutes
extern bool     ENABLE_TICK_STREAMING = true;         // Enable tick streaming
extern bool     ENABLE_SCREENSHOT_ANALYSIS = true;    // Enable screenshot analysis
extern bool     ENABLE_AUTO_RECONNECT = true;         // Enable auto-reconnection
extern int      MAX_RETRY_ATTEMPTS = 3;               // Maximum retry attempts
extern int      RETRY_DELAY_MS = 250;                 // Retry delay in milliseconds

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

//--- HTTP Request Objects
string headers = "";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int init()
{
   Print("BridgeEA MT4 Initialized");
   
   // Get terminal and account information
   terminalId = TerminalName();
   accountNumber = AccountNumber();
   
   // Initialize screenshot path
   screenshotPath = TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL4\\Files\\Screenshots\\";
   
   // Set up headers for authentication
   headers = "Authorization: Bearer " + BRIDGE_TOKEN + "\r\n";
   headers += "Content-Type: application/json\r\n";
   
   // Test connection
   TestConnection();
   
   Print("Screenshot path: " + screenshotPath);
   
   return(0);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
int deinit()
{
   Print("BridgeEA MT4 Deinitialized");
   return(0);
}

//+------------------------------------------------------------------+
//| Expert start function                                            |
//+------------------------------------------------------------------+
int start()
{
   // Send heartbeat
   if((TimeCurrent() - lastHeartbeatTime) >= HEARTBEAT_INTERVAL)
   {
      SendHeartbeat();
      lastHeartbeatTime = TimeCurrent();
   }
   
   // Send position snapshot
   if((TimeCurrent() - lastPositionSnapshotTime) >= POSITION_SNAPSHOT_INTERVAL)
   {
      SendPositionSnapshot();
      lastPositionSnapshotTime = TimeCurrent();
   }
   
   // Send tick data if enabled and enough time has passed
   if(ENABLE_TICK_STREAMING && (TimeCurrent() - lastTickTime) >= 1)
   {
      SendTickData();
      lastTickTime = TimeCurrent();
   }
   
   // Take and send screenshot for AI analysis
   if(ENABLE_SCREENSHOT_ANALYSIS && (TimeCurrent() - lastScreenshotTime) >= SCREENSHOT_INTERVAL)
   {
      TakeAndSendScreenshot();
      lastScreenshotTime = TimeCurrent();
   }
   
   return(0);
}

//+------------------------------------------------------------------+
//| Test API connection                                              |
//+------------------------------------------------------------------+
void TestConnection()
{
   string url = API_ENDPOINT + "/bridge/heartbeat";
   string postData = CreateHeartbeatData();
   
   int result = WebRequest("POST", url, headers, postData, 5000);
   
   if(result == 200)
   {
      isConnected = true;
      retryCount = 0;
      Print("Successfully connected to API");
   }
   else
   {
      isConnected = false;
      lastError = "Connection failed with code: " + IntegerToString(result);
      Print("Connection failed: ", lastError);
   }
}

//+------------------------------------------------------------------+
//| Send heartbeat to API                                           |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
   if(!isConnected && ENABLE_AUTO_RECONNECT)
   {
      TestConnection();
      return;
   }
   
   string url = API_ENDPOINT + "/bridge/heartbeat";
   string postData = CreateHeartbeatData();
   
   int result = WebRequest("POST", url, headers, postData, 5000);
   
   if(result == 200)
   {
      isConnected = true;
      retryCount = 0;
   }
   else
   {
      isConnected = false;
      lastError = "Heartbeat failed with code: " + IntegerToString(result);
      Print("Heartbeat failed: ", lastError);
      
      if(ENABLE_AUTO_RECONNECT)
      {
         HandleReconnection();
      }
   }
}

//+------------------------------------------------------------------+
//| Send tick data to API                                           |
//+------------------------------------------------------------------+
void SendTickData()
{
   if(!isConnected) return;
   
   string url = API_ENDPOINT + "/bridge/tick";
   string postData = CreateTickData();
   
   int result = WebRequest("POST", url, headers, postData, 5000);
   
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
   
   string url = API_ENDPOINT + "/bridge/position_snapshot";
   string postData = CreatePositionSnapshotData();
   
   int result = WebRequest("POST", url, headers, postData, 5000);
   
   if(result != 200)
   {
      Print("Position snapshot send failed with code: ", result);
   }
}

//+------------------------------------------------------------------+
//| Create heartbeat data JSON                                       |
//+------------------------------------------------------------------+
string CreateHeartbeatData()
{
   string json = "{";
   json += "\"terminal_id\":\"" + terminalId + "\",";
   json += "\"platform\":\"MT4\",";
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
   json += "\"bid\":" + DoubleToString(Bid, Digits) + ",";
   json += "\"ask\":" + DoubleToString(Ask, Digits) + ",";
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
   
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderType() <= OP_SELL) // Only open positions
         {
            if(!firstPosition) json += ",";
            
            json += "{";
            json += "\"ticket\":\"" + IntegerToString(OrderTicket()) + "\",";
            json += "\"symbol\":\"" + OrderSymbol() + "\",";
            json += "\"type\":\"" + (OrderType() == OP_BUY ? "BUY" : "SELL") + "\",";
            json += "\"volume\":" + DoubleToString(OrderLots(), 2) + ",";
            json += "\"price_open\":" + DoubleToString(OrderOpenPrice(), Digits) + ",";
            json += "\"sl\":" + (OrderStopLoss() > 0 ? DoubleToString(OrderStopLoss(), Digits) : "null") + ",";
            json += "\"tp\":" + (OrderTakeProfit() > 0 ? DoubleToString(OrderTakeProfit(), Digits) : "null") + ",";
            json += "\"profit\":" + DoubleToString(OrderProfit(), 2) + ",";
            json += "\"swap\":" + DoubleToString(OrderSwap(), 2) + ",";
            json += "\"commission\":" + DoubleToString(OrderCommission(), 2) + ",";
            json += "\"time_open\":\"" + TimeToString(OrderOpenTime(), TIME_DATE|TIME_SECONDS) + "\"";
            json += "}";
            
            firstPosition = false;
         }
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
   string timestamp = TimeToStr(TimeCurrent(), TIME_DATE|TIME_MINUTES);
   StringReplace(timestamp, ".", "_");
   StringReplace(timestamp, ":", "_");
   StringReplace(timestamp, " ", "_");
   
   string filename = "chart_" + Symbol() + "_" + timestamp + ".gif";
   string fullPath = screenshotPath + filename;
   
   // Take screenshot
   if(WindowScreenShot(filename, 1920, 1080))
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
   // Read screenshot file as base64
   string base64Data = "";
   if(ReadFileAsBase64(filePath, base64Data))
   {
      // Create JSON payload for screenshot analysis
      string jsonData = CreateScreenshotAnalysisData(base64Data, filename);
      
      // Send to API
      string url = API_ENDPOINT + "/api/v1/market-analysis/screenshot";
      
      int result = WebRequest("POST", url, headers, 10000, jsonData, NULL, NULL);
      
      if(result == 200)
      {
         Print("Screenshot analysis sent successfully");
         // Note: MT4 doesn't support response handling as easily as MT5
         // The Python API will process the screenshot and generate signals
      }
      else
      {
         Print("Failed to send screenshot analysis. HTTP code: " + result);
         if(result == -1)
         {
            Print("Error: " + GetLastError());
         }
      }
   }
   else
   {
      Print("Failed to read screenshot file: " + filePath);
   }
   
   // Clean up - delete screenshot file after sending
   FileDelete(filename);
}

//+------------------------------------------------------------------+
//| Create JSON data for screenshot analysis                        |
//+------------------------------------------------------------------+
string CreateScreenshotAnalysisData(string base64Image, string filename)
{
   string json = "{";
   json += "\"symbol\":\"" + Symbol() + "\",";
   json += "\"timeframe\":\"" + Period() + "\",";
   json += "\"timestamp\":\"" + TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",";
   json += "\"image_data\":\"" + base64Image + "\",";
   json += "\"filename\":\"" + filename + "\",";
   json += "\"market_context\":{";
   json += "\"current_price\":" + DoubleToStr(Bid, Digits) + ",";
   json += "\"spread\":" + DoubleToStr(Ask - Bid, Digits) + ",";
   json += "\"session\":\"" + GetCurrentSession() + "\",";
   json += "\"account_balance\":" + DoubleToStr(AccountBalance(), 2) + ",";
   json += "\"account_equity\":" + DoubleToStr(AccountEquity(), 2) + "";
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
   if(fileHandle < 0)
   {
      Print("Failed to open file: " + filename + ", Error: " + GetLastError());
      return false;
   }
   
   // Get file size
   int fileSize = FileSize(fileHandle);
   if(fileSize <= 0)
   {
      FileClose(fileHandle);
      Print("File is empty or invalid size: " + filename);
      return false;
   }
   
   // Read file data (simplified base64 encoding for MT4)
   base64Data = "";
   for(int i = 0; i < fileSize && i < 1000000; i++) // Limit to 1MB
   {
      int byteValue = FileReadInteger(fileHandle, 1);
      base64Data += IntegerToHexString(byteValue);
   }
   
   FileClose(fileHandle);
   Print("File read successfully. Size: " + fileSize + " bytes");
   return true;
}

//+------------------------------------------------------------------+
//| Get current trading session                                     |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   int hour = TimeHour(TimeCurrent());
   
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
//| Get connection status                                            |
//+------------------------------------------------------------------+
bool IsConnected()
{
   return isConnected;
}

//+------------------------------------------------------------------+
//| Get last error message                                           |
//+------------------------------------------------------------------+
string GetLastError()
{
   return lastError;
}