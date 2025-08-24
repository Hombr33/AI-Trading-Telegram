"""Trading notifications for Telegram bot."""

import os
import json
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from src.core.logging import get_logger
from .manager import NotificationManager
from ..utils.constants import NotificationPriority

logger = get_logger(__name__)


def save_signal_to_file(signal_data: Dict[str, Any], message: str):
    """Save trading signal to a text file.
    
    Args:
        signal_data: The original signal data.
        message: The formatted message that would be sent to Telegram.
    """
    try:
        # Create logs/signals directory if it doesn't exist
        signals_dir = Path("logs/signals")
        os.makedirs(signals_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Safely get values with fallbacks
        if not isinstance(signal_data, dict):
            logger.warning(f"Invalid signal data type: {type(signal_data)}")
            signal_data = {"symbol": "INVALID", "action": "error"}
            
        symbol = signal_data.get("symbol", "UNKNOWN")
        action = signal_data.get("action", "unknown")
        action = action.upper() if isinstance(action, str) else "UNKNOWN"
        
        # Sanitize filename values to prevent invalid filenames
        symbol = ''.join(c for c in symbol if c.isalnum() or c in '-_')
        action = ''.join(c for c in action if c.isalnum() or c in '-_')
        
        filename = f"{signals_dir}/signal_{symbol}_{action}_{timestamp}.txt"
        
        # Extract important diagnostic information
        diagnostic_info = {
            "timestamp": datetime.now().isoformat(),
            "signal_type": signal_data.get("signal_type", "unknown"),
            "extracted_data": {}
        }
        
        # Add validation error info to diagnostics if applicable
        analysis = signal_data.get('analysis', '')
        if isinstance(analysis, str) and ("error" in analysis.lower() or "validation failed" in analysis.lower()):
            try:
                import json
                import ast
                
                # Try to parse the analysis string if it looks like JSON
                parsed_analysis = None
                if analysis.strip().startswith('{') and analysis.strip().endswith('}'):
                    try:
                        parsed_analysis = json.loads(analysis)
                    except json.JSONDecodeError:
                        try:
                            parsed_analysis = ast.literal_eval(analysis)
                        except (SyntaxError, ValueError):
                            pass
                
                if parsed_analysis and isinstance(parsed_analysis, dict):
                    diagnostic_info["validation_error"] = {
                        "status": parsed_analysis.get("status", "unknown"),
                        "reason": parsed_analysis.get("reason", "unknown"),
                        "data_source": parsed_analysis.get("data_source", "unknown")
                    }
                    
                    # Extract just the error message without quotes and brackets
                    if "reason" in parsed_analysis:
                        import re
                        error_match = re.search(r"'(.*?)'", str(parsed_analysis["reason"]))
                        if error_match:
                            diagnostic_info["validation_error"]["clean_reason"] = error_match.group(1)
            except Exception as e:
                diagnostic_info["validation_error_parsing_failed"] = str(e)
        
        # Try to extract parsed data from raw_analysis for diagnostics
        raw_analysis = signal_data.get("raw_analysis", {})
        if isinstance(raw_analysis, str):
            try:
                raw_analysis = json.loads(raw_analysis)
                diagnostic_info["raw_analysis_parsed"] = True
            except:
                diagnostic_info["raw_analysis_parsed"] = False
        
        if isinstance(raw_analysis, dict):
            signal_info = raw_analysis.get("signal", {})
            if signal_info:
                diagnostic_info["extracted_data"]["market_bias"] = signal_info.get("bias")
                setups = signal_info.get("setups", [])
                if setups and len(setups) > 0:
                    setup = setups[0]
                    diagnostic_info["extracted_data"]["entry_zone"] = setup.get("entry_zone")
                    diagnostic_info["extracted_data"]["stop_loss"] = setup.get("sl")
                    diagnostic_info["extracted_data"]["take_profit"] = setup.get("tp")
                    diagnostic_info["extracted_data"]["setup_confidence"] = setup.get("confidence")
                    diagnostic_info["extracted_data"]["setup_type"] = setup.get("type")
        
        # Write both raw data and formatted message to file
        with open(filename, "w", encoding="utf-8") as file:
            file.write("===== FORMATTED MESSAGE =====\n\n")
            # Safely write message content
            if message and isinstance(message, str):
                file.write(message)
            else:
                file.write("Error: No valid message content")
            
            file.write("\n\n===== DIAGNOSTIC INFO =====\n\n")
            try:
                file.write(json.dumps(diagnostic_info, indent=2, default=str))
            except Exception as e:
                file.write(f"Error serializing diagnostic info: {str(e)}")
            
            file.write("\n\n===== RAW SIGNAL DATA =====\n\n")
            try:
                file.write(json.dumps(signal_data, indent=2, default=str))
            except Exception as e:
                file.write(f"Error serializing signal data: {str(e)}\n")
                file.write(f"Raw signal data type: {type(signal_data)}\n")
                file.write(f"Raw signal data: {str(signal_data)}")
        
        logger.info(f"Signal saved to file: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving signal to file: {e}")
        return None


class TradingNotifications:
    """Trading notifications for Telegram bot."""

    def __init__(self, notification_manager: NotificationManager):
        """Initialize trading notifications.
        
        Args:
            notification_manager: The notification manager to use.
        """
        self.notification_manager = notification_manager

    async def send_signal_notification(self, signal_data: Dict[str, Any]):
        """Send trading signal notification.
        
        Args:
            signal_data: The signal data to send.
        """
        try:
            symbol = signal_data.get("symbol", "UNKNOWN")
            direction = signal_data.get("direction", "NEUTRAL")
            strength = signal_data.get("strength", 0)
            entry_price = signal_data.get("entry_price", 0)
            target_price = signal_data.get("target_price", 0)
            stop_loss = signal_data.get("stop_loss", 0)

            # Determine emoji based on direction
            direction_emoji = "📈" if direction.upper() == "BUY" else "📉" if direction.upper() == "SELL" else "📊"
            
            message = (
                f"🚨 **NEW TRADING SIGNAL** 🚨\n\n"
                f"{direction_emoji} **Symbol**: {symbol}\n"
                f"🎯 **Direction**: {direction}\n"
                f"💯 **Strength**: {strength * 100:.1f}%\n"
                f"📊 **Entry**: ${entry_price:.5f}\n"
                f"🎯 **Target**: ${target_price:.5f}\n"
                f"⚠️ **Stop Loss**: ${stop_loss:.5f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Use /positions to check current positions\n"
                f"Use /risk to monitor risk levels"
            )

            # Save signal to file
            saved_file = save_signal_to_file(signal_data, message)
            if saved_file:
                logger.info(f"Signal saved to file: {saved_file}")

            await self.notification_manager.send_notification(
                message, 
                notification_type="signal", 
                priority=NotificationPriority.HIGH, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")

    async def send_position_notification(self, position_data: Dict[str, Any], action: str):
        """Send position update notification.
        
        Args:
            position_data: The position data to send.
            action: The action that occurred (opened, closed, modified).
        """
        try:
            symbol = position_data.get("symbol", "UNKNOWN")
            direction = position_data.get("type", "UNKNOWN")
            volume = position_data.get("volume", 0)
            price = position_data.get("price_open", 0)
            pnl = position_data.get("profit", 0)

            if action == "opened":
                emoji = "✅"
                action_text = "OPENED"
            elif action == "closed":
                emoji = "🔒"
                action_text = "CLOSED"
            elif action == "modified":
                emoji = "🔄"
                action_text = "MODIFIED"
            else:
                emoji = "📊"
                action_text = action.upper()

            # Determine emoji based on direction
            direction_emoji = "📈" if direction.upper() == "BUY" else "📉" if direction.upper() == "SELL" else "📊"
            
            # Determine emoji based on profit
            profit_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"

            message = (
                f"{emoji} **POSITION {action_text}** {emoji}\n\n"
                f"{direction_emoji} **Symbol**: {symbol}\n"
                f"📈 **Direction**: {direction}\n"
                f"📊 **Volume**: {volume}\n"
                f"💰 **Price**: ${price:.5f}\n"
                f"{profit_emoji} **P&L**: ${abs(pnl):.2f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            await self.notification_manager.send_notification(
                message, 
                notification_type="position", 
                priority=NotificationPriority.MEDIUM, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending position notification: {e}")

    async def send_order_notification(self, order_data: Dict[str, Any], action: str):
        """Send order update notification.
        
        Args:
            order_data: The order data to send.
            action: The action that occurred (placed, cancelled, filled).
        """
        try:
            symbol = order_data.get("symbol", "UNKNOWN")
            order_type = order_data.get("type", "UNKNOWN")
            volume = order_data.get("volume", 0)
            price = order_data.get("price", 0)

            if action == "placed":
                emoji = "📝"
                action_text = "PLACED"
            elif action == "cancelled":
                emoji = "❌"
                action_text = "CANCELLED"
            elif action == "filled":
                emoji = "✅"
                action_text = "FILLED"
            else:
                emoji = "📊"
                action_text = action.upper()

            message = (
                f"{emoji} **ORDER {action_text}** {emoji}\n\n"
                f"📊 **Symbol**: {symbol}\n"
                f"📈 **Type**: {order_type}\n"
                f"📊 **Volume**: {volume}\n"
                f"💰 **Price**: ${price:.5f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            await self.notification_manager.send_notification(
                message, 
                notification_type="order", 
                priority=NotificationPriority.MEDIUM, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending order notification: {e}")


# Global notification functions for backward compatibility
async def send_signal_notification(signal_data: Dict[str, Any]):
    """Send trading signal notification (global function).
    
    Args:
        signal_data: The signal data to send.
    """
    try:
        # Format the signal for Telegram
        symbol = signal_data.get("symbol", "UNKNOWN")
        action = signal_data.get("action", "HOLD").upper()
        entry_price = signal_data.get("entry_price", 0)
        stop_loss = signal_data.get("stop_loss", 0)
        take_profit = signal_data.get("take_profit", 0)
        confidence = signal_data.get("confidence", 0)
        risk_level = signal_data.get("risk_level", "unknown").upper()
        platform = signal_data.get("platform", "unknown")
        timestamp = signal_data.get("timestamp", datetime.now().isoformat())
        
        # Extract current price and potential setups from raw_analysis if available
        current_price = None
        potential_entry = None
        potential_sl = None
        potential_tp = None
        market_bias = None
        
        # Try to extract actual market data even for HOLD signals
        raw_analysis = signal_data.get("raw_analysis", {})
        if isinstance(raw_analysis, str):
            try:
                import json
                raw_analysis = json.loads(raw_analysis)
            except:
                logger.warning("Could not parse raw_analysis as JSON")
        
        if isinstance(raw_analysis, dict):
            # Try to extract current price from market data
            try:
                market_data = raw_analysis.get("market_data", "")
                if "Current Price: $" in market_data:
                    price_start = market_data.find("Current Price: $") + len("Current Price: $")
                    price_end = market_data.find("\n", price_start)
                    if price_end > price_start:
                        price_str = market_data[price_start:price_end].replace(",", "").strip()
                        current_price = float(price_str)
            except Exception as e:
                logger.warning(f"Failed to extract current price: {e}")
            
            # Try to extract signal setups
            try:
                signal_info = raw_analysis.get("signal", {})
                if signal_info:
                    market_bias = signal_info.get("bias")
                    setups = signal_info.get("setups", [])
                    if setups and len(setups) > 0:
                        setup = setups[0]  # Get first setup
                        entry_zone = setup.get("entry_zone", [])
                        if entry_zone and len(entry_zone) > 0:
                            potential_entry = sum(entry_zone) / len(entry_zone)  # Average of entry zone
                        potential_sl = setup.get("sl")
                        tp_values = setup.get("tp", [])
                        if tp_values and len(tp_values) > 0:
                            potential_tp = tp_values[0]  # First take profit level
            except Exception as e:
                logger.warning(f"Failed to extract setup details: {e}")
        
        # Use extracted data if action is HOLD but we have market data
        if action == "HOLD" and current_price:
            # If we have a current price but no entry/sl/tp, use potential values from raw data
            if entry_price == 0 and potential_entry:
                entry_price = potential_entry
            if stop_loss == 0 and potential_sl:
                stop_loss = potential_sl
            if take_profit == 0 and potential_tp:
                take_profit = potential_tp
            # If we still don't have prices, at least show current price
            if entry_price == 0:
                entry_price = current_price
        
        # Process analysis text to extract meaningful information
        analysis_text = signal_data.get('analysis', 'AI-generated signal')
        cleaned_analysis = 'AI-generated signal'
        
        # Check if analysis contains validation error (in JSON-like format)
        if isinstance(analysis_text, str):
            if "error" in analysis_text and "validation failed" in analysis_text.lower():
                try:
                    # Extract the actual error message from the JSON-like string
                    import json
                    import ast
                    
                    # Try to parse the string as a dict if it's formatted like one
                    try:
                        # First try direct JSON parsing
                        parsed = json.loads(analysis_text)
                    except json.JSONDecodeError:
                        try:
                            # Try Python's literal_eval for safer dict parsing
                            parsed = ast.literal_eval(analysis_text)
                        except (SyntaxError, ValueError):
                            parsed = None
                    
                    if parsed and isinstance(parsed, dict):
                        # Extract meaningful error information
                        if 'reason' in parsed:
                            error_reason = parsed['reason']
                            
                            # Further clean up the reason if it contains nested quotes and brackets
                            if "Setup" in error_reason and ":" in error_reason:
                                # Extract just the actual error message
                                import re
                                error_match = re.search(r"Setup \d+: (.*?)(?:'|$)", error_reason)
                                if error_match:
                                    cleaned_analysis = f"Signal validation error: {error_match.group(1).strip()}"
                                else:
                                    cleaned_analysis = f"Signal validation error: {error_reason}"
                            else:
                                cleaned_analysis = f"Signal validation error: {error_reason}"
                        else:
                            cleaned_analysis = "Signal validation error"
                except Exception as e:
                    logger.warning(f"Failed to parse error reason: {e}")
                    cleaned_analysis = "Signal validation failed"
            else:
                # Normal analysis, just use the text as is
                cleaned_analysis = analysis_text
        
        # Limit length to avoid overly long messages
        analysis_snippet = cleaned_analysis[:100] if cleaned_analysis else 'AI-generated signal'
        # Escape special markdown characters
        analysis_snippet = analysis_snippet.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
        
        # Determine emojis
        action_emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
        risk_emoji = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
        
        # Add market bias if available
        if market_bias and action == "HOLD":
            action = f"HOLD ({market_bias})"
        elif action == "HOLD":
            # Try to determine a reason for the HOLD recommendation
            reason = "UNFAVORABLE MARKET"
            
            # Check if analysis contains error information
            if isinstance(analysis_text, str) and "error" in analysis_text.lower():
                reason = "VALIDATION FAILED"
                
                # Try to extract the specific error reason
                try:
                    import re
                    error_match = re.search(r"Setup \d+: (.*?)(?:'|$|\])", analysis_text)
                    if error_match:
                        specific_error = error_match.group(1).strip()
                        
                        # Format the reason based on the specific error
                        if "risk-reward ratio" in specific_error.lower():
                            # Extract the actual ratio if available
                            ratio_match = re.search(r"ratio (\d+\.\d+)", specific_error)
                            if ratio_match:
                                reason = f"RR RATIO {ratio_match.group(1)} TOO LOW"
                            else:
                                reason = "POOR RISK-REWARD"
                        elif "stop loss" in specific_error.lower():
                            reason = "INVALID STOP LOSS"
                        elif "take profit" in specific_error.lower():
                            reason = "INVALID TAKE PROFIT"
                        elif "minimum" in specific_error.lower():
                            reason = "BELOW MINIMUM CRITERIA"
                        else:
                            # Use a shortened version of the specific error
                            short_reason = specific_error[:20].upper()
                            if len(short_reason) < len(specific_error):
                                short_reason += "..."
                            reason = short_reason
                except Exception:
                    # Fallback to basic checks if regex extraction fails
                    if "risk-reward" in analysis_text.lower():
                        reason = "INVALID RISK-REWARD"
                    elif "stop loss" in analysis_text.lower():
                        reason = "INVALID STOP LOSS"
                    elif "minimum" in analysis_text.lower():
                        reason = "BELOW MINIMUM CRITERIA"
            else:
                # Look for common phrases in the analysis that might indicate why
                analysis_lower = analysis_text.lower() if analysis_text else ""
                if "wait" in analysis_lower or "waiting" in analysis_lower:
                    reason = "WAITING FOR SETUP"
                elif "range" in analysis_lower or "consolidation" in analysis_lower:
                    reason = "MARKET RANGING"
                elif "unclear" in analysis_lower or "uncertain" in analysis_lower:
                    reason = "MARKET UNCERTAINTY"
                elif "volatility" in analysis_lower:
                    reason = "HIGH VOLATILITY"
                
            action = f"HOLD ({reason})"
        
        # Format message for Telegram
        if action.startswith("HOLD"):
            # Special formatting for HOLD signals with market context
            entry_line = f" **Potential Entry**: ${entry_price:.5f}\n" if entry_price > 0 else ""
            stop_line = f"🛡️ **Potential Stop**: ${stop_loss:.5f}\n" if stop_loss > 0 else ""
            target_line = f"🎯 **Potential Target**: ${take_profit:.5f}\n" if take_profit > 0 else ""
            
            # If we have potential levels, add a header
            levels_header = "\n**Market Levels**:\n" if (entry_line or stop_line or target_line) else ""
            
            # For HOLD signals that have validation errors, format differently
            if "error" in cleaned_analysis.lower() or "validation" in cleaned_analysis.lower():
                telegram_message = f"""
🚨 **AI TRADING SIGNAL** 🚨

{action_emoji} **Action**: {action}
📊 **Symbol**: {symbol}
📊 **Current Price**: ${entry_price:.5f}{levels_header}{entry_line}{stop_line}{target_line}
📈 **Confidence**: {confidence}/10
{risk_emoji} **Risk Level**: {risk_level}
🔗 **Platform**: {platform}
⏰ **Time**: {timestamp[:19]}

⚠️ **Reason**: {cleaned_analysis}

Use /positions to check current positions
Use /risk to monitor risk levels
                """.strip()
            else:
                telegram_message = f"""
🚨 **AI TRADING SIGNAL** 🚨

{action_emoji} **Action**: {action}
📊 **Symbol**: {symbol}
📊 **Current Price**: ${entry_price:.5f}{levels_header}{entry_line}{stop_line}{target_line}
📈 **Confidence**: {confidence}/10
{risk_emoji} **Risk Level**: {risk_level}
🔗 **Platform**: {platform}
⏰ **Time**: {timestamp[:19]}

📋 **Analysis**: {analysis_snippet}...

Use /positions to check current positions
Use /risk to monitor risk levels
                """.strip()
        else:
            # Standard formatting for BUY/SELL signals
            telegram_message = f"""
🚨 **AI TRADING SIGNAL** 🚨

{action_emoji} **Action**: {action}
📊 **Symbol**: {symbol}
💰 **Entry**: ${entry_price:.5f}
🛡️ **Stop Loss**: ${stop_loss:.5f}
🎯 **Take Profit**: ${take_profit:.5f}

📈 **Confidence**: {confidence}/10
{risk_emoji} **Risk Level**: {risk_level}
🔗 **Platform**: {platform}
⏰ **Time**: {timestamp[:19]}

📋 **Analysis**: {analysis_snippet}...

Use /positions to check current positions
Use /risk to monitor risk levels
        """.strip()
        
        # Log the formatted signal
        logger.info(f"📡 Telegram Signal Generated:")
        logger.info(f"Symbol: {symbol} | Action: {action} | Entry: ${entry_price:.5f}")
        logger.info(f"Confidence: {confidence}/10 | Risk: {risk_level}")
        
        # Actually send the message to Telegram
        try:
            from ..core.trading_bot import TradingBot
            bot = TradingBot.get_instance()
            if bot and bot.config.chat_id:
                try:
                    # Try with Markdown first
                    await bot.send_message(bot.config.chat_id, telegram_message, parse_mode="Markdown")
                except Exception as markdown_error:
                    logger.warning(f"Markdown parsing failed: {markdown_error}, trying without parse_mode")
                    # If markdown fails, send as plain text
                    plain_message = telegram_message.replace('**', '').replace('`', '')
                    await bot.send_message(bot.config.chat_id, plain_message)
                    
                logger.info(f"✅ Signal sent to Telegram chat {bot.config.chat_id}")
            else:
                logger.warning("❌ Telegram bot not available or chat_id not configured")
        except Exception as e:
            logger.error(f"❌ Error sending signal to Telegram: {e}")
        
        # Save signal to file with error handling
        try:
            saved_file = save_signal_to_file(signal_data, telegram_message)
            if saved_file:
                logger.info(f"Signal saved to file: {saved_file}")
            
            # Store formatted message for Telegram bot to pick up
            signal_data['telegram_message'] = telegram_message
            signal_data['formatted_for_telegram'] = True
        except Exception as file_error:
            logger.error(f"Error saving signal to file: {file_error}")
            # Still try to store the message if possible
            if 'telegram_message' in locals():
                signal_data['telegram_message'] = telegram_message
                signal_data['formatted_for_telegram'] = True
        
        return signal_data
        
    except Exception as e:
        logger.error(f"Error formatting signal notification: {e}")
        logger.info(f"Raw signal data: {signal_data}")


async def send_trade_notification(trade_data: Dict[str, Any]):
    """Send trade notification (global function).
    
    Args:
        trade_data: The trade data to send.
    """
    # For now, just log the trade since we don't have a global notification manager
    logger.info(f"Trade executed: {trade_data}")