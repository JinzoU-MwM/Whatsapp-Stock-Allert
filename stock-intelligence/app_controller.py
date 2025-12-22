import os
import requests
import subprocess
import threading
import json
import time
from dotenv import load_dotenv

# Import Logic
from technical_analysis import analyze_technical
from quant_engine import QuantAnalyzer
try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

from catalyst_agent import get_technical_analysis, get_bandarmology_analysis, get_fundamental_analysis, get_final_verdict
from news_fetcher import fetch_stock_news
from chart_generator import generate_chart
from main import format_message, broadcast_message
import db_manager

class StockAppController:
    def __init__(self, log_callback=None):
        """
        :param log_callback: Function to send log messages to (e.g., ui_logger)
        """
        self.log_callback = log_callback
        self.wa_process = None
        self.service_url = "http://localhost:3000"
        
        load_dotenv()
        db_manager.init_db()
        
        # Initialize Quant Components
        self.goapi_client = None
        if os.getenv("GOAPI_API_KEY") and GoApiClient:
            self.goapi_client = GoApiClient()
            
        self.quant_engine = QuantAnalyzer(self.goapi_client)

    def log(self, message):
        # Suppress logging in production unless it's a critical error or analysis step
        if self.log_callback and (message.startswith("✅") or message.startswith("❌") or message.startswith("📊") or message.startswith("🧠") or message.startswith("🌍") or message.startswith("🔵") or message.startswith("🔎") or message.startswith("📈")):
             self.log_callback(message)
        # Always log to console/file if needed for debugging, or comment out for cleaner production
        # else:
        #     try:
        #         print(message)
        #     except:
        #         pass

    def start_wa_service(self):
        """Starts Node.js service. Hides window for cleaner UX but logs to file."""
        try:
            service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp-service")
            log_path = os.path.join(service_path, "service_debug.log")
            
            # Use CREATE_NO_WINDOW to hide the console completely
            creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.log(f"🚀 Memulai Layanan WhatsApp (Log: {log_path})...")
            
            # Open log file
            self.log_file = open(log_path, "w")
            
            # Use node directly instead of npm for better process control
            cmd = "node index.js"
            
            self.wa_process = subprocess.Popen(
                cmd, 
                cwd=service_path,
                shell=True,
                creationflags=creation_flags,
                stdout=self.log_file,
                stderr=self.log_file
            )
        except Exception as e:
            self.log(f"❌ Gagal memulai Layanan WhatsApp: {e}")

    def stop_wa_service(self):
        if self.wa_process:
            try:
                subprocess.run(f"taskkill /F /T /PID {self.wa_process.pid}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                pass
        
        if hasattr(self, 'log_file') and self.log_file:
            try:
                self.log_file.close()
            except:
                pass

    def check_service_health(self):
        try:
            requests.get(f"{self.service_url}/health", timeout=2)
            return True
        except:
            return False

    def get_qr_code(self):
        """Fetches QR code string from the Node.js service."""
        try:
            response = requests.get(f"{self.service_url}/qr", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data
            return None
        except:
            return None

    def logout_whatsapp(self):
        try:
            response = requests.post(f"{self.service_url}/logout", timeout=5)
            if response.status_code == 200:
                self.log("✅ Berhasil Logout WhatsApp.")
                return True
            else:
                self.log(f"⚠️ Gagal Logout: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error during logout: {e}")
            return False

    def fetch_groups(self):
        try:
            response = requests.get(f"{self.service_url}/groups", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            self.log(f"Error fetching groups: {e}")
            return []

    def run_analysis(self, ticker, timeframe="daily", progress_callback=None):
        """
        Orchestrates the unified "Stock Intelligence" pipeline.
        Combines Technical, Forensic Bandarmology, and News into one report.
        """
        ticker = ticker.upper()
        self.log(f"🔵 Memulai Stock Intelligence untuk {ticker} ({timeframe})...")
        if progress_callback: progress_callback(0.1)
        
        # Save to History
        db_manager.add_history(ticker)

        _cached = None
        # 1. Check Cache (Daily only)
        if timeframe == "daily":
            cached_data = db_manager.get_cached_analysis(ticker)
            if cached_data:
                # pass for now, forcing refresh as per logic
                pass 

        try:
            # 1. FETCH DATA (Parallel Technical + Bandarmology + News)
            # Parallel execution logic is kept here or could be valid to extract too, 
            # but for now we keep the data fetching here as it orchestrates the inputs.
            import concurrent.futures
            
            def fetch_full_bandar():
                if self.goapi_client and timeframe == "daily":
                    self.log(f"🔎 Menjalankan Forensik Bandarmology...")
                    if progress_callback: progress_callback(0.4)
                    real = self.quant_engine.fetch_real_bandarmology(ticker)
                    hist = self.goapi_client.get_broker_summary_historical(ticker, days=20)
                    return real, hist
                return None, None

            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.log(f"🚀 Memulai Parallel Data Fetching ({ticker})...")
                future_tech = executor.submit(analyze_technical, ticker, timeframe=timeframe)
                future_bandar = executor.submit(fetch_full_bandar)
                future_news = executor.submit(fetch_stock_news, ticker)
                
                try:
                    ta_data = future_tech.result()
                    real_bandar, hist_raw = future_bandar.result()
                    news_summary = future_news.result()
                except Exception as e:
                    self.log(f"❌ Error in Parallel Fetch: {e}")
                    raise e

            if progress_callback: progress_callback(0.6)

            # 2. PREPARE CONTEXT (Bandarmology Processing)
            context_data = {
                'today_summary': 'N/A', 'top_seller': 'N/A', 'seller_hist_net': 'N/A', 'seller_avg_price': '0',
                'vwap': ta_data.get('vwap', 0), 'price_change': ta_data.get('change_pct', 0),
                'top1_buy_price': 0, 'top1_sell_price': 0, 'status_header': 'N/A' 
            }
            
            broker_history_df = None
            broker_flow_df = None
            bandar_summary_lines = []

            if real_bandar:
                # Process Bandar Data using QuantEngine logic
                bs_data = real_bandar.get('broker_summary', {})
                ff_data = real_bandar.get('foreign_flow', {})
                context_data['today_summary'] = bs_data.get('summary', 'N/A')
                
                ta_data['bandar_status'] = bs_data.get('status', 'Neutral')
                ta_data['foreign_status'] = ff_data.get('status', 'N/A')
                
                # Historical Analysis (Optional)
                if hist_raw:
                    broker_history_df = self.quant_engine.analyze_historical_broker_summary(hist_raw)
                    cum_summary = self.quant_engine.get_cumulative_broker_summary(hist_raw)
                    broker_flow_df = self.quant_engine.prepare_broker_flow_data(hist_raw)
                else:
                    broker_history_df = None
                    cum_summary = {'top_sellers': [], 'top_buyers': []}
                    broker_flow_df = None
                
                # Context Extraction
                
                # Context Extraction
                top_seller_code = cum_summary['top_sellers'][0][0] if cum_summary['top_sellers'] else bs_data.get('top_seller', 'N/A')
                context_data['top_seller'] = top_seller_code
                context_data['top1_buy_price'] = bs_data.get('top1_buy_price', 0)
                context_data['top1_sell_price'] = bs_data.get('top1_sell_price', 0)
                
                if top_seller_code != "N/A":
                    net_vol, avg_price = self.quant_engine.calculate_broker_net_history(hist_raw, top_seller_code)
                    pos_str = "Net Buy" if net_vol > 0 else "Net Sell"
                    context_data['seller_hist_net'] = f"{pos_str} ({net_vol:,.0f} Lot)"
                    context_data['seller_avg_price'] = f"{avg_price:,.0f}"

                context_data['top3_buyers'] = bs_data.get('top_buyers_formatted', bs_data.get('top_buyers_list', 'N/A'))
                context_data['top3_sellers'] = bs_data.get('top_sellers_formatted', bs_data.get('top_sellers_list', 'N/A'))
                
                # Final Verdict Calculation
                tech_score = 50 
                if "Bullish" in ta_data['trend']: tech_score += 20
                if "Golden Cross" in ta_data['macd_status']: tech_score += 10
                
                final_res = self.quant_engine.calculate_final_verdict(
                    tech_score=tech_score,
                    bandar_score=bs_data.get('bandar_score', 0),
                    foreign_score=ff_data.get('foreign_score', 0)
                )
                ta_data['final_score'] = final_res['final_score']
                ta_data['verdict'] = final_res['verdict']
                
                # Valuation & Foreign Context
                val_data = ta_data.get('valuation', {})
                context_data['foreign_flow'] = ff_data.get('status', 'N/A')
                context_data['pbv'] = val_data.get('pbv', 0)
                context_data['per'] = val_data.get('per', 0)
                context_data['market_cap'] = val_data.get('market_cap', 0)
                
                # Summary Lines
                data_date = "Unknown"
                if broker_history_df is not None and not broker_history_df.empty:
                    last_date = broker_history_df.index[-1]
                    data_date = last_date.strftime('%d-%m-%Y')
                
                bandar_summary_lines.append(f"📅 *Data Date*: {data_date}")
                current_top_buyer = bs_data.get('top_buyers_formatted', bs_data.get('top_buyers_list', '-'))
                current_top_seller = bs_data.get('top_sellers_formatted', bs_data.get('top_sellers_list', '-'))
                
                # Fallback check
                if current_top_buyer == '-' and broker_history_df is not None and not broker_history_df.empty:
                     last_day = broker_history_df.iloc[-1]
                     current_top_buyer = last_day.get('Top3Buyers', '-')
                     current_top_seller = last_day.get('Top3Sellers', '-')

                bandar_summary_lines.append(f"Top 3 Buyer (Today): {current_top_buyer}")
                bandar_summary_lines.append(f"Top 3 Seller (Today): {current_top_seller}")

            self.log("🌍 Berita Terambil via Parallel Fetch.")

            # 3. RUN AI PIPELINE (Refactored)
            self.log("🧠 Melakukan Riset AI (Technical + Forensic + Fundamental)...")
            
            # Prepare Fundamental Data Input
            fund_data = {
                "pe_ratio": ta_data.get('valuation', {}).get('per', 0),
                "pbv": ta_data.get('valuation', {}).get('pbv', 0),
                "roe": ta_data.get('valuation', {}).get('roe', 0),
                "der": ta_data.get('valuation', {}).get('der', 0),
                "eps_growth": ta_data.get('valuation', {}).get('eps_growth', 0),
            }
            
            ai_tech, ai_forensic, ai_fund, ai_cio = self._run_ai_pipeline(
                ticker, ta_data, context_data, fund_data, news_summary
            )
            
            if progress_callback: progress_callback(0.8)

            # 4. GENERATE CHART
            self.log("📈 Membuat Chart Technical Standard...")
            chart_path = generate_chart(
                ta_data['ticker'], ta_data['df_daily'], 
                broker_history_df=broker_history_df, broker_flow_df=broker_flow_df,
                chart_mode='technical' 
            )

            # 5. FORMAT REPORT (Refactored)
            # Update final score before formatting logic if needed, typically AI score is used
            ta_data['final_score'] = ai_cio.get('final_score', 50)
            
            msg, tech_analysis_text = self._format_analysis_report(
                ticker, ta_data, ai_tech, ai_forensic, ai_fund, ai_cio, 
                bandar_summary_lines, news_summary
            )

            # Save (Daily)
            if timeframe == "daily":
                db_manager.save_analysis(ta_data['ticker'], ta_data, tech_analysis_text, msg)
            
            self.log("✅ Analisa Selesai.")
            if progress_callback: progress_callback(1.0)
            
            return msg, chart_path, ta_data.get('final_score', 50)
            
        except Exception as e:
            self.log(f"❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def _run_ai_pipeline(self, ticker, ta_data, context_data, fund_data, news_summary):
        """Executes AI agents in parallel."""
        import concurrent.futures
        
        ai_tech = {}
        ai_forensic = {}
        ai_fund = {}
        ai_cio = {}
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as ai_executor:
                future_ai_tech = ai_executor.submit(get_technical_analysis, ticker, ta_data, news_summary)
                future_ai_fund = ai_executor.submit(get_fundamental_analysis, ticker, fund_data)
                
                # Only run forensic if context exists
                future_ai_forensic = None
                if context_data.get('top_seller') != 'N/A' or context_data.get('today_summary') != 'N/A':
                    future_ai_forensic = ai_executor.submit(get_bandarmology_analysis, ticker, context_data)
                
                ai_tech = future_ai_tech.result()
                ai_fund = future_ai_fund.result()
                
                if future_ai_forensic:
                    ai_forensic = future_ai_forensic.result()
                else:
                    ai_forensic = {"status": "N/A", "analysis": "Data Bandar Tidak Cukup"}
                    
                # --- CIO SYNTHESIS ---
                self.log("⚖️ Menjalankan CIO Agent (Synthesis Decision)...")
                ai_cio = get_final_verdict(ticker, ai_tech, ai_forensic, ai_fund)
                
        except Exception as e:
            self.log(f"❌ Error in Parallel AI: {e}")
            ai_tech = {'analysis': f"Error: {e}", 'action': 'ERROR'}
            ai_forensic = {}
            ai_fund = {}
            ai_cio = {'recommended_action': 'ERROR', 'final_reasoning': str(e)}
            
        return ai_tech, ai_forensic, ai_fund, ai_cio

    def _format_analysis_report(self, ticker, ta_data, ai_tech, ai_forensic, ai_fund, ai_cio, bandar_summary_lines, news_summary):
        """Formats the final WhatsApp message with Professional Aesthetics."""
        try:
            # Helper for bullets
            def to_bullet(lines, symbol="•"):
                if isinstance(lines, list):
                    return "\n".join([f"{symbol} {line}" for line in lines])
                return lines

            # Extract Data
            tech_analysis_text = ai_tech.get('analysis', '-')
            trading_plan = ai_tech.get('trading_plan', {})
            
            forensic_status = ai_forensic.get('status', 'NETRAL')
            forensic_analysis = ai_forensic.get('analysis', '-')
            forensic_warning = ai_forensic.get('warning', '')
            
            cio_action = ai_cio.get('recommended_action', 'WAIT')
            cio_reason = ai_cio.get('final_reasoning', '-')
            cio_strategy = ai_cio.get('primary_strategy', '-')
            cio_alloc = ai_cio.get('allocation_size', '-')
            cio_score = ai_cio.get('final_score', 50)
            
            # --- HEADER ---
            msg = f"🚨 *STOCK INTELLIGENCE: {ticker}*\n"
            msg += "━━━━━━━━━━━━━━━━━━\n"  # Separator
            msg += f"🎯 *VERDICT: {cio_action}* (Conf: {cio_score}%)\n"
            msg += f"💡 *STRATEGY: {cio_strategy}*\n"
            msg += f"💰 *ALLOCATION: {cio_alloc}*\n"
            msg += f"📝 *CIO NOTE*: _{cio_reason}_\n"
            msg += f"📉 *Last Price*: {ta_data['price']:.0f}\n\n"
            
            # --- 1. TEKNIKAL ---
            msg += "📊 *1. DATA TEKNIKAL & FLOW*\n"
            msg += f"• Tren: {ta_data['trend']}\n"
            msg += f"• Candle: {ta_data.get('candle_pattern', '-')}\n"
            msg += f"• MACD: {ta_data['macd_status']}\n"
            msg += f"• Volume: {ta_data['vol_status']} ({ta_data['vol_ratio']:.2f}x Avg)\n"
            msg += f"• Foreign: {ta_data.get('foreign_status', '-')}\n"
            msg += f"• Bandar: {ta_data.get('bandar_status', '-')}\n"
            msg += f"• Power: RSI {ta_data['rsi']:.0f} | ADX {ta_data.get('adx',0):.0f}\n\n"
            
            # --- 2. FUNDAMENTAL ---
            val = ta_data.get('valuation', {})
            msg += "💰 *2. FUNDAMENTAL SNAPSHOT*\n"
            msg += f"• Status: *{val.get('valuation_status', '-')}*\n"
            msg += f"• PER: {val.get('per',0):.2f}x  |  PBV: {val.get('pbv',0):.2f}x\n"
            
            mc_val = val.get('market_cap', 0)
            if mc_val > 1_000_000_000_000: mc_str = f"{mc_val/1e12:.2f} T"
            else: mc_str = f"{mc_val/1e9:.0f} M"
            
            msg += f"• ROE: {val.get('roe',0)*100:.2f}% | Cap: {mc_str}\n\n"
            
            # --- 3. CHART ANALYSIS ---
            msg += "📈 *3. ANALISA CHART (AI)*\n"
            msg += f"• Trend: {ta_data['trend']}\n"
            msg += f"• Support: {ta_data.get('support', 0):.0f}\n"
            msg += f"• Resistance: {ta_data.get('resistance', 0):.0f}\n"
            if "pivot" in ta_data: msg += f"• Pivot: {ta_data['pivot']:.0f}\n"
            msg += f"\n_\"{tech_analysis_text}\"_\n\n"
            
            # --- 4. BANDARMOLOGY ---
            msg += "🕵️ *4. FORENSIK BANDAR*\n"
            msg += f"• Status: *{forensic_status}*\n"
            if bandar_summary_lines:
                # Format sub-lines with small bullets
                for line in bandar_summary_lines:
                     msg += f"▫️ {line}\n"
            msg += f"\n_\"{forensic_analysis}\"_\n"
            if forensic_warning:
                msg += f"⚠️ *WARNING*: {forensic_warning}\n"
            msg += "\n"
            
            # --- 5. EXECUTION PLAN ---
            msg += "⚔️ *5. TRADING PLAN*\n"
            if trading_plan:
                msg += f"🟢 *BUY*: {trading_plan.get('buy_area', '-')}\n"
                msg += f"🔴 *STOP LOSS*: {trading_plan.get('stop_loss', '-')}\n"
                msg += f"🎯 *TARGET*: {trading_plan.get('target_profit', '-')}\n"
            else:
                msg += "⚠️ Wait for clear setup.\n"
            msg += "\n"
            
            # --- 6. ACTION PLAN (CIO) ---
            action_plan = ai_cio.get('action_plan', '')
            if action_plan:
                msg += "🛑 *ACTION PLAN (CIO INSTRUCTION)*\n"
                msg += "━━━━━━━━━━━━━━━━━━\n"
                
                # Handle List or String
                if isinstance(action_plan, list):
                    for item in action_plan:
                        msg += f"👉 {item}\n"
                else:
                    # Robust Line-by-Line Parsing
                    import re
                    lines = action_plan.split('\n')
                    for line in lines:
                        # Check for nested bullets (indented)
                        # Matches spaces + bullet (* or -)
                        nested_match = re.match(r'^(\s+)([*•-])\s+(.*)', line)
                        # Check for top level bullet
                        top_match = re.match(r'^([*•-])\s+(.*)', line)
                        
                        if nested_match or (line.startswith('    ') or line.startswith('\t')):
                            # It's nested
                            clean_text = line.strip().lstrip('*•-').strip()
                            if clean_text:
                                msg += f"   ▫️ {clean_text}\n"
                        elif top_match:
                            # Top level
                            clean_text = top_match.group(2).strip()
                            # remove bold markers from start/end if excessive
                            clean_text = clean_text.replace('**', '').replace('__', '')
                            msg += f"👉 *{clean_text}*\n"
                        else:
                            # Normal text (sentences describing the point)
                            clean = line.strip()
                            if clean:
                                msg += f"{clean}\n"

                msg += "━━━━━━━━━━━━━━━━━━\n\n"
            
            # --- 7. NEWS ---
            msg += "📰 *MARKET NEWES*\n"
            if news_summary:
                news_lines = news_summary.split('\n')
                # Take top 3, format cleanly
                for i, line in enumerate(news_lines[:3]):
                    msg += f"{i+1}. {line.replace('- ', '')}\n"
            else:
                msg += "• Tidak ada berita signifikan.\n"
                
            msg += "\n🤖 _Generated by StockSignal AI_"
            return msg, tech_analysis_text
            
        except Exception as e:
            self.log(f"❌ Error formatting report: {e}")
            import traceback
            traceback.print_exc()
            return "Error Generating Report", "Error"

    def send_whatsapp_message(self, phone, message, image_path=None):
        broadcast_message(phone, message, image_path)
        
        # Cleanup chart image if it exists to save storage
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                self.log(f"🗑️ Chart dihapus: {os.path.basename(image_path)}")
            except Exception as e:
                self.log(f"⚠️ Gagal menghapus chart: {e}")

    # --- HISTORY & FAVORITES ---
    def get_history(self, limit=10):
        return db_manager.get_history(limit)

    def get_favorites(self):
        return db_manager.get_favorites()

    def add_favorite(self, ticker):
        if db_manager.add_favorite(ticker):
            self.log(f"⭐ {ticker} ditambahkan ke Favorit.")
            return True
        return False

    def remove_favorite(self, ticker):
        db_manager.remove_favorite(ticker)
        self.log(f"🗑️ {ticker} dihapus dari Favorit.")

    def is_favorite(self, ticker):
        return db_manager.is_favorite(ticker)

    # --- PORTFOLIO MANAGEMENT ---
    def get_portfolio(self):
        return db_manager.get_portfolio()

    def add_portfolio_item(self, ticker, price, lots):
        """
        Adds item to portfolio with Weighted Average logic.
        Formula: New Avg = ((Old Avg * Old Lots) + (New Price * New Lots)) / (Old Lots + New Lots)
        """
        ticker = ticker.upper()
        
        # 1. Check if exists
        existing = db_manager.get_portfolio_item(ticker)
        
        final_price = price
        final_lots = lots
        
        if existing:
            old_price = existing['avg_price']
            old_lots = existing['lots']
            
            total_lots = old_lots + lots
            
            # Prevent division by zero if someone enters negative lots (selling)
            if total_lots > 0:
                weighted_avg = ((old_price * old_lots) + (price * lots)) / total_lots
                final_price = weighted_avg
                final_lots = total_lots
                self.log(f"📉 Averaging Down/Up for {ticker}: Old {old_price:,.0f} -> New {final_price:,.0f}")
            elif total_lots == 0:
                # Sold everything
                return self.remove_portfolio_item(ticker)
            else:
                self.log(f"⚠️ Cannot have negative lots for {ticker}")
                return False

        if db_manager.add_portfolio(ticker, final_price, final_lots):
            self.log(f"💼 Portfolio Saved: {ticker} @ {final_price:,.0f} (Qty: {final_lots})")
            return True
        return False

    def remove_portfolio_item(self, ticker):
        if db_manager.delete_portfolio(ticker):
            self.log(f"🗑️ Removed {ticker} from Portfolio.")
            return True
        return False

    def get_portfolio_summary(self):
        """Returns portfolio list with added Real-Time P/L data."""
        portfolio = self.get_portfolio()
        if not portfolio:
            return []

        self.log("💼 Calculating Portfolio Performance...")
        import yfinance as yf
        
        # Prepare Tickers for Bulk Fetch (Add .JK)
        yf_tickers = [p['ticker'] + ".JK" for p in portfolio]
        if not yf_tickers:
            return portfolio

        try:
            # Efficient Bulk Fetch
            tickers_str = " ".join(yf_tickers)
            # Use '1d' history to get the absolute latest close
            data = yf.download(tickers_str, period="1d", progress=False)['Close']
            
            # Handle single ticker result (Series) vs multiple (DataFrame)
            is_series = len(yf_tickers) == 1
            
            for item in portfolio:
                sym = item['ticker'] + ".JK"
                current_price = 0
                
                try:
                    if is_series:
                        if not data.empty:
                            current_price = float(data.iloc[-1])
                    else:
                        if sym in data.columns:
                            # access last row for that symbol
                            val = data[sym].iloc[-1]
                            current_price = float(val)
                except Exception as e:
                    self.log(f"⚠️ Price fetch error for {sym}: {e}")

                # Calculations
                # 1 Lot = 100 Shares (Standard IDX)
                item['current_price'] = current_price
                
                if current_price > 0:
                    initial_investment = item['avg_price'] * item['lots'] * 100
                    current_market_val = current_price * item['lots'] * 100
                    
                    pl_value = current_market_val - initial_investment
                    pl_pct = (pl_value / initial_investment) * 100 if initial_investment != 0 else 0
                    
                    item['market_value'] = current_market_val
                    item['pl_value'] = pl_value
                    item['pl_pct'] = pl_pct
                else:
                    item['market_value'] = 0
                    item['pl_value'] = 0
                    item['pl_pct'] = 0

        except Exception as e:
            self.log(f"❌ Portfolio Analysis Error: {e}")
            
        return portfolio

    # --- SETTINGS / CONFIG ---
    def get_config(self):
        """Reads current environment variables useful for UI."""
        return {
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
            "SERPER_API_KEY": os.getenv("SERPER_API_KEY", ""),
            "GOAPI_API_KEY": os.getenv("GOAPI_API_KEY", ""),
            "TARGET_PHONE": os.getenv("TARGET_PHONE", ""),
            "AI_MODEL": os.getenv("AI_MODEL", "gemini-2.0-flash-exp") # Default to fast free model
        }

    def save_config(self, config_dict):
        """Writes configuration to .env file and updates current environment."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        
        try:
            # 1. Read existing lines to preserve comments if possible, or just overwrite simple
            # For simplicity and robustness, we'll read, update known keys, and write back.
            
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
            
            # Map of keys to update
            keys_to_update = {
                "GOOGLE_API_KEY": config_dict.get("GOOGLE_API_KEY"),
                "SERPER_API_KEY": config_dict.get("SERPER_API_KEY"),
                "GOAPI_API_KEY": config_dict.get("GOAPI_API_KEY"),
                "TARGET_PHONE": config_dict.get("TARGET_PHONE"),
                "AI_MODEL": config_dict.get("AI_MODEL")
            }
            
            new_lines = []
            processed_keys = set()
            
            for line in lines:
                key_match = None
                for key in keys_to_update:
                    if line.startswith(f"{key}="):
                        key_match = key
                        break
                
                if key_match:
                    val = keys_to_update[key_match]
                    if val is not None:
                        new_lines.append(f"{key_match}={val}\n")
                        processed_keys.add(key_match)
                    else:
                        new_lines.append(line) # Keep as is if None passed
                else:
                    new_lines.append(line)
            
            # Append missing keys
            for key, val in keys_to_update.items():
                if key not in processed_keys and val is not None:
                    if new_lines and not new_lines[-1].endswith("\n"):
                        new_lines.append("\n")
                    new_lines.append(f"{key}={val}\n")
            
            # Write back
            with open(env_path, "w") as f:
                f.writelines(new_lines)
                
            # Update current process env
            for key, val in keys_to_update.items():
                if val:
                    os.environ[key] = val
            
            # Reload dotenv to be sure
            load_dotenv(override=True)
            
            # --- HOT RELOAD COMPONENTS ---
            # Re-initialize GoAPI Client and Quant Engine with new keys
            if os.getenv("GOAPI_API_KEY") and GoApiClient:
                self.log("🔄 Reloading GoAPI Client & Quant Engine...")
                self.goapi_client = GoApiClient()
                self.quant_engine = QuantAnalyzer(self.goapi_client)
            else:
                self.goapi_client = None
                self.quant_engine = QuantAnalyzer(None)
            
            self.log("✅ Configuration saved to .env")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to save config: {e}")
            return False
