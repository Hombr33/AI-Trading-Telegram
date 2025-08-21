//+------------------------------------------------------------------+
//|                                                    BridgeEA.mq5 |
//|                                  Copyright 2025, AI Trading Bot |
//|                                             https://example.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, AI Trading Bot"
#property link      "https://example.com"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//--- Input Parameters
input string   BRIDGE_TOKEN = "";                    // Bridge authentication token
input string   API_ENDPOINT = "http://127.0.0.1:8000"; // API endpoint
input int      HEARTBEAT_INTERVAL = 5;               // Heartbeat interval (seconds)
input int      POSITION_SNAPSHOT_INTERVAL = 30;      // Position snapshot interval (seconds)
input bool     ENABLE_TICK_STREAMING = true;         // Enable tick streaming
input bool     ENABLE_AUTO_RECONNECT = true;         // Enable auto-reconnection
input int      MAX_RETRY_ATTEMPTS = 3;               // Maximum retry attempts
input int      RETRY_DELAY_MS = 250;                 // Retry delay in milliseconds

//--- Global Variables
datetime lastHeartbeatTime = 0;
datetime lastPositionSnapshotTime = 0;
datetime lastTickTime = 0;
bool isConnected = false;
int retryCount = 0;
string lastError = "";
string terminalId = "";
string accountNumber = "";

//--- Trading Objects
CTrade trade;
CPositionInfo positionInfo;
COrderInfo orderInfo;
CSymbolInfo symbolInfo;

//--- HTTP Request Objects
string headers = "";

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
   accountNumber = AccountInfoString(ACCOUNT_LOGIN);
   
   // Set up headers for authentication
   headers = "Authorization: Bearer " + BRIDGE_TOKEN + "\r\n";
   headers += "Content-Type: application/json\r\n";
   
   // Test connection
   TestConnection();
   
   // Set up timer for periodic operations
   EventSetTimer(1); // Check every second
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("BridgeEA MT5 Deinitialized. Reason: ", reason);
   
   // Remove timer
   EventSetTimer(0);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Send tick data if enabled and enough time has passed
   if(ENABLE_TICK_STREAMING && (TimeCurrent() - lastTickTime) >= 1)
   {
      SendTickData();
      lastTickTime = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
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
         json += "\"time_open\":\"" + TimeToString(positionInfo.Time(), TIME_DATE|TIME_SECONDS) + "\"";
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