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
extern bool     ENABLE_TICK_STREAMING = true;         // Enable tick streaming
extern bool     ENABLE_AUTO_RECONNECT = true;         // Enable auto-reconnection
extern int      MAX_RETRY_ATTEMPTS = 3;               // Maximum retry attempts
extern int      RETRY_DELAY_MS = 250;                 // Retry delay in milliseconds

//--- Global Variables
datetime lastHeartbeatTime = 0;
datetime lastPositionSnapshotTime = 0;
datetime lastTickTime = 0;
bool isConnected = false;
int retryCount = 0;
string lastError = "";
string terminalId = "";
string accountNumber = "";

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
   
   // Set up headers for authentication
   headers = "Authorization: Bearer " + BRIDGE_TOKEN + "\r\n";
   headers += "Content-Type: application/json\r\n";
   
   // Test connection
   TestConnection();
   
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