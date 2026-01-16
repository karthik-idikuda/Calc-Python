import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import threading
import re
import math
import numpy as np
import sympy as sp
from sympy import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
from PIL import Image, ImageTk

class AICalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Calculator with Voice")
        self.root.geometry("900x950")
        self.root.configure(bg='#1a1a2e')
        
        # Configure Gemini API
        self.api_key = "AIzaSyC5YkSctoGAPaXmfb0Om4HGs1eV8xXR8m4"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize speech recognition and text-to-speech
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 160)
            self.tts_engine.setProperty('volume', 0.9)
            
            # Set voice to a more natural one if available
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice or use the first available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'karen' in voice.name.lower() or 'samantha' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
                    
        except Exception as e:
            print(f"Error initializing audio components: {e}")
            self.recognizer = None
            self.microphone = None
            self.tts_engine = None
        
        # Variables
        self.is_listening = False
        self.calculation_history = []
        
        # Setup GUI
        self.setup_gui()
        
        # Adjust microphone for ambient noise (only if audio is available)
        if self.microphone and self.recognizer:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                print(f"Could not adjust microphone: {e}")
        
        # Welcome message
        self.speak("AI Calculator initialized and ready to use!")
    
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = tk.Label(main_frame, text="🤖 AI Calculator with Voice 🎤", 
                              font=('Helvetica', 20, 'bold'), 
                              bg='#1a1a2e', fg='#00d4ff')
        title_label.pack(pady=(0, 15))
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg='#1a1a2e')
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Expression entry
        tk.Label(input_frame, text="Mathematical Expression:", font=('Helvetica', 14, 'bold'), 
                bg='#1a1a2e', fg='#ffffff').pack(anchor=tk.W)
        
        self.expression_var = tk.StringVar()
        self.expression_entry = tk.Entry(input_frame, textvariable=self.expression_var,
                                        font=('Consolas', 16), width=50,
                                        bg='#16213e', fg='#00ff88', 
                                        insertbackground='#00ff88',
                                        relief='flat', bd=5)
        self.expression_entry.pack(fill=tk.X, pady=(8, 15), ipady=8)
        self.expression_entry.bind('<Return>', self.calculate_expression)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons with modern styling
        self.calculate_btn = tk.Button(button_frame, text="🧮 Calculate", 
                                      command=self.calculate_expression,
                                      bg='#4caf50', fg='white', font=('Helvetica', 12, 'bold'),
                                      padx=25, pady=8, relief='flat', bd=0,
                                      activebackground='#45a049', cursor='hand2')
        self.calculate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Voice button with status indication
        self.voice_btn = tk.Button(button_frame, text="🎤 Start Voice", 
                                  command=self.toggle_voice_input,
                                  bg='#2196f3', fg='white', font=('Helvetica', 12, 'bold'),
                                  padx=25, pady=8, relief='flat', bd=0,
                                  activebackground='#1976d2', cursor='hand2')
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = tk.Button(button_frame, text="🗑️ Clear All", 
                                  command=self.clear_all,
                                  bg='#f44336', fg='white', font=('Helvetica', 12, 'bold'),
                                  padx=25, pady=8, relief='flat', bd=0,
                                  activebackground='#d32f2f', cursor='hand2')
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.graph_btn = tk.Button(button_frame, text="📊 Graph Function", 
                                  command=self.plot_function,
                                  bg='#ff9800', fg='white', font=('Helvetica', 12, 'bold'),
                                  padx=25, pady=8, relief='flat', bd=0,
                                  activebackground='#f57c00', cursor='hand2')
        self.graph_btn.pack(side=tk.LEFT)
        
        # Add microphone test button
        self.mic_test_btn = tk.Button(button_frame, text="🎤 Test Mic", 
                                     command=self.test_microphone,
                                     bg='#9c27b0', fg='white', font=('Helvetica', 12, 'bold'),
                                     padx=25, pady=8, relief='flat', bd=0,
                                     activebackground='#7b1fa2', cursor='hand2')
        self.mic_test_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Calculator buttons frame
        calc_frame = tk.Frame(main_frame, bg='#1a1a2e')
        calc_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create calculator buttons
        self.create_calculator_buttons(calc_frame)
        
        # Result frame
        result_frame = tk.Frame(main_frame, bg='#1a1a2e')
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Result display
        tk.Label(result_frame, text="📋 Calculation Results & History:", font=('Helvetica', 14, 'bold'), 
                bg='#1a1a2e', fg='#ffffff').pack(anchor=tk.W)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=16, 
                                                    font=('Consolas', 12),
                                                    bg='#0f0f23', fg='#00ff88',
                                                    insertbackground='#00ff88',
                                                    relief='flat', bd=5,
                                                    selectbackground='#16213e')
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(8, 15))
        
        # Status label
        self.status_label = tk.Label(main_frame, text="🟢 Ready - Say 'Calculate' followed by your expression", 
                                    font=('Helvetica', 11), 
                                    bg='#1a1a2e', fg='#00d4ff')
        self.status_label.pack(pady=(0, 5))
        
    def create_calculator_buttons(self, parent):
        # Button layout with improved design
        buttons = [
            ['7', '8', '9', '÷', 'sin', 'cos'],
            ['4', '5', '6', '×', 'tan', 'log'],
            ['1', '2', '3', '−', '√', 'ln'],
            ['0', '.', '=', '+', '^', 'π'],
            ['(', ')', 'C', '⌫', 'e', '°']
        ]
        
        for i, row in enumerate(buttons):
            row_frame = tk.Frame(parent, bg='#1a1a2e')
            row_frame.pack(fill=tk.X, pady=3)
            
            for j, btn_text in enumerate(row):
                # Button styling based on type
                if btn_text == '=':
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=self.calculate_expression,
                                   bg='#4caf50', fg='white', font=('Helvetica', 12, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#45a049', cursor='hand2')
                elif btn_text == 'C':
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=self.clear_expression,
                                   bg='#f44336', fg='white', font=('Helvetica', 12, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#d32f2f', cursor='hand2')
                elif btn_text == '⌫':
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=self.backspace,
                                   bg='#ff9800', fg='white', font=('Helvetica', 12, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#f57c00', cursor='hand2')
                elif btn_text in ['÷', '×', '−', '+', '^']:
                    # Operator buttons
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=lambda x=btn_text: self.button_click(x),
                                   bg='#2196f3', fg='white', font=('Helvetica', 12, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#1976d2', cursor='hand2')
                elif btn_text in ['sin', 'cos', 'tan', 'log', 'ln', '√', 'π', 'e', '°']:
                    # Function buttons
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=lambda x=btn_text: self.button_click(x),
                                   bg='#9c27b0', fg='white', font=('Helvetica', 11, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#7b1fa2', cursor='hand2')
                else:
                    # Number and other buttons
                    btn = tk.Button(row_frame, text=btn_text, 
                                   command=lambda x=btn_text: self.button_click(x),
                                   bg='#37474f', fg='white', font=('Helvetica', 12, 'bold'),
                                   width=10, height=2, relief='flat', bd=0,
                                   activebackground='#455a64', cursor='hand2')
                
                btn.pack(side=tk.LEFT, padx=2)
    
    def button_click(self, value):
        current = self.expression_var.get()
        
        # Handle special buttons with Unicode symbols
        if value == 'π':
            value = 'pi'
        elif value == 'e':
            value = 'e'
        elif value == '^':
            value = '**'
        elif value == '÷':
            value = '/'
        elif value == '×':
            value = '*'
        elif value == '−':
            value = '-'
        elif value == '√':
            value = 'sqrt('
        elif value == '°':
            # Convert last result from radians to degrees if applicable
            if hasattr(self, 'last_result') and isinstance(self.last_result, (int, float)):
                degrees = math.degrees(self.last_result)
                self.expression_var.set(str(degrees))
                self.speak(f"Converted to {degrees} degrees")
                return
            else:
                return
        elif value in ['sin', 'cos', 'tan', 'log', 'ln']:
            value = value + '('
        
        new_expression = current + str(value)
        self.expression_var.set(new_expression)
        
        # Provide audio feedback for button clicks
        if value in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            # Just a subtle click sound effect (can be implemented)
            pass
    
    def clear_expression(self):
        self.expression_var.set("")
    
    def backspace(self):
        current = self.expression_var.get()
        self.expression_var.set(current[:-1])
    
    def clear_all(self):
        self.expression_var.set("")
        self.result_text.delete(1.0, tk.END)
        self.calculation_history.clear()
        self.update_status("🟢 Calculator cleared and ready")
        
        # Add welcome message to result area
        welcome_msg = """🎉 Welcome to AI Calculator with Voice! 🎉

🔹 Enter mathematical expressions in the input field
🔹 Click buttons to build expressions
🔹 Use voice commands: "Calculate 2 + 3" or "What is sine of pi"
🔹 Click Graph to visualize functions
🔹 Supports: basic math, trigonometry, logarithms, and more!

Examples:
• 2 + 3 * 4
• sin(pi/2)
• sqrt(16)
• log(100)
• 2^10

Try saying: "Calculate two plus three times four"
"""
        self.result_text.insert(tk.END, welcome_msg)
    
    def calculate_expression(self, event=None):
        expression = self.expression_var.get().strip()
        if not expression:
            self.speak("Please enter a mathematical expression")
            return
        
        self.update_status("🔄 Calculating...")
        self.speak("Calculating")
        
        try:
            # First try to use Gemini AI for complex expressions
            ai_result = self.get_ai_calculation(expression)
            
            if ai_result:
                self.display_result(expression, ai_result, "AI")
                self.update_status("✅ Calculation complete using AI")
            else:
                # Fallback to local calculation
                local_result = self.calculate_locally(expression)
                self.display_result(expression, local_result, "Local")
                self.update_status("✅ Calculation complete using local computation")
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.display_result(expression, error_msg, "Error")
            self.update_status("❌ Calculation failed")
            self.speak("Calculation failed. Please check your expression.")
    
    def get_ai_calculation(self, expression):
        try:
            prompt = f"""
            Please solve this mathematical expression step by step: {expression}
            
            Provide:
            1. The final numerical answer
            2. A brief explanation of the solution steps
            3. If it's a complex mathematical concept, provide some context
            
            Format your response clearly with the final answer prominently displayed.
            If the expression involves calculus, algebra, or advanced mathematics, show the work.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"AI calculation error: {e}")
            return None
    
    def calculate_locally(self, expression):
        try:
            # Prepare expression for evaluation
            expr = expression.lower()
            
            # Replace common mathematical expressions and Unicode symbols
            replacements = {
                'sin': 'sin',
                'cos': 'cos', 
                'tan': 'tan',
                'log': 'log10',
                'ln': 'log',
                'sqrt': 'sqrt',
                '√': 'sqrt',
                'pi': 'pi',
                'π': 'pi',
                'e': 'E',
                '^': '**',
                '÷': '/',
                '×': '*',
                '−': '-'
            }
            
            for old, new in replacements.items():
                expr = expr.replace(old, new)
            
            # Use sympy for evaluation
            result = sp.sympify(expr)
            numerical_result = float(result.evalf())
            
            self.last_result = numerical_result
            
            # Format result
            if abs(numerical_result) < 0.001 or abs(numerical_result) > 1000000:
                formatted_result = f"{numerical_result:.6e}"
            else:
                formatted_result = f"{numerical_result:.6f}".rstrip('0').rstrip('.')
            
            return formatted_result
                
        except Exception as e:
            raise Exception(f"Calculation error: {str(e)}")
    
    def display_result(self, expression, result, source):
        timestamp = self.get_timestamp()
        
        # Add to history
        self.calculation_history.append({
            'expression': expression,
            'result': result,
            'source': source,
            'timestamp': timestamp
        })
        
        # Display in result text with better formatting
        self.result_text.insert(tk.END, f"\n🕒 [{timestamp}] Source: {source}\n")
        self.result_text.insert(tk.END, f"📝 Expression: {expression}\n")
        self.result_text.insert(tk.END, f"🔢 Result: {result}\n")
        self.result_text.insert(tk.END, "─" * 60 + "\n")
        self.result_text.see(tk.END)
        
        # Speak result with improved logic
        try:
            if source != "Error":
                # Extract numerical result for speaking
                if source == "AI":
                    # Try to extract the final answer from AI response
                    lines = str(result).split('\n')
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['answer', 'result', '=', 'equals']):
                            # Try to extract number
                            import re
                            numbers = re.findall(r'-?\d+\.?\d*', line)
                            if numbers:
                                self.speak(f"The answer is {numbers[-1]}")
                                return
                    self.speak("Calculation completed. Check the result above.")
                else:
                    # Local calculation - speak the numerical result
                    try:
                        num_result = float(str(result))
                        if abs(num_result) < 1000000:
                            self.speak(f"The result is {num_result}")
                        else:
                            self.speak("Result calculated. Check the display for the full answer.")
                    except:
                        self.speak("Calculation completed")
            else:
                self.speak("There was an error in the calculation")
        except Exception as e:
            print(f"TTS error: {e}")
    
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def toggle_voice_input(self):
        if not self.recognizer or not self.microphone:
            self.speak("Voice functionality is not available. Audio components failed to initialize.")
            messagebox.showwarning("Audio Error", "Voice functionality is not available. Please check your microphone and audio settings.")
            return
            
        if not self.is_listening:
            self.start_voice_input()
        else:
            self.stop_voice_input()
    
    def start_voice_input(self):
        self.is_listening = True
        self.voice_btn.config(text="🛑 Stop Voice", bg='#f44336', activebackground='#d32f2f')
        self.update_status("🎤 Listening... Say 'Calculate' followed by your math expression")
        self.speak("Voice input activated. Say 'Calculate' followed by your mathematical expression.")
        
        # Start voice recognition in a separate thread
        voice_thread = threading.Thread(target=self.voice_recognition_loop)
        voice_thread.daemon = True
        voice_thread.start()
    
    def stop_voice_input(self):
        self.is_listening = False
        self.voice_btn.config(text="🎤 Start Voice", bg='#2196f3', activebackground='#1976d2')
        self.update_status("🔴 Voice input stopped")
        self.speak("Voice input deactivated")
    
    def voice_recognition_loop(self):
        print("Voice recognition loop started")
        
        # Adjust microphone settings for better detection on macOS
        with self.microphone as source:
            print("Adjusting microphone sensitivity for macOS...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Initial energy threshold: {self.recognizer.energy_threshold}")
        
        # Aggressive settings for macOS microphone detection
        self.recognizer.energy_threshold = 100  # Much lower for MacBook Air microphone
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5  # Shorter pause detection
        self.recognizer.phrase_threshold = 0.2  # Lower minimum speaking duration
        self.recognizer.non_speaking_duration = 0.3  # Shorter non-speaking detection
        
        print(f"macOS optimized settings - Energy threshold: {self.recognizer.energy_threshold}")
        print("📢 IMPORTANT: Speak LOUDLY and CLEARLY into your MacBook microphone!")
        
        while self.is_listening:
            try:
                print("\n🎤 Ready to listen... Say 'CALCULATE TWO PLUS THREE' loudly!")
                with self.microphone as source:
                    # Optimized for MacBook Air microphone
                    print("👂 Listening actively... SPEAK NOW!")
                    
                    # Shorter timeout, longer phrase limit for better detection
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=8)
                    print("🔊 Audio captured! Processing speech...")
                
                try:
                    # Recognize speech using Google
                    print("🌐 Sending to Google Speech Recognition...")
                    text = self.recognizer.recognize_google(audio)
                    print(f"✅ SUCCESS! Recognized text: '{text}'")
                    # Process voice command with error handling
                    try:
                        self.root.after(0, lambda t=text: self.process_voice_command(t))
                    except Exception as cmd_error:
                        print(f"❌ Error scheduling voice command: {cmd_error}")
                    
                except sr.UnknownValueError:
                    # Could not understand audio
                    print("⚠️  Audio was captured but couldn't understand speech. Try speaking LOUDER and more clearly.")
                    pass
                except sr.RequestError as e:
                    print(f"❌ Google Speech Recognition error: {e}")
                    try:
                        self.root.after(0, lambda: self.update_status(f"🔴 Speech recognition error: {e}"))
                    except:
                        pass
                    
            except sr.WaitTimeoutError:
                # No speech detected within timeout
                print("⏰ No speech detected. Try speaking LOUDER directly into the microphone...")
                pass
            except Exception as e:
                print(f"❌ Voice input error: {e}")
                self.root.after(0, lambda: self.update_status(f"🔴 Voice input error: {e}"))
                break
        print("Voice recognition loop ended")
    
    def process_voice_command(self, text):
        try:
            print(f"Processing voice command: '{text}'")
            text = text.lower().strip()
            
            # Update status safely
            self.update_status(f"🎙️ Heard: '{text}'")
            print(f"Attempting to speak: 'I heard: {text}'")
            self.speak(f"I heard: {text}")
            
            # Process voice commands
            if any(word in text for word in ["calculate", "compute", "solve", "what is", "find"]):
                print("Found calculation trigger word")
                # Extract mathematical expression after trigger words
                math_expr = text
                for trigger in ["calculate", "compute", "solve", "what is", "find"]:
                    if trigger in text:
                        math_expr = text.split(trigger)[-1].strip()
                        break
                    
                print(f"Extracted math expression: '{math_expr}'")
                # Convert speech to mathematical notation
                converted_expr = self.speech_to_math(math_expr)
                print(f"Converted expression: '{converted_expr}'")
                
                if converted_expr:
                    self.expression_var.set(converted_expr)
                    self.speak(f"Calculating: {converted_expr}")
                    print(f"✅ Expression set to: '{converted_expr}', triggering calculation...")
                    # Auto-calculate after voice input with safer threading
                    self.root.after(1500, self.calculate_expression)
                else:
                    self.speak("I couldn't understand the mathematical expression. Please try again.")
                
            elif "clear" in text or "reset" in text:
                print("Clear command detected")
                self.clear_all()
                self.speak("Calculator cleared")
                
            elif "stop" in text or "quit" in text or "exit" in text:
                print("Stop command detected")
                self.stop_voice_input()
                
            elif "graph" in text or "plot" in text:
                print("Graph command detected")
                self.speak("Opening graphing function")
                self.plot_function()
                
            else:
                print("No specific command found, trying to interpret as math expression")
                # Try to interpret the entire text as a mathematical expression
                math_expr = self.speech_to_math(text)
                print(f"Direct conversion result: '{math_expr}'")
                
                # Check if it's a valid math expression (contains operators)
                if math_expr and any(op in math_expr for op in ['+', '-', '*', '/', '**', 'sin', 'cos', 'sqrt', 'log']):
                    self.expression_var.set(math_expr)
                    self.speak(f"Calculating: {math_expr}")
                    print(f"✅ Setting expression and triggering calculation for: '{math_expr}'")
                    # Auto-calculate after a short delay
                    self.root.after(1500, self.calculate_expression)
                else:
                    self.speak("Please say 'Calculate' followed by your math expression, like 'Calculate two plus three'.")
                    
        except Exception as e:
            print(f"❌ Error in process_voice_command: {e}")
            self.speak("Sorry, there was an error processing your command.")
            # Update status to show error
            self.update_status(f"❌ Voice command error: {str(e)}")
    
    def speech_to_math(self, text):
        # Convert spoken words to mathematical notation
        text = text.lower()
        
        # Enhanced replacements for better speech recognition
        replacements = {
            "plus": " + ",
            "add": " + ",
            "and": " + ",
            "minus": " - ",
            "subtract": " - ",
            "take away": " - ",
            "times": " * ",
            "multiply": " * ",
            "multiplied by": " * ",
            "x": " * ",
            "divided by": " / ",
            "divide": " / ",
            "over": " / ",
            "power": " ** ",
            "to the power of": " ** ",
            "to the": " ** ",
            "raised to": " ** ",
            "squared": " ** 2",
            "cubed": " ** 3",
            "square root of": " sqrt(",
            "square root": " sqrt(",
            "sqrt": " sqrt(",
            "sine of": " sin(",
            "sine": " sin(",
            "sin": " sin(",
            "cosine of": " cos(",
            "cosine": " cos(",
            "cos": " cos(",
            "tangent of": " tan(",
            "tangent": " tan(",
            "tan": " tan(",
            "log of": " log(",
            "log": " log(",
            "logarithm": " log(",
            "natural log of": " ln(",
            "natural log": " ln(",
            "ln": " ln(",
            "pi": " pi ",
            "pie": " pi ",
            "open parenthesis": " ( ",
            "close parenthesis": " ) ",
            "left parenthesis": " ( ",
            "right parenthesis": " ) ",
            "open bracket": " ( ",
            "close bracket": " ) ",
            "point": ".",
            "decimal": ".",
            "dot": ".",
        }
        
        # Replace number words with enhanced coverage
        number_words = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
            "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
            "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
            "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
            "eighty": "80", "ninety": "90", "hundred": "100", "thousand": "1000"
        }
        
        # Apply replacements
        for word, replacement in replacements.items():
            text = text.replace(word, replacement)
            
        for word, number in number_words.items():
            text = text.replace(word, number)
        
        # Clean up the expression
        import re as regex_module  # Import with alias to avoid sympy conflict
        text = regex_module.sub(r'\s+', ' ', text)  # Normalize spaces
        text = text.strip()
        
        # Remove non-mathematical characters but keep spaces for now
        text = regex_module.sub(r'[^\d+\-*/().a-z\s]', '', text)
        
        # Final cleanup - remove extra spaces
        text = regex_module.sub(r'\s+', '', text)
        
        return text
    
    def speak(self, text):
        def tts_thread():
            try:
                if self.tts_engine and text and text.strip():
                    # Stop any running speech first
                    try:
                        self.tts_engine.stop()
                    except:
                        pass
                    # Set properties again to ensure consistency
                    self.tts_engine.setProperty('rate', 160)
                    self.tts_engine.setProperty('volume', 0.9)
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                else:
                    print(f"TTS: {text}")  # Fallback to console output
            except Exception as e:
                print(f"TTS error: {e}")
        
        # Only speak if TTS is available and text is provided
        if self.tts_engine and text and text.strip():
            try:
                thread = threading.Thread(target=tts_thread)
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(f"TTS threading error: {e}")
                print(f"TTS fallback: {text}")
        else:
            print(f"TTS: {text}")
    
    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def test_microphone(self):
        """Test microphone functionality optimized for macOS"""
        if not self.recognizer or not self.microphone:
            messagebox.showerror("Error", "Audio components not available")
            return
            
        self.speak("Testing microphone. Please speak loudly and clearly.")
        
        try:
            with self.microphone as source:
                print("🎤 MACBOOK MICROPHONE TEST")
                print("Adjusting for MacBook ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Use same aggressive settings as voice loop
                self.recognizer.energy_threshold = 100
                print(f"Energy threshold set to: {self.recognizer.energy_threshold}")
                print("📢 Speak LOUDLY for 5 seconds: 'HELLO CALCULATOR TEST'")
                
                # Listen for test audio with macOS optimized settings
                audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=5)
                print("🔊 Audio captured from MacBook microphone! Attempting recognition...")
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    message = f"✅ MacBook microphone working perfectly! You said: '{text}'"
                    print(message)
                    self.speak(f"Excellent! Microphone test successful. You said: {text}")
                    messagebox.showinfo("Microphone Test Success", message)
                    
                except sr.UnknownValueError:
                    message = "⚠️ MacBook microphone detected audio but couldn't understand speech.\n\nTips:\n• Speak directly into the microphone area\n• Speak louder and more clearly\n• Try moving closer to the screen\n• Check for background noise"
                    print(message)
                    self.speak("Microphone detected audio but couldn't understand speech. Try speaking louder.")
                    messagebox.showwarning("Microphone Test - Partial Success", message)
                    
                except sr.RequestError as e:
                    message = f"❌ Speech recognition service error: {e}\n\nCheck your internet connection."
                    print(message)
                    messagebox.showerror("Microphone Test Error", message)
                    
        except sr.WaitTimeoutError:
            message = "❌ No audio detected from MacBook microphone.\n\nSolutions:\n• Check System Preferences > Security & Privacy > Microphone\n• Grant Python/Terminal microphone access\n• Speak louder and closer to the microphone\n• Try restarting the application"
            print(message)
            self.speak("No audio detected. Please check microphone permissions in System Preferences.")
            messagebox.showerror("Microphone Test Failed", message)
            
        except Exception as e:
            message = f"❌ Microphone test failed: {e}"
            print(message)
            messagebox.showerror("Microphone Test Error", message)
    
    def plot_function(self):
        expression = self.expression_var.get().strip()
        if not expression:
            messagebox.showwarning("Warning", "Please enter a function to plot")
            return
        
        try:
            # Create a new window for the plot
            plot_window = tk.Toplevel(self.root)
            plot_window.title("Function Graph")
            plot_window.geometry("600x500")
            
            # Prepare the expression for plotting
            x = sp.Symbol('x')
            
            # Replace common patterns for sympy
            expr_str = expression.lower()
            expr_str = expr_str.replace('^', '**')
            expr_str = expr_str.replace('sin', 'sin')
            expr_str = expr_str.replace('cos', 'cos')
            expr_str = expr_str.replace('tan', 'tan')
            expr_str = expr_str.replace('log', 'log')
            expr_str = expr_str.replace('ln', 'log')
            expr_str = expr_str.replace('sqrt', 'sqrt')
            
            # Parse the expression
            expr = sp.sympify(expr_str)
            
            # Create numerical function
            f = sp.lambdify(x, expr, 'numpy')
            
            # Generate x values
            x_vals = np.linspace(-10, 10, 1000)
            y_vals = f(x_vals)
            
            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(x_vals, y_vals, 'b-', linewidth=2)
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('x')
            ax.set_ylabel('f(x)')
            ax.set_title(f'Graph of: {expression}')
            ax.axhline(y=0, color='k', linewidth=0.5)
            ax.axvline(x=0, color='k', linewidth=0.5)
            
            # Embed plot in tkinter window
            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Plot Error", f"Could not plot function: {str(e)}")

def main():
    root = tk.Tk()
    app = AICalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
