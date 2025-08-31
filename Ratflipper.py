#!/usr/bin/env python3
"""
Rat Flipper GUI
"""

# everything is working.

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import asyncio
import threading 
import json
import re
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import aiofiles
import nats
from nats.errors import TimeoutError, NoServersError
import aiohttp
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pandas as pd
import os
from collections import defaultdict, deque
import glob
import sys
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import urllib.request
import io
import json as pyjson
import tkinter.simpledialog
import colorsys
import platform
if platform.system() == "Windows":
    import winsound
import wave
import struct
import urllib.parse
import math
from customtkinter import CTkTabview
import requests
import zipfile
import shutil
import subprocess

# --- Auto Updater Class ---

class AutoUpdater:
    """GitHub-based auto-updater for Rat Flipper Pro"""
    
    def __init__(self, current_version="1.0.0"):
        self.current_version = current_version
        # Your actual GitHub repository
        self.github_repo = "ratflipper/Ratflipper-project"
        self.github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.download_url = None
        self.latest_version = None
        self.update_available = False
        self.update_window = None
        self.enabled = True  # Set to False to disable auto-updater
        
    def check_for_updates(self, parent=None, silent=False):
        """Check for updates on GitHub"""
        if not self.enabled:
            if not silent:
                messagebox.showinfo("Updater", "Auto-updater is disabled.")
            return False
            
        try:
            print(f"🔍 Checking for updates... Current version: {self.current_version}")
            # Get latest release info from GitHub API
            response = requests.get(self.github_api_url, timeout=10)
            print(f"📡 GitHub API response status: {response.status_code}")
            
            if response.status_code == 200:
                release_data = response.json()
                print(f"📦 Release data: {release_data}")
                
                # Extract version and clean it
                raw_tag = release_data.get('tag_name', '')
                # Remove 'v' and any leading dots or non-numeric characters
                cleaned_tag = raw_tag.lstrip('v').lstrip('.')
                self.latest_version = cleaned_tag if cleaned_tag else '0.0.0'
                print(f"🏷️ Latest version from GitHub: {self.latest_version} (cleaned from '{raw_tag}')")
                
                # Get download URL
                assets = release_data.get('assets', [])
                self.download_url = assets[0]['browser_download_url'] if assets else None
                print(f"📥 Download URL: {self.download_url}")
                
                # Compare versions
                comparison_result = self._compare_versions(self.latest_version, self.current_version)
                print(f"⚖️ Version comparison: {self.current_version} vs {self.latest_version} = {comparison_result}")
                
                if comparison_result > 0:
                    self.update_available = True
                    if not silent:
                        self._show_update_dialog(parent)
                    return True
                else:
                    if not silent:
                        messagebox.showinfo("Updater", f"You have the latest version! (Current: {self.current_version}, Latest: {self.latest_version})")
                    return False
            elif response.status_code == 404:
                # Repository not found - D
                if not silent:
                    messagebox.showinfo("Updater", "GitHub repository not found. Please set up your repository or contact support.")
                return False
            else:
                if not silent:
                    messagebox.showerror("Update Error", f"Failed to check for updates: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            if not silent:
                messagebox.showerror("Update Error", "No internet connection. Cannot check for updates.")
            return False
        except Exception as e:
            print(f"❌ Error checking for updates: {str(e)}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            if not silent:
                messagebox.showerror("Update Error", f"Error checking for updates: {str(e)}")
            return False
    
    def _compare_versions(self, version1, version2):
        """Compare two version strings (e.g., '1.2.3' vs '1.2.4')"""
        try:
            # Clean version strings - remove any non-numeric characters except dots
            v1_clean = ''.join(c for c in version1 if c.isdigit() or c == '.')
            v2_clean = ''.join(c for c in version2 if c.isdigit() or c == '.')
            
            # Split and convert to integers, handling empty parts
            v1_parts = []
            for part in v1_clean.split('.'):
                if part.strip():
                    v1_parts.append(int(part))
                else:
                    v1_parts.append(0)
                    
            v2_parts = []
            for part in v2_clean.split('.'):
                if part.strip():
                    v2_parts.append(int(part))
                else:
                    v2_parts.append(0)
            
            # Pad with zeros if needed
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            return 0
        except (ValueError, AttributeError) as e:
            print(f"Error comparing versions '{version1}' and '{version2}': {e}")
            # If there's an error, assume versions are equal
            return 0
    
    def _get_release_notes(self):
        """Fetch actual release notes from GitHub"""
        try:
            response = requests.get(self.github_api_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                body = release_data.get('body', '')
                if body:
                    # Convert markdown to simple text
                    lines = body.split('\n')
                    formatted_notes = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith('- ') or line.startswith('* '):
                            formatted_notes.append(line)
                        elif line.startswith('##'):
                            formatted_notes.append(f"\n{line.replace('#', '').strip()}")
                        elif line and not line.startswith('#'):
                            formatted_notes.append(line)
                    return '\n'.join(formatted_notes)
        except Exception as e:
            print(f"Error fetching release notes: {e}")
        return None
    
    def _show_update_dialog(self, parent):
        """Show update dialog with skip option"""
        if self.update_window:
            self.update_window.destroy()
            
        self.update_window = ctk.CTkToplevel(parent)
        self.update_window.title("Update Available")
        self.update_window.geometry("600x500")
        self.update_window.resizable(False, False)
        self.update_window.attributes('-topmost', True)
        
        # Center the window
        self.update_window.update_idletasks()
        x = (self.update_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.update_window.winfo_screenheight() // 2) - (500 // 2)
        self.update_window.geometry(f"600x500+{x}+{y}")
        
        # Main frame with gradient-like effect
        main_frame = ctk.CTkFrame(
            self.update_window, 
            fg_color="#1a1d2e", 
            corner_radius=24, 
            border_width=2, 
            border_color="#00d4ff"
        )
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Header with enhanced styling
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(24, 16))
        
        # App icon and title
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🦁",
            font=("Segoe UI Emoji", 32),
            text_color="#00d4ff"
        )
        icon_label.pack(side="left", padx=(0, 12))
        
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        header_label = ctk.CTkLabel(
            title_frame,
            text="Update Available",
            font=("Segoe UI", 28, "bold"),
            text_color="#ffffff"
        )
        header_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="A new version of Rat Flipper Pro is ready to install",
            font=("Segoe UI", 14),
            text_color="#a0aec0"
        )
        subtitle_label.pack(anchor="w")
        
        # Version info with enhanced styling
        version_frame = ctk.CTkFrame(main_frame, fg_color="#232946", corner_radius=12)
        version_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        version_header = ctk.CTkLabel(
            version_frame,
            text="Version Information",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        )
        version_header.pack(pady=(16, 12), padx=16, anchor="w")
        
        # Version comparison
        version_comparison_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
        version_comparison_frame.pack(fill="x", padx=16, pady=(0, 16))
        
        # Current version
        current_version_frame = ctk.CTkFrame(version_comparison_frame, fg_color="#1a1d2e", corner_radius=8)
        current_version_frame.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            current_version_frame,
            text="Current Version",
            font=("Segoe UI", 12, "bold"),
            text_color="#a0aec0"
        ).pack(anchor="w", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(
            current_version_frame,
            text=self.current_version,
            font=("Segoe UI", 18, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=12, pady=(0, 8))
        
        # Latest version
        latest_version_frame = ctk.CTkFrame(version_comparison_frame, fg_color="#00d4ff", corner_radius=8)
        latest_version_frame.pack(fill="x")
        
        ctk.CTkLabel(
            latest_version_frame,
            text="Latest Version",
            font=("Segoe UI", 12, "bold"),
            text_color="#181c24"
        ).pack(anchor="w", padx=12, pady=(8, 4))
        
        ctk.CTkLabel(
            latest_version_frame,
            text=self.latest_version,
            font=("Segoe UI", 18, "bold"),
            text_color="#181c24"
        ).pack(anchor="w", padx=12, pady=(0, 8))
        
        # Release notes with enhanced styling
        notes_label = ctk.CTkLabel(
            main_frame,
            text="📝 Release Notes",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        )
        notes_label.pack(pady=(0, 8), anchor="w", padx=24)
        
        # Scrollable text area for release notes
        notes_frame = ctk.CTkFrame(main_frame, fg_color="#232946", corner_radius=12, border_width=1, border_color="#2d3748")
        notes_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        
        notes_text = ctk.CTkTextbox(
            notes_frame,
            font=("Segoe UI", 12),
            text_color="#e2e8f0",
            fg_color="transparent",
            wrap="word",
            corner_radius=8
        )
        notes_text.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Fetch and display actual release notes from GitHub
        try:
            release_notes = self._get_release_notes()
            if release_notes:
                notes_text.insert("1.0", release_notes)
            else:
                notes_text.insert("1.0", "• Bug fixes and performance improvements\n• Enhanced flip detection algorithm\n• New enchanting opportunities feature\n• Improved UI responsiveness\n• Better error handling")
        except Exception as e:
            notes_text.insert("1.0", "• Bug fixes and performance improvements\n• Enhanced flip detection algorithm\n• New enchanting opportunities feature\n• Improved UI responsiveness\n• Better error handling")
        notes_text.configure(state="disabled")
        
        # Button frame with enhanced styling
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        # Primary action button (Update Now)
        update_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Update Now",
            command=self._start_update,
            width=180,
            height=44,
            fg_color="#00d4ff",
            text_color="#181c24",
            corner_radius=22,
            font=("Segoe UI", 14, "bold"),
            hover_color="#00b0cc"
        )
        update_btn.pack(side="left", padx=(0, 12))
        
        # Secondary action buttons
        secondary_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        secondary_frame.pack(side="right")
        
        # Skip button
        skip_btn = ctk.CTkButton(
            secondary_frame,
            text="⏭️ Skip",
            command=self._skip_update,
            width=100,
            height=36,
            fg_color="#4a5568",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 12),
            hover_color="#2d3748"
        )
        skip_btn.pack(side="left", padx=(0, 8))
        
        # Remind later button
        remind_btn = ctk.CTkButton(
            secondary_frame,
            text="⏰ Later",
            command=self._remind_later,
            width=100,
            height=36,
            fg_color="#2d3748",
            text_color="#a0aec0",
            corner_radius=18,
            font=("Segoe UI", 12),
            hover_color="#1a202c"
        )
        remind_btn.pack(side="left")
        
        # Progress bar (hidden initially) with enhanced styling
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            progress_color="#00d4ff",
            fg_color="#2d3748",
            corner_radius=8
        )
        self.progress_bar.pack(fill="x", padx=24, pady=(0, 8))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()
        
        # Status label (hidden initially) with enhanced styling
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color="#00d4ff"
        )
        self.status_label.pack(pady=(0, 8))
        self.status_label.pack_forget()
    
    def _start_update(self):
        """Start the update process"""
        if not self.download_url:
            messagebox.showerror("Update Error", "Download URL not available")
            return
            
        # Show progress bar and status
        self.progress_bar.pack(fill="x", padx=30, pady=(0, 10))
        self.status_label.pack(pady=(0, 10))
        
        # Disable buttons during update
        for widget in self.update_window.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkButton):
                                grandchild.configure(state="disabled")
        
        # Start update in a separate thread
        update_thread = threading.Thread(target=self._download_and_install_update)
        update_thread.daemon = True
        update_thread.start()
    
    def _download_and_install_update(self):
        """Download and install the update"""
        try:
            # Update status
            self.status_label.configure(text="Downloading update...")
            self.progress_bar.set(0.1)
            
            # Download the update
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file size for progress calculation
            total_size = int(response.headers.get('content-length', 0))
            
            # Create temp directory
            temp_dir = Path("temp_update")
            temp_dir.mkdir(exist_ok=True)
            
            # Download file
            update_file = temp_dir / "rat_flipper_update.zip"
            downloaded_size = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = 0.1 + (downloaded_size / total_size) * 0.7
                            self.progress_bar.set(progress)
            
            # Extract update
            self.status_label.configure(text="Installing update...")
            self.progress_bar.set(0.8)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Create backup of current version
            backup_dir = Path("backup")
            backup_dir.mkdir(exist_ok=True)
            
            current_script = Path(__file__)
            if current_script.exists():
                shutil.copy2(current_script, backup_dir / f"rat_flipper_backup_{self.current_version}.py")
            
            # Replace current file with new version
            new_script = temp_dir / "Ratflipper.py"
            if new_script.exists():
                shutil.copy2(new_script, current_script)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Update completed! Restarting...")
            
            # Restart the application
            self.update_window.after(2000, self._restart_application)
            
        except Exception as e:
            self.status_label.configure(text=f"Update failed: {str(e)}")
            messagebox.showerror("Update Error", f"Failed to update: {str(e)}")
    
    def _restart_application(self):
        """Restart the application"""
        try:
            # Close current application
            self.update_window.destroy()
            
            # Restart the script
            python = sys.executable
            subprocess.Popen([python, __file__])
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Restart Error", f"Failed to restart: {str(e)}")
    
    def _skip_update(self):
        """Skip this update"""
        self.update_window.destroy()
        messagebox.showinfo("Update Skipped", "Update skipped. You can check for updates again later from the Settings menu.")
    
    def _remind_later(self):
        """Remind later (close dialog)"""
        self.update_window.destroy()
        messagebox.showinfo("Reminder Set", "You'll be reminded about this update next time you start the application.")

# --- Loading Animation Class ---

class LoadingAnimation:
    """Beautiful loading animation with fade effects"""
    def __init__(self, parent, on_complete=None):
        self.parent = parent
        self.on_complete = on_complete
        self.loading_window = None
        self.current_alpha = 0.0
        self.animation_step = 0
        self.animation_running = False
        
    def show_loading_screen(self):
        """Create and show the loading screen"""
        # Create loading window
        self.loading_window = tk.Toplevel(self.parent)
        self.loading_window.title("Loading...")
        self.loading_window.geometry("800x500")
        self.loading_window.configure(bg="#181c24")
        self.loading_window.attributes('-topmost', True)
        self.loading_window.overrideredirect(True)  # Remove window decorations
        
        # Center the window
        self.center_window(self.loading_window, 800, 500)
        
        # Create main frame with glassmorphism effect
        main_frame = ctk.CTkFrame(
            self.loading_window, 
            fg_color="#232946", 
            corner_radius=24, 
            border_width=2, 
            border_color="#00d4ff"
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create content frame
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # App icon with glow effect
        self.icon_label = ctk.CTkLabel(
            content_frame, 
            text="🦁", 
            font=("Segoe UI Emoji", 72),
            text_color="#00d4ff"
        )
        self.icon_label.pack(pady=(40, 20))
        
        # Start pulsing animation for icon
        self.pulse_icon()
        
        # Welcome text (will fade out)
        self.welcome_label = ctk.CTkLabel(
            content_frame,
            text="Welcome",
            font=("Segoe UI", 36, "bold"),
            text_color="#f8f8f2"
        )
        self.welcome_label.pack(pady=10)
        
        # App name text (will fade in)
        self.app_label = ctk.CTkLabel(
            content_frame,
            text="Rat Flipper Pro",
            font=("Segoe UI", 28, "bold"),
            text_color="#00d4ff"
        )
        self.app_label.pack(pady=10)
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            content_frame,
            text="Standalone Edition",
            font=("Segoe UI", 16),
            text_color="#888888"
        )
        self.subtitle_label.pack(pady=5)
        
        # Loading bar
        self.progress_frame = ctk.CTkFrame(content_frame, fg_color="transparent", height=8)
        self.progress_frame.pack(fill="x", padx=50, pady=(30, 10))
        self.progress_frame.pack_propagate(False)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Configure progress bar colors
        self.progress_bar.configure(
            progress_color="#00d4ff",
            fg_color="#232946",
            border_color="#00d4ff"
        )
        
        # Status text
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="Initializing...",
            font=("Segoe UI", 14),
            text_color="#00d4ff"
        )
        self.status_label.pack(pady=10)
        
        # Start background animation
        self.start_background_animation()
        
        # Start animation
        self.start_animation()
        
    def center_window(self, window, width, height):
        """Center the window on screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
    def start_background_animation(self):
        """Start subtle background color animation"""
        if not self.animation_running:
            return
            
        def animate_bg(phase=0):
            if not self.animation_running or not self.loading_window:
                return
                
            # Subtle color shift in the background
            intensity = 0.1 + 0.05 * math.sin(phase)
            
            # Shift the background color slightly
            r = int(35 + (5 * intensity))
            g = int(41 + (5 * intensity))
            b = int(70 + (10 * intensity))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            try:
                if self.loading_window:
                    self.loading_window.configure(bg=color)
            except:
                pass
                
            # Continue animation
            self.parent.after(200, lambda: animate_bg(phase + 0.1))
            
        animate_bg()
        
    def start_animation(self):
        """Start the loading animation sequence"""
        self.animation_running = True
        self.animation_step = 0
        self.current_alpha = 0.0
        self.animate_step()
        
    def animate_step(self):
        """Animate each step of the loading sequence"""
        if not self.animation_running:
            return
            
        step = self.animation_step
        
        if step == 0:
            # Step 0: Fade in welcome text
            self.fade_in_text(self.welcome_label, "Welcome", 0.05, self.next_step)
            
        elif step == 1:
            # Step 1: Hold welcome text
            self.status_label.configure(text="Loading components...")
            self.progress_bar.set(0.2)
            self.parent.after(1000, self.next_step)
            
        elif step == 2:
            # Step 2: Fade out welcome, fade in app name
            self.fade_out_text(self.welcome_label, 0.03, lambda: self.fade_in_text(self.app_label, "Rat Flipper Pro", 0.03, self.next_step))
            
        elif step == 3:
            # Step 3: Show subtitle
            self.status_label.configure(text="Connecting to servers...")
            self.progress_bar.set(0.4)
            self.parent.after(800, self.next_step)
            
        elif step == 4:
            # Step 4: Loading progress
            self.status_label.configure(text="Loading market data...")
            self.progress_bar.set(0.6)
            self.parent.after(600, self.next_step)
            
        elif step == 5:
            # Step 5: Final loading
            self.status_label.configure(text="Preparing interface...")
            self.progress_bar.set(0.8)
            self.parent.after(500, self.next_step)
            
        elif step == 6:
            # Step 6: Complete
            self.status_label.configure(text="Ready!")
            self.progress_bar.set(1.0)
            self.parent.after(300, self.finish_loading)
            
    def fade_in_text(self, label, text, speed, callback):
        """Fade in text with specified speed"""
        label.configure(text=text)
        self.current_alpha = 0.0
        
        def fade():
            if self.current_alpha < 1.0 and self.animation_running:
                self.current_alpha += speed
                # Create color with alpha
                color = self.interpolate_color("#000000", "#f8f8f2", self.current_alpha)
                label.configure(text_color=color)
                self.parent.after(20, fade)
            else:
                if callback:
                    callback()
                    
        fade()
        
    def fade_out_text(self, label, speed, callback):
        """Fade out text with specified speed"""
        self.current_alpha = 1.0
        
        def fade():
            if self.current_alpha > 0.0 and self.animation_running:
                self.current_alpha -= speed
                # Create color with alpha
                color = self.interpolate_color("#000000", "#f8f8f2", self.current_alpha)
                label.configure(text_color=color)
                self.parent.after(20, fade)
            else:
                if callback:
                    callback()
                    
        fade()
        
    def interpolate_color(self, color1, color2, factor):
        """Interpolate between two colors"""
        # Clamp factor to valid range [0, 1]
        factor = max(0.0, min(1.0, factor))
        
        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        # Interpolate
        r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * factor)
        g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * factor)
        b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * factor)
        
        # Clamp RGB values to valid range [0, 255]
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def next_step(self):
        """Move to next animation step"""
        self.animation_step += 1
        self.animate_step()
        
    def finish_loading(self):
        """Finish loading animation and close loading window"""
        self.animation_running = False
        if self.loading_window:
            # Fade out the entire loading window
            self.fade_out_window()
            
        # Call completion callback if provided
        if self.on_complete:
            self.parent.after(100, self.on_complete)
            
    def pulse_icon(self):
        """Create a pulsing effect for the icon"""
        if not self.animation_running or not self.icon_label:
            return
            
        def pulse(phase=0):
            if not self.animation_running or not self.icon_label:
                return
                
            # Create pulsing effect with sine wave
            intensity = 0.3 + 0.7 * abs(math.sin(phase))
            
            # Interpolate between dark and bright blue
            r = int(0 + (0 * intensity))
            g = int(212 + (43 * intensity))
            b = int(255 + (0 * intensity))
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.icon_label.configure(text_color=color)
            
            # Continue pulsing
            self.parent.after(100, lambda: pulse(phase + 0.2))
            
        pulse()
        
    def fade_out_window(self):
        """Fade out the loading window"""
        if not self.loading_window:
            return
            
        def fade():
            if self.loading_window:
                try:
                    current_alpha = self.loading_window.attributes('-alpha')
                    if current_alpha > 0.0:
                        self.loading_window.attributes('-alpha', current_alpha - 0.1)
                        self.parent.after(30, fade)
                    else:
                        self.loading_window.destroy()
                        self.loading_window = None
                except:
                    # Window might have been destroyed
                    pass
                    
        fade()

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('item_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# NATS Server Configuration
NATS_SERVERS = {
    'Europe': 'nats://public:thenewalbiondata@nats.albion-online-data.com:34222',
    'Americas': 'nats://public:thenewalbiondata@nats.albion-online-data.com:4222',
    'Asia': 'nats://public:thenewalbiondata@nats.albion-online-data.com:24222'
}

# Theme Configuration
THEMES = {
    'dark': {
        'bg_color': '#1a1a1a',
        'fg_color': '#2b2b2b',
        'text_color': '#ffffff',
        'selected_color': '#144870',
        'button_color': '#1f538d',
        'button_hover_color': '#14375e',
        'entry_color': '#343638',
        'scrollbar_color': '#565b5e'
    },
    'light': {
        'bg_color': '#f0f0f0',
        'fg_color': '#ffffff',
        'text_color': '#000000',
        'selected_color': '#c7ddf2',
        'button_color': '#3b8ed0',
        'button_hover_color': '#36719f',
        'entry_color': '#ffffff',
        'scrollbar_color': '#c7c7c7'
    }
}

# Modern font
MODERN_FONT = ("Segoe UI", 14)
HEADER_FONT = ("Segoe UI", 26, "bold")
TABLE_FONT = ("Segoe UI", 11)
TABLE_HEADER_FONT = ("Segoe UI", 11, "bold")

# Accent color and glassmorphism settings
ACCENT_COLOR = "#00d4ff"
GLASS_ALPHA = 180  # 0-255, for glass effect
GLASS_BG = (35, 41, 70, GLASS_ALPHA)  # RGBA for glass panels

# Theme palettes
DARK_PALETTE = {
    'bg': '#181c24',
    'panel': '#232946',
    'panel2': '#23272e',
    'text': '#f8f8f2',
    'header': '#232946',
    'accent': ACCENT_COLOR,
    'button_fg': ACCENT_COLOR,
    'button_text': '#181c24',
    'label': '#f8f8f2',
    'tree_bg': '#23272e',
    'tree_even': '#2b2f36',
    'tree_header': '#181c24',
    'tree_header_text': ACCENT_COLOR
}
LIGHT_PALETTE = {
    'bg': '#faf4e8',  # warm soft white
    'panel': '#faf4e8',  # warm soft white
    'panel2': '#e0e4ea',  # light blue-gray
    'text': '#232946',
    'header': '#e0e4ea',
    'accent': ACCENT_COLOR,
    'button_fg': ACCENT_COLOR,
    'button_text': '#232946',
    'label': '#232946',
    'tree_bg': '#faf4e8',  # warm soft white
    'tree_even': '#e0e4ea',
    'tree_header': '#e0e4ea',
    'tree_header_text': ACCENT_COLOR
}

QUALITY_LEVEL_NAMES = {
    1: "Normal",
    2: "Good",
    3: "Outstanding",
    4: "Excellent",
    5: "Masterpiece"
}

# --- Data Classes and Utilities ---

@dataclass
class ItemData:
    """Data class for item information (from items.txt)"""
    id: str
    name: str
    status: str
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class FlipOpportunity:
    """Data class for flip opportunities"""
    item_name: str
    tier: int
    enchantment: int
    city: str
    city_price: int
    bm_price: int
    profit: int
    bm_age: int
    city_age: int
    risk_score: float
    volume: int = 0
    quantity: int = 1
    profit_margin: float = 0.0
    last_update: Optional[datetime] = None
    selected: bool = False
    flip_id: str = ""
    full_volume: int = 0
    city_quality: int = 1
    bm_quality: int = 1

@dataclass
class MarketOrder:
    """Data class for market orders from NATS"""
    item_id: str
    location_id: int
    quality_level: int
    enchantment_level: int
    unit_price_silver: int
    amount: int
    auction_type: str  # "offer" or "request"
    expires: str
    order_id: str
    timestamp: datetime

@dataclass
class MarketHistory:
    """Data class for market history from NATS"""
    item_id: str
    location_id: int
    quality_level: int
    item_amount: int
    silver_amount: int
    timestamp: datetime

class ItemManager:
    """Manages item loading with validation and enchantment support"""
    def __init__(self):
        self.items = []
        self.item_id_to_name = {}
    def load_items_from_file(self, filename: str) -> List[str]:
        """Load and validate items from file."""
        try:
            if not os.path.exists(filename):
                logger.error(f"File {filename} not found")
                return []
            with open(filename, 'r', encoding='utf-8-sig') as f:
                items = []
                self.item_id_to_name = {}
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    item_id = ''
                    display_name = ''

                    if ':' in line:
                        # Handle formats with a colon, e.g., "ID:Name" or "Num:ID:Name"
                        parts = [p.strip() for p in line.split(':')]
                        if len(parts) >= 3 and parts[0].isdigit():
                            # Format: number: ITEM_ID : Name
                            item_id = parts[1].lower()
                            display_name = parts[-1]
                        elif len(parts) >= 2:
                            # Format: ITEM_ID : Name
                            item_id = parts[0].lower()
                            display_name = parts[-1]
                    else:
                        # Handle format with just the item ID
                        item_id = line.lower()
                        display_name = line  # Use ID as a fallback name

                    if item_id and self._is_valid_item_name(item_id):
                        items.append(item_id)
                        self.item_id_to_name[item_id] = display_name
                    elif item_id: # Only log if we found an ID but it was invalid
                        logger.warning(f"Skipping invalid item on line {line_num}: {line}")

            logger.info(f"Loaded {len(items)} valid items from {filename}")
            return items
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            return []
    
    def _is_valid_item_name(self, item_name: str) -> bool:
        """Basic validation for item names"""
        if len(item_name) < 3:
            return False
        if any(char in item_name for char in ['<', '>']):
            return False
        return True
    
    def generate_enchanted_items(self, base_items: List[str], max_enchant: int = 3) -> List[str]:
        """Generate enchanted versions with .1, .2, .3, .4 format"""
        all_items = []
        for item in base_items:
            all_items.append(item)
            if not any(item.endswith(f'.{i}') or item.endswith(f'@{i}') for i in range(1, 5)):
                for enchant in range(1, max_enchant + 1):
                    all_items.append(f"{item}.{enchant}")
        return all_items

    def get_display_name(self, item_id: str) -> str:
        """Get the display name for an item, using the new format from items.txt"""
        return self.item_id_to_name.get(item_id.lower(), item_id)

# --- File Watcher and NATS Client ---

class FileWatcher(FileSystemEventHandler):
    """File system event handler for monitoring items.txt changes"""
    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback
        self.last_modified = 0
    def on_modified(self, event):
        if event.is_directory:
            return
        current_time = time.time()
        if current_time - self.last_modified < 0.5:
            return
        self.last_modified = current_time
        # Ensure src_path is a string for endswith
        src_path = str(event.src_path)
        if src_path.endswith('items.txt'):
            logger.info(f"File modified: {src_path}")
            self.callback()

class NATSClient:
    """Handles NATS connection and message processing"""
    def __init__(self):
        self.nc = None
        self.connected = False
        self.connection_callbacks = []
        self.message_callbacks = []
        self.status_callback = None
        self.topics = [
            'marketorders.ingest',
            'marketorders.deduped',
            'markethistories.ingest',
            'markethistories.deduped',
            'goldprices.ingest',
            'goldprices.deduped'
        ]
        self.message_buffer = {topic: deque(maxlen=1000) for topic in self.topics}

    def add_connection_callback(self, callback: Callable):
        self.connection_callbacks.append(callback)

    def add_message_callback(self, callback: Callable):
        self.message_callbacks.append(callback)

    def set_status_callback(self, callback: Callable):
        self.status_callback = callback

    async def discover_best_server(self):
        """Return a sorted list of (url, latency) for all servers that responded."""
        logger.info("Discovering best NATS server by measuring connection latency...")
        tasks = []
        for region, url in NATS_SERVERS.items():
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port
            if host and port:
                tasks.append(self._check_latency(region, host, port, url))
        results = await asyncio.gather(*tasks)
        server_latencies = []
        for region, latency, url in results:
            if latency is not None:
                logger.info(f"Latency to {region} ({url}): {latency:.2f} ms")
                server_latencies.append((url, latency, region))
            else:
                logger.warning(f"Failed to connect to {region} server.")
        server_latencies.sort(key=lambda x: x[1])  # sort by latency
        return server_latencies

    async def _check_latency(self, region: str, host: str, port: int, url: str):
        """Helper to check latency to one server."""
        start = time.time()
        try:
            # Timeout connection attempt after 2 seconds
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=2.0
            )
            latency = (time.time() - start) * 1000  # Convert to ms
            writer.close()
            await writer.wait_closed()
            return region, latency, url
        except Exception:
            return region, None, url

    async def connect(self, server_url: Optional[str] = None):
        """Connect to NATS server and subscribe to topics. If server_url is None, try all servers by lowest latency."""
        if self.nc and self.nc.is_connected:
            return
        try:
            if not server_url:
                server_latencies = await self.discover_best_server()
                for url, latency, region in server_latencies:
                    try:
                        logger.info(f"Attempting to connect to {region} server: {url} (latency: {latency:.2f} ms)")
                        self.nc = await nats.connect(
                            url,
                            error_cb=self._on_error,
                            disconnected_cb=self._on_disconnected,
                            reconnected_cb=self._on_reconnected,
                            closed_cb=self._on_closed,
                            max_reconnect_attempts=-1,
                            reconnect_time_wait=5
                        )
                        self.connected = True
                        logger.info(f"Connected to NATS server: {url} (latency: {latency:.2f} ms)")
                        for topic in self.topics:
                            await self.subscribe(topic)
                        for callback in self.connection_callbacks:
                            callback(True, f"Connected to {url} (latency: {latency:.2f} ms)")
                        return
                    except Exception as e:
                        logger.warning(f"Failed to connect to {region} server {url}: {e}")
                        self.nc = None
                        self.connected = False
                # If all fail
                error_msg = "Failed to connect to any NATS server in Auto mode."
                logger.error(error_msg)
                for callback in self.connection_callbacks:
                    callback(False, error_msg)
                return
            else:
                # User selected a specific server
                logger.info(f"Attempting to connect to specified server: {server_url}")
                self.nc = await nats.connect(
                    server_url,
                    error_cb=self._on_error,
                    disconnected_cb=self._on_disconnected,
                    reconnected_cb=self._on_reconnected,
                    closed_cb=self._on_closed,
                    max_reconnect_attempts=-1,
                    reconnect_time_wait=5
                )
                self.connected = True
                logger.info(f"Connected to NATS server: {server_url}")
                for topic in self.topics:
                    await self.subscribe(topic)
                for callback in self.connection_callbacks:
                    callback(True, f"Connected to {server_url}")
        except Exception as e:
            self.connected = False
            error_msg = f"Failed to connect to NATS: {e}"
            logger.error(error_msg)
            for callback in self.connection_callbacks:
                callback(False, error_msg)

    async def subscribe(self, topic: str):
        """Subscribe to a NATS topic"""
        if not self.nc:
            logger.error("Cannot subscribe: Not connected to NATS")
            return
        try:
            await self.nc.subscribe(topic, cb=self._message_handler)
            logger.info(f"Subscribed to topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")

    async def _message_handler(self, msg):
        """Handle incoming NATS messages"""
        try:
            # Parse message data
            data = json.loads(msg.data.decode())
            topic = msg.subject
            
            # Store in appropriate buffer
            if topic in self.message_buffer:
                self.message_buffer[topic].append(data)
            
            # Notify callbacks
            for callback in self.message_callbacks:
                callback({
                    'topic': topic,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _on_disconnected(self):
        """Handle NATS disconnection"""
        self.connected = False
        logger.warning("Disconnected from NATS")
        for callback in self.connection_callbacks:
            callback(False, "Disconnected from NATS")

    async def _on_reconnected(self):
        """Handle NATS reconnection"""
        self.connected = True
        logger.info("Reconnected to NATS")
        for callback in self.connection_callbacks:
            callback(True, "Reconnected to NATS")

    async def _on_error(self, e):
        """Handle NATS errors"""
        logger.error(f"NATS error: {e}")

    async def _on_closed(self):
        """Handle NATS connection closure"""
        self.connected = False
        logger.info("NATS connection closed")

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.nc:
            try:
                await self.nc.drain()
                await self.nc.close()
            except Exception as e:
                logger.error(f"Error disconnecting from NATS: {e}")
            finally:
                self.nc = None
                self.connected = False

# --- Item Parser and Flip Detection ---

class ItemParser:
    """Parser for items.txt file with flexible format support"""
    @staticmethod
    def parse_line(line: str) -> Optional[ItemData]:
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        try:
            # Format 1: "id: 101, name: Item A, status: active"
            if ':' in line and ',' in line:
                parts = {}
                for part in line.split(','):
                    if ':' in part:
                        key, value = part.split(':', 1)
                        parts[key.strip().lower()] = value.strip()
                return ItemData(
                    id=parts.get('id', ''),
                    name=parts.get('name', ''),
                    status=parts.get('status', 'unknown')
                )
            # Format 2: JSON-like
            elif line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                return ItemData(
                    id=str(data.get('id', '')),
                    name=data.get('name', ''),
                    status=data.get('status', 'unknown')
                )
            # Format 3: Tab or space separated
            elif '\t' in line or '  ' in line:
                parts = re.split(r'\s{2,}|\t', line)
                if len(parts) >= 3:
                    return ItemData(
                        id=parts[0],
                        name=parts[1],
                        status=parts[2]
                    )
            # Format 4: Simple comma separated
            elif ',' in line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    return ItemData(
                        id=parts[0],
                        name=parts[1],
                        status=parts[2]
                    )
        except Exception as e:
            logger.error(f"Error parsing line '{line}': {e}")
        return None
    @staticmethod
    async def parse_file(file_path: str) -> List[ItemData]:
        items = []
        try:
            if not Path(file_path).exists():
                logger.warning(f"File not found: {file_path}")
                return items
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    item = ItemParser.parse_line(line)
                    if item:
                        items.append(item)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        return items

class RealTimeFlipDetector:
    """Real-time flip opportunity detection using NATS data (BM quality only, city prices per quality)"""
    def __init__(self):
        self.item_filters = set()
        self.city_filters = set()
        self.opportunity_callbacks = []
        # Store city sell prices per item, per city, per quality
        self.city_price_data = defaultdict(lambda: defaultdict(dict))  # item_id -> city_name -> quality -> price_info
        self.bm_price_data = defaultdict(dict)    # (item_id, quality_level) -> 'Black Market' -> price_info
        self.flip_debug_log = deque(maxlen=200)
        self.filter_debug_log = deque(maxlen=200)
    def set_filters(self, items: List[str], cities: List[str]):
        self.item_filters = set(i.lower().strip() for i in items)
        self.city_filters = set(cities)
        self.filter_debug_log.appendleft(f"Item filter set: {sorted(self.item_filters)}")
        self.filter_debug_log.appendleft(f"City filter set: {sorted(self.city_filters)}")
    def register_opportunity_callback(self, callback: Callable):
        self.opportunity_callbacks.append(callback)
    def process_market_order(self, order: MarketOrder):
        self.flip_debug_log.appendleft(f"Processing order: {order}")
        self.filter_debug_log.appendleft(f"Checking item: '{order.item_id}' (normalized: '{order.item_id.lower().strip()}') against filter")
        if self.item_filters and order.item_id.lower().strip() not in self.item_filters:
            self.flip_debug_log.appendleft(f"Item {order.item_id} not in filters, skipping.")
            self.filter_debug_log.appendleft(f"Item {order.item_id} not in filters, skipping.")
            return
        location_name = self._location_name(order.location_id)
        if not location_name:
            self.flip_debug_log.appendleft(f"Unknown location id {order.location_id}, skipping.")
            return
        if order.auction_type == "offer":  # City sell order (track by quality)
            if location_name != 'Black Market':
                q = order.quality_level
                if q not in self.city_price_data[order.item_id][location_name]:
                    self.city_price_data[order.item_id][location_name][q] = {
                        'sell_price': None,
                        'sell_amount': 0,
                        'last_update': None
                    }
                city_data = self.city_price_data[order.item_id][location_name][q]
                if city_data['sell_price'] is None or order.unit_price_silver < city_data['sell_price']:
                    city_data['sell_price'] = order.unit_price_silver
                    city_data['sell_amount'] = order.amount
                city_data['last_update'] = datetime.now(timezone.utc)
                # Log city data save
                self.flip_debug_log.appendleft(f"Saved city data: {order.item_id} in {location_name} Q{q} - Price: {order.unit_price_silver:,}, Amount: {order.amount}")
                # Check flips for all BM qualities for this item
                for bm_q in range(1, 6):
                    self._check_flip_opportunities(order.item_id, bm_q, location_name)
        elif order.auction_type == "request" and location_name == 'Black Market':
            item_key = (order.item_id, order.quality_level)
            if 'Black Market' not in self.bm_price_data[item_key]:
                self.bm_price_data[item_key]['Black Market'] = {
                    'buy_price': None,
                    'buy_amount': 0,
                    'last_update': None
                }
            bm_data = self.bm_price_data[item_key]['Black Market']
            if bm_data['buy_price'] is None or order.unit_price_silver > bm_data['buy_price']:
                bm_data['buy_price'] = order.unit_price_silver
                bm_data['buy_amount'] = order.amount
            bm_data['last_update'] = datetime.now(timezone.utc)
            # Log black market data save
            self.flip_debug_log.appendleft(f"Saved BM data: {order.item_id} Q{order.quality_level} - Buy Price: {order.unit_price_silver:,}, Amount: {order.amount}")
            # Check flips for all cities for this item/quality
            for city in self.city_filters:
                self._check_flip_opportunities(order.item_id, order.quality_level, city)
    def _check_flip_opportunities(self, item_id: str, bm_quality: int, city_name: str):
        self.flip_debug_log.appendleft(f"Checking flips for {item_id} BM Q{bm_quality} in {city_name}")
        item_key = (item_id, bm_quality)
        bm_data = self.bm_price_data.get(item_key, {}).get('Black Market')
        city_qualities = self.city_price_data.get(item_id, {}).get(city_name, {})
        if not bm_data or not bm_data.get('buy_price'):
            self.flip_debug_log.appendleft(f"No Black Market buy price for {item_id} Q{bm_quality}")
            return
        # Find the lowest city price for quality >= bm_quality
        eligible_qualities = [q for q in city_qualities if q >= bm_quality]
        if not eligible_qualities:
            self.flip_debug_log.appendleft(f"No eligible city qualities for {item_id} in {city_name} for BM Q{bm_quality}")
            return
        min_price = None
        min_q = None
        min_data = None
        for q in eligible_qualities:
            data = city_qualities[q]
            if data.get('sell_price') is not None:
                if min_price is None or data['sell_price'] < min_price:
                    min_price = data['sell_price']
                    min_q = q
                    min_data = data
        if min_price is None:
            self.flip_debug_log.appendleft(f"No city sell price for {item_id} in {city_name} for BM Q{bm_quality}")
            return
        bm_buy_price = bm_data['buy_price']
        bm_amount = bm_data.get('buy_amount', 0)
        city_sell_price = min_price
        city_amount = min_data.get('sell_amount', 0) if min_data else 0
        
        # Calculate age data
        bm_age = 0
        city_age = 0
        current_time = datetime.now(timezone.utc)
        
        if bm_data.get('last_update'):
            bm_age = int((current_time - bm_data['last_update']).total_seconds() / 60)  # Age in minutes
        
        if min_data and min_data.get('last_update'):
            city_age = int((current_time - min_data['last_update']).total_seconds() / 60)  # Age in minutes
        
        profit = bm_buy_price - city_sell_price
        available_quantity = min(city_amount, bm_amount) if bm_amount > 0 else city_amount
        tier, _, enchantment = parse_item_id(item_id)
        opportunity = FlipOpportunity(
            item_name=item_id,
            tier=tier if tier is not None else 0,
            enchantment=enchantment if enchantment is not None else 0,
            city=city_name,
            city_price=city_sell_price,
            bm_price=bm_buy_price,
            profit=profit,
            bm_age=bm_age,
            city_age=city_age,
            risk_score=0,
            volume=available_quantity,
            quantity=min(available_quantity, 10),
            flip_id=f"{item_id}_{bm_quality}_{city_name}_{city_sell_price}_{bm_buy_price}",
            last_update=current_time,
            full_volume=available_quantity,
            city_quality=min_q if min_q is not None else 0,
            bm_quality=bm_quality
        )
        self.flip_debug_log.appendleft(f"Opportunity found: {opportunity}")
        for callback in self.opportunity_callbacks:
            try:
                callback(opportunity)
            except Exception as e:
                logger.error(f"Error in opportunity callback: {e}")
    def scan_for_all_flips(self, scan_log: deque) -> List[FlipOpportunity]:
        """Iterates through all stored price data to find every possible flip, logging its progress."""
        opportunities = []
        scan_log.appendleft(f"--- Starting Full Scan at {datetime.now(timezone.utc).strftime('%H:%M:%S')} ---")
        for item_id, city_dict in self.city_price_data.items():
            if self.item_filters and item_id.lower().strip() not in self.item_filters:
                continue
            for city_name, qualities in city_dict.items():
                if city_name not in self.city_filters:
                    continue
                for bm_quality in range(1, 6):
                    # Find the lowest city price for quality >= bm_quality
                    eligible_qualities = [q for q in qualities if q >= bm_quality]
                    min_price = None
                    min_q = None
                    min_data = None
                    for q in eligible_qualities:
                        data = qualities[q]
                        if data.get('sell_price') is not None:
                            if min_price is None or data['sell_price'] < min_price:
                                min_price = data['sell_price']
                                min_q = q
                                min_data = data
                    if min_price is None:
                        continue
                    item_key = (item_id, bm_quality)
                    bm_data = self.bm_price_data.get(item_key, {}).get('Black Market')
                    if not bm_data or not bm_data.get('buy_price'):
                        continue
                    bm_buy_price = bm_data['buy_price']
                    bm_amount = bm_data.get('buy_amount', 0)
                    city_sell_price = min_price
                    city_amount = min_data.get('sell_amount', 0) if min_data else 0
                    profit = bm_buy_price - city_sell_price
                    available_quantity = min(city_amount, bm_amount) if bm_amount > 0 else city_amount
                    tier, _, enchantment = parse_item_id(item_id)
                    opportunity = FlipOpportunity(
                        item_name=item_id,
                        tier=tier if tier is not None else 0,
                        enchantment=enchantment if enchantment is not None else 0,
                        city=city_name,
                        city_price=city_sell_price,
                        bm_price=bm_buy_price,
                        profit=profit,
                        bm_age=0,
                        city_age=0,
                        risk_score=0,
                        volume=available_quantity,
                        quantity=min(available_quantity, 10),
                        flip_id=f"{item_id}_{bm_quality}_{city_name}_{city_sell_price}_{bm_buy_price}",
                        last_update=datetime.now(timezone.utc),
                        full_volume=available_quantity,
                        city_quality=min_q if min_q is not None else 0,
                        bm_quality=bm_quality
                    )
                    opportunities.append(opportunity)
        scan_log.appendleft(f"--- Scan Complete: Found {len(opportunities)} flips from {len(self.city_price_data)} tracked items. ---")
        return opportunities
    def _location_name(self, location_id: int) -> Optional[str]:
        location_map = {
            5003: 'Brecilien',
            2004: 'Bridgewatch',
            1002: 'Lymhurst',
            4002: 'Fort Sterling',
            7: 'Thetford',
            3008: 'Martlock',
            3005: 'Caerleon',
            3003: 'Black Market'
        }
        return location_map.get(location_id)

# --- Animated Button and Main GUI Skeleton ---

class AnimatedButton(ctk.CTkButton):
    """Custom button with click and hover animation (color, scale, and ripple)"""
    def __init__(self, *args, **kwargs):
        # Ensure fg_color and text_color are always set and high-contrast
        kwargs.setdefault('fg_color', ACCENT_COLOR)
        kwargs.setdefault('text_color', '#f8f8f2')
        super().__init__(*args, **kwargs)
        self.original_width = kwargs.get('width', 140)
        self.original_height = kwargs.get('height', 28)
        self._hovered = False
        self._animating = False
        self._scale = 1.0
        self._fg_normal = kwargs['fg_color']
        self._fg_hover = self._darker(self._fg_normal, 0.85)
        self._fg_press = self._darker(self._fg_normal, 0.7)
        self._pressed = False  # Ensure _pressed is always defined
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        # Ripple effect canvas
        self._ripple_canvas = None
    def _on_click(self, event):
        self._animate_press()
        self._ripple(event)
        # Play custom pop sound (Windows only)
        if platform.system() == "Windows":
            try:
                # winsound.PlaySound(POP_WAV, winsound.SND_FILENAME | winsound.SND_ASYNC)
                # POP_WAV aint workin
                pass
            except Exception:
                pass
        # For ...
    def _on_enter(self, event=None):
        self._hovered = True
        self._animate_hover(True)
    def _on_leave(self, event=None):
        self._hovered = False
        self._animate_hover(False)
    def _animate_hover(self, entering, step=0):
        # Speed up animation.
        steps = 6
        delay = 10
        if entering:
            color1 = self._fg_normal
            color2 = self._fg_hover
        else:
            color1 = self._fg_hover
            color2 = self._fg_normal
        def animate(i=0):
            t = i / steps
            color = self._interpolate_color(color1, color2, t)
            self.configure(fg_color=color)
            if i < steps:
                self.after(delay, lambda: animate(i+1))
        animate()
    def _animate_press(self, step=0):
        # Speed up press animation
        steps = 4
        delay = 8
        color1 = self._fg_hover
        color2 = self._fg_press
        def animate_down(i=0):
            t = i / steps
            color = self._interpolate_color(color1, color2, t)
            self.configure(fg_color=color)
            if i < steps:
                self.after(delay, lambda: animate_down(i+1))
        def animate_up(i=0):
            t = i / steps
            color = self._interpolate_color(color2, color1, t)
            self.configure(fg_color=color)
            if i < steps:
                self.after(delay, lambda: animate_up(i+1))
        if self._pressed:
            animate_down()
        else:
            animate_up()
    def _darker(self, color, factor):
        # Accepts hex or tuple
        if isinstance(color, str) and color.startswith('#'):
            color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        # Ensure all elements are ints
        color = tuple(int(x) for x in color)
        r, g, b = [x/255 for x in color]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        l = max(0, l * factor)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
    def _interpolate_color(self, c1, c2, t):
        # Clamp t to valid range [0, 1]
        t = max(0.0, min(1.0, t))
        
        def hex_to_rgb(h):
            if isinstance(h, str) and h.startswith('#'):
                return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
            return tuple(int(x) for x in h)
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        # Clamp RGB values to valid range [0, 255]
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        return '#%02x%02x%02x' % (r, g, b)
    def _ripple(self, event):
        if self._ripple_canvas:
            self._ripple_canvas.destroy()
        w = self.winfo_width()
        h = self.winfo_height()
        self._ripple_canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0, bg='white', bd=0)
        self._ripple_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        x, y = event.x, event.y
        max_radius = max(w, h)
        color = self._fg_press if (hasattr(self, '_fg_press') and isinstance(self._fg_press, str) and self._fg_press.startswith('#')) else '#ffffff'
        def animate_ripple(r=0):
            if self._ripple_canvas is not None:
                self._ripple_canvas.delete("ripple")
                self._ripple_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="", tags="ripple")
                if r < max_radius:
                    self.after(8, lambda: animate_ripple(r + 15))
                else:
                    if self._ripple_canvas is not None:
                        self._ripple_canvas.destroy()
                        self._ripple_canvas = None
        animate_ripple()

def find_items_txt():
    # Search in common user directories
    user_dirs = [
        os.path.join(os.path.expanduser('~'), 'Downloads'),
        os.path.join(os.path.expanduser('~'), 'Desktop'),
        os.path.join(os.path.expanduser('~'), 'Documents'),
        os.getcwd(),
    ]
    
    # First check the common directories
    for folder in user_dirs:
        pattern = os.path.join(folder, 'items.txt')
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    # If not found in common directories, search recursively in current directory and subdirectories
    current_dir = os.getcwd()
    for root, dirs, files in os.walk(current_dir):
        if 'items.txt' in files:
            return os.path.join(root, 'items.txt')
    
    # Also search in parent directories (up to 3 levels up)
    parent_dir = os.path.dirname(current_dir)
    for level in range(3):
        if parent_dir and os.path.exists(parent_dir):
            for root, dirs, files in os.walk(parent_dir):
                if 'items.txt' in files:
                    return os.path.join(root, 'items.txt')
        parent_dir = os.path.dirname(parent_dir)
    
    return None

# --- Utility for bracketed item display ---
ITEM_TIER_NAMES = {
    4: "Adept's",
    5: "Expert's",
    6: "Master's",
    7: "Grandmaster's",
    8: "Elder's"
}

def parse_item_id(item_id: str):
    # Example: T5_2H_SHAPESHIFTER_AVALON@4
    match = re.match(r'T(\d+)_([A-Z0-9_]+)(?:@([1-4]))?', item_id)
    if not match:
        return None, None, None
    tier = int(match.group(1))
    base = f"T{tier}_" + match.group(2)
    enchant = int(match.group(3)) if match.group(3) else 0
    return tier, base, enchant

def bracketed_item_name(item_id: str, items_data: list):
    tier, base, enchant = parse_item_id(item_id)
    if tier is None:
        return item_id  # fallback
    # Find base name from items_data
    base_name = None
    for item in items_data:
        if item.id.startswith(base):
            base_name = item.name
            break
    if not base_name:
        base_name = base
    tier_name = ITEM_TIER_NAMES.get(tier, f"T{tier}")
    enchant_str = f"{tier}.{enchant}" if enchant else f"{tier}.0"
    # Prefer: (Expert's Lightcaller 5.4)
    return f"({tier_name} {base_name} {enchant_str})"

CONFIG_FILE = "rat_flipper_config.json"

class RatFlipperGUI:
    """Main GUI application class (skeleton)"""
    def __init__(self):
        print("🚀 Starting Rat Flipper Pro initialization...")
        
        # STANDALONE MODE: No license or webhook checks needed
        print("🎭 STANDALONE MODE - No license or webhook checks required")
        
        # Initialize the app directly
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the main application after license check"""
        print("🔄 Initializing main application...")
        
        # License manager removed - standalone version
        
        self.completed_flips_file = "completed_flips.json"
        self.completed_flips_history = []  # List of dicts: {item, city, profit, time}
        self.load_completed_flips() # Load persistent history

        import customtkinter
        print('customtkinter version:', customtkinter.__version__)
        # Initialize customtkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        # Create main window
        print("🪟 Creating main window...")
        self.root = ctk.CTk()
        self.root.title("Rat Flipper Pro - Standalone Edition")
        self.root.geometry("1800x1000")
        self.root.minsize(1500, 800)
        
        # Show loading animation
        print("🎬 Starting loading animation...")
        
        def on_loading_complete():
            self.root.deiconify()  # Make sure window is visible
            self.root.lift()  # Bring to front
            self.root.focus_force()  # Force focus
            print("🪟 Main window should now be visible!")
            
            # Check for updates on startup (if enabled)
            if hasattr(self, 'auto_check_updates') and self.auto_check_updates.get():
                # Delay the update check to allow the app to fully load
                self.root.after(5000, self.check_for_updates_silent)
            
            # Start the mainloop to run the GUI
            print("🔄 Starting mainloop...")
            self.root.mainloop()
            print("✅ Mainloop finished")
        
        self.loading_animation = LoadingAnimation(self.root, on_loading_complete)
        self.loading_animation.show_loading_screen()
        
        # Hide main window during loading
        self.root.withdraw()
        # Initialize enchanting variables after root exists
        self.enchanting_enabled = tk.BooleanVar(value=False)
        self.enchanting_source_city = tk.StringVar(value="All Cities")
        print("✅ Main window created")
        
        self.MAX_OPPORTUNITIES = 300
        # State and managers (to be filled in next chunks)
        self.current_theme = 'dark'  # Always use dark theme
        self.current_font_size = 12
        self.items_data = []
        self.flip_opportunities = []
        self.completed_flips = set([f['flip_id'] for f in self.completed_flips_history if 'flip_id' in f]) # Re-populate from loaded history
        self.nats_messages = []
        self.selected_nats_region = tk.StringVar(value="Auto")
        self.nats_data_buffer = deque(maxlen=100)  # Store last 100 NATS messages
        self.status_var = tk.StringVar(value="Ready.")
        self.premium_var = tk.BooleanVar(value=True)
        self.min_profit_var = tk.StringVar(value="100")
        self.bg_image = None
        self.bg_image_tk = None
        self.bg_url = None
        self.bg_label = None
        self.sort_column = "Total Profit"
        self.sort_reverse = True
        self.filter_city_var = tk.StringVar(value="All")
        self.filter_quality_var = tk.StringVar(value="All")
        self.filter_tier_var = tk.StringVar(value="All")
        self.opportunity_batch = deque()
        self._update_scheduled = False
        self._update_job_id = None
        self.scan_log = deque(maxlen=1000)
        # Add a separate debug log for opportunity batch that doesn't get cleared
        self.opportunity_batch_debug_log = deque(maxlen=500)
        self.opportunity_batch_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring for new opportunities...")
        # Enchanting state/config
        self.enchanting_source_city = None
        self.enchanting_debug_log = deque(maxlen=500)
        self.enchanting_raw_debug_log = deque(maxlen=500)
        self.enchanting_prices = {}
        self.enchanting_opportunities = []
        self.enchanting_enabled = None  # Will be initialized after root exists
        # Performance optimization: disable debug logging by default
        self.debug_enabled = False
        self.debug_window_open = False
        
        # Notification settings
        self.notifications_enabled = tk.BooleanVar(value=True)
        
        # Auto-updater initialization
        self.current_version = "1.3.0"  # Current version matching your latest GitHub release
        self.auto_updater = AutoUpdater(self.current_version)
        self.notification_min_profit = tk.StringVar(value="200000")
        self.notification_cooldown_var = tk.StringVar(value="10")
        self.last_notification_time = 0  # Track last notification time
        self.active_notification = None  # Track active notification window
        self.load_config()
        
        # Auto-load enchanting prices
        self.load_enchanting_prices()
        # --- Automatic items.txt scan ---
        print("📁 Looking for items.txt...")
        items_txt_path = find_items_txt()
        if not items_txt_path:
            print("❌ items.txt not found!")
            messagebox.showerror("File Error", "items.txt not found in Downloads, Desktop, Documents, or current directory. Please add items.txt and restart.")
            self.root.destroy()
            return
        print(f"✅ Found items.txt at: {items_txt_path}")
        self.file_path = items_txt_path
        self.nats_client = NATSClient()
        self.file_observer = None
        self.event_loop = None
        self.loop_thread = None
        self.item_manager = ItemManager()
        self.flip_detector = RealTimeFlipDetector()
        self.flip_detector.register_opportunity_callback(self._on_new_opportunity)
        # Set initial filters
        self.reload_item_filters()
        self._themed_widgets = []  # Store all panels/frames/widgets to update on theme/bg change
        self.current_font_color = "#f8f8f2"  # Default font color
        self._refreshing_ui = False  # Flag to prevent recursive calls
        # Setup UI (to be filled in next chunks)
        print("🎨 Creating UI...")
        self.create_ui()
        print("✅ UI created")
        # Setup file watcher and NATS client
        self.setup_file_watcher()
        self.setup_nats_client()
        # Start async event loop
        self.start_event_loop()
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # In __init__, bind resize event
        self.root.bind('<Configure>', self.on_resize)
        print('✅ Main window created and UI initialized')
        self.schedule_auto_scan_and_refresh()
        # Start automatic enchanting scan
        self.schedule_auto_enchanting_scan()
        print("🚀 Rat Flipper Pro initialization complete!")
        
        # Loading animation will handle showing the main window when complete

    def create_ui(self):
        # Configure grid for 2-column layout: sidebar (left) and main content (right)
        self.root.grid_columnconfigure(0, weight=0)  # Sidebar: fixed or minimal width
        self.root.grid_columnconfigure(1, weight=1)  # Main content: takes most space
        self.root.grid_rowconfigure(1, weight=1)
        self.create_header_frame()
        self.create_sidebar_panel()
        self.create_main_frame()
        self.create_status_bar()
        
        # Force layout update and ensure proper sizing
        self.root.update_idletasks()
        self.root.update()
        self.root.minsize(1200, 800)

    def create_sidebar_panel(self):
        """Create left sidebar panel with vertical navigation buttons that control the main content area"""
        sidebar = ctk.CTkFrame(self.root, fg_color="#232946", width=90)
        sidebar.grid(row=1, column=0, sticky="nsw", padx=(10, 0), pady=5)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Vertical navigation buttons
        self.flips_btn = ctk.CTkButton(sidebar, text="🦁\nFlips", command=lambda: self.select_main_tab("Flips"), height=60, width=80, anchor="center")
        self.flips_btn.grid(row=0, column=0, padx=4, pady=(15, 8), sticky="ew")
        self.analytics_btn = ctk.CTkButton(sidebar, text="📈\nAnalytics", command=lambda: self.select_main_tab("Analytics"), height=60, width=80, anchor="center")
        self.analytics_btn.grid(row=1, column=0, padx=4, pady=8, sticky="ew")
        self.enchanting_btn = ctk.CTkButton(sidebar, text="✨\nEnchant", command=lambda: self.select_main_tab("Enchanting"), height=60, width=80, anchor="center")
        self.enchanting_btn.grid(row=2, column=0, padx=4, pady=8, sticky="ew")
        self.settings_btn = ctk.CTkButton(sidebar, text="⚙️\nSettings", command=lambda: self.select_main_tab("Settings"), height=60, width=80, anchor="center")
        self.settings_btn.grid(row=3, column=0, padx=4, pady=(8, 15), sticky="ew")

    def create_main_frame(self):
        """Create main content area with all tabs: Flips, Analytics, Stats, Settings"""
        main_frame = ctk.CTkFrame(self.root, fg_color="#232946")
        main_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        # Add CTkTabview for main content
        self.tabview = CTkTabview(main_frame, fg_color="#232946", segmented_button_fg_color="#232946", segmented_button_selected_color=ACCENT_COLOR, segmented_button_unselected_color="#232946", segmented_button_selected_hover_color="#00b0cc", width=900)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.add("Flips")
        self.create_results_panel(self.tabview.tab("Flips"))
        self.tabview.add("Analytics")
        self.create_analytics_section(self.tabview.tab("Analytics"))
        self.tabview.add("Enchanting")
        self.create_enchanting_panel(self.tabview.tab("Enchanting"))
        self.tabview.add("Settings")
        self.create_settings_panel(self.tabview.tab("Settings"))
        # Hide CTkTabview's segmented tab buttons (sidebar handles navigation)
        try:
            self.tabview._segmented_button.grid_remove()
        except AttributeError:
            pass  # Fallback if private attribute name changes in future versions
        self.tabview.set("Flips")  # Default to Flips tab

    def select_main_tab(self, tab_name):
        """Select the given tab in the main content area and update header if needed"""
        self.tabview.set(tab_name)
        # Optionally update header here if you want to reflect the selected tab
        # Example: self.header_label.configure(text=tab_name)

    def create_status_bar(self):
        status_bar = ctk.CTkFrame(self.root, fg_color="#181c24", height=36, corner_radius=0, border_width=0)
        self._themed_widgets.append(status_bar)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 12))
        status_bar.grid_columnconfigure(0, weight=1)
        status_label = ctk.CTkLabel(status_bar, textvariable=self.status_var, font=("Segoe UI", 11), text_color=ACCENT_COLOR)
        self._themed_widgets.append(status_label)
        status_label.grid(row=0, column=0, padx=16, pady=6, sticky="w")

    def create_header_frame(self):
        # Glassmorphism: create a blurred, semi-transparent overlay for the header
        header_frame = ctk.CTkFrame(self.root, fg_color="#232946", corner_radius=24, border_width=0)
        self._themed_widgets.append(header_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 8))
        header_frame.grid_columnconfigure(13, weight=1)
        # App icon and title
        icon_label = ctk.CTkLabel(header_frame, text="🦁", font=("Segoe UI Emoji", 36))
        self._themed_widgets.append(icon_label)
        icon_label.grid(row=0, column=0, padx=(20, 10), pady=10)
        title_label = ctk.CTkLabel(header_frame, text="Rat Flipper Pro", font=HEADER_FONT, text_color=ACCENT_COLOR)
        self._themed_widgets.append(title_label)
        title_label.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="w")
        sep1 = ctk.CTkLabel(header_frame, text="|", font=MODERN_FONT, text_color="#444")
        self._themed_widgets.append(sep1)
        sep1.grid(row=0, column=2, padx=6)
        # NATS server selection (restored)
        nats_label = ctk.CTkLabel(header_frame, text="🌐  NATS Server:", font=MODERN_FONT, text_color="#f8f8f2")
        nats_label.grid(row=0, column=3, padx=6, pady=10, sticky="e")
        self._themed_widgets.append(nats_label)
        self.nats_server_combo = ctk.CTkComboBox(
            header_frame,
            values=["Europe", "Americas", "Asia"],
            variable=self.selected_nats_region,
            command=self.on_nats_server_change,
            width=130,
            font=MODERN_FONT,
            dropdown_font=MODERN_FONT,
            corner_radius=14,
            fg_color="#232946",
            text_color="#f8f8f2"
        )
        self.selected_nats_region.set("Europe")
        self._themed_widgets.append(self.nats_server_combo)
        self.create_tooltip(self.nats_server_combo, "Select NATS server region")
        self.nats_server_combo.grid(row=0, column=4, padx=10, pady=10)

        sep2 = ctk.CTkLabel(header_frame, text="|", font=MODERN_FONT, text_color="#444")
        self._themed_widgets.append(sep2)
        sep2.grid(row=0, column=5, padx=6)

        premium_check = ctk.CTkCheckBox(
            header_frame,
            text="Premium",
            variable=self.premium_var,
            command=self.apply_filters_and_refresh,
            font=MODERN_FONT,
            text_color="#f8f8f2"
        )
        self._themed_widgets.append(premium_check)
        premium_check.grid(row=0, column=6, padx=(10, 0), pady=10)
        self.create_tooltip(premium_check, "Calculate profits using premium tax rates (2.5% tax + 4% setup fee)")

        # Font size controls
        font_frame = ctk.CTkFrame(header_frame, fg_color="#232946")
        self._themed_widgets.append(font_frame)
        font_label = ctk.CTkLabel(font_frame, text="🔠  Font:", font=MODERN_FONT, text_color="#f8f8f2")
        font_label.pack(side="left", padx=6)
        self._themed_widgets.append(font_label)
        self.font_size_var = tk.StringVar(value=str(self.current_font_size))
        font_combo = ctk.CTkComboBox(
            font_frame,
            values=["10", "12", "14", "16", "18", "20"],
            variable=self.font_size_var,
            command=self.change_font_size,
            width=90,
            font=MODERN_FONT,
            dropdown_font=MODERN_FONT,
            corner_radius=14,
            fg_color="#232946",
            text_color="#f8f8f2"
        )
        self._themed_widgets.append(font_combo)
        self.create_tooltip(font_combo, "Change font size")
        self.connection_label = ctk.CTkLabel(
            header_frame,
            text="🔴  Disconnected",
            font=MODERN_FONT
        )
        self._themed_widgets.append(self.connection_label)
        self.connection_label.grid(row=0, column=9, padx=10, pady=10)
        refresh_button = AnimatedButton(
            header_frame,
            text="🔄  Refresh",
            command=self.refresh_nats_server,
            width=120,
            height=40,
            fg_color=ACCENT_COLOR,
            text_color="#f8f8f2",
            corner_radius=20
        )
        self._themed_widgets.append(refresh_button)
        refresh_button.grid(row=0, column=10, padx=10, pady=10)
        refresh_button.bind("<Enter>", lambda e: refresh_button.configure(fg_color="#00b0cc"))
        refresh_button.bind("<Leave>", lambda e: refresh_button.configure(fg_color=ACCENT_COLOR))
        self.create_tooltip(refresh_button, "Reconnect to the selected NATS server")
        
        # Manual Scan button
        manual_scan_button = AnimatedButton(
            header_frame,
            text="🔍 Scan & Refresh",
            command=self.run_full_scan,
            width=160,
            height=40,
            fg_color=ACCENT_COLOR,
            text_color="#f8f8f2",
            corner_radius=20
        )
        self._themed_widgets.append(manual_scan_button)
        manual_scan_button.grid(row=0, column=11, padx=10, pady=10)
        manual_scan_button.bind("<Enter>", lambda e: manual_scan_button.configure(fg_color="#00b0cc"))
        manual_scan_button.bind("<Leave>", lambda e: manual_scan_button.configure(fg_color=ACCENT_COLOR))
        self.create_tooltip(manual_scan_button, "Run a full scan for new flips and refresh the table")

        # Reload items.txt button
        reload_items_button = AnimatedButton(
            header_frame,
            text="🔄 Reload items.txt",
            command=self.reload_item_filters,
            width=180,
            height=40,
            fg_color=ACCENT_COLOR,
            text_color="#f8f8f2",
            corner_radius=20
        )
        self._themed_widgets.append(reload_items_button)
        reload_items_button.grid(row=0, column=12, padx=10, pady=10)
        self.create_tooltip(reload_items_button, "Force a reload of the items.txt file")
        # Webhook Ban System removed - this should be a separate admin tool

    def create_stats_panel(self, parent):
        """Create statistics panel for smaller side window"""
        # Stats content
        stats_label = ctk.CTkLabel(parent, text="📊 Statistics", font=("Segoe UI", 14, "bold"), text_color=ACCENT_COLOR)
        stats_label.pack(pady=8)
        
        # Add some basic stats
        self.total_flips_label = ctk.CTkLabel(parent, text="Total Flips: 0", font=("Segoe UI", 11))
        self.total_flips_label.pack(pady=3)
        
        self.total_profit_label = ctk.CTkLabel(parent, text="Total Profit: 0", font=("Segoe UI", 11))
        self.total_profit_label.pack(pady=3)
        
        self.avg_profit_label = ctk.CTkLabel(parent, text="Average Profit: 0", font=("Segoe UI", 11))
        self.avg_profit_label.pack(pady=3)
        
        # Refresh stats button
        refresh_stats_btn = ctk.CTkButton(parent, text="Refresh Stats", command=self.refresh_stats, height=30)
        refresh_stats_btn.pack(pady=8)

    def create_settings_panel(self, parent):
        """Create settings panel for smaller side window with debug, theme, background, and flip management controls (no premium or min profit)"""
        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)
        
        # Add animated scroll indicator
        self.scroll_indicator = ctk.CTkLabel(
            parent,
            text="⬇️",
            font=("Segoe UI", 20),
            text_color="#00d4ff"
        )
        self.scroll_indicator.pack(side="bottom", pady=5)
        
        # Animate the scroll indicator
        def animate_scroll_indicator():
            if hasattr(self, 'scroll_indicator') and self.scroll_indicator.winfo_exists():
                current_text = self.scroll_indicator.cget("text")
                if current_text == "⬇️":
                    self.scroll_indicator.configure(text="⬇")
                else:
                    self.scroll_indicator.configure(text="⬇️")
                parent.after(800, animate_scroll_indicator)
        
        animate_scroll_indicator()
        
        # Bind scroll events to hide/show indicator
        def on_scroll(event):
            if scrollable_frame._parent_canvas.yview()[1] >= 1.0:  # At bottom
                self.scroll_indicator.pack_forget()
            else:
                self.scroll_indicator.pack(side="bottom", pady=5)
        
        scrollable_frame._parent_canvas.bind("<MouseWheel>", on_scroll)
        scrollable_frame._parent_canvas.bind("<Button-4>", on_scroll)
        scrollable_frame._parent_canvas.bind("<Button-5>", on_scroll)
        
        # Use scrollable_frame as the new parent
        parent = scrollable_frame
        # Main settings header with enhanced styling
        settings_header_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        settings_header_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        settings_label = ctk.CTkLabel(
            settings_header_frame, 
            text="⚙️ Settings", 
            font=("Segoe UI", 16, "bold"), 
            text_color="#00d4ff"
        )
        settings_label.pack(pady=12)
        
        # Save settings button with enhanced styling
        save_settings_btn = ctk.CTkButton(
            settings_header_frame, 
            text="💾 Save Settings", 
            command=self.save_config, 
            height=36,
            fg_color="#00d4ff",
            text_color="#181c24",
            corner_radius=18,
            font=("Segoe UI", 12, "bold"),
            hover_color="#00b0cc"
        )
        save_settings_btn.pack(pady=(0, 12))
        
        # --- Divider ---
        divider1 = ctk.CTkLabel(parent, text="", height=2, fg_color="#2d3748", width=200)
        divider1.pack(fill="x", padx=8, pady=8)
        
        # Debug and Development section
        debug_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        debug_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        debug_header = ctk.CTkLabel(
            debug_frame,
            text="🐛 Debug & Development",
            font=("Segoe UI", 14, "bold"),
            text_color="#00d4ff"
        )
        debug_header.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Debug/log window button
        debug_btn = ctk.CTkButton(
            debug_frame, 
            text="📊 Open Debug/Log Window", 
            command=self.show_log_window, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        debug_btn.pack(fill="x", padx=12, pady=(0, 8))
        
        # Debug toggle button
        self.debug_toggle_var = tk.BooleanVar(value=self.debug_enabled)
        debug_toggle_btn = ctk.CTkButton(
            debug_frame, 
            text="🔧 Toggle Debug Logging", 
            command=self.toggle_debug_logging, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        debug_toggle_btn.pack(fill="x", padx=12, pady=(0, 12))
        
        # --- Divider ---
        divider2 = ctk.CTkLabel(parent, text="", height=2, fg_color="#2d3748", width=200)
        divider2.pack(fill="x", padx=8, pady=8)
        
        # Appearance section
        appearance_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        appearance_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        appearance_header = ctk.CTkLabel(
            appearance_frame,
            text="🎨 Appearance",
            font=("Segoe UI", 14, "bold"),
            text_color="#00d4ff"
        )
        appearance_header.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Theme picker button
        theme_btn = ctk.CTkButton(
            appearance_frame, 
            text="🎨 Theme Picker", 
            command=self.open_theme_picker, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        theme_btn.pack(fill="x", padx=12, pady=(0, 8))
        
        # Background image selection button
        bg_btn = ctk.CTkButton(
            appearance_frame, 
            text="🖼️ Set Background Image", 
            command=self.set_background_image, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        bg_btn.pack(fill="x", padx=12, pady=(0, 12))
        
        # --- Divider ---
        divider3 = ctk.CTkLabel(parent, text="", height=2, fg_color="#2d3748", width=200)
        divider3.pack(fill="x", padx=8, pady=8)
        
        # Notification settings section with enhanced styling
        notification_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        notification_frame.pack(fill="x", padx=8, pady=8)
        
        # Header with status indicator
        notification_header_frame = ctk.CTkFrame(notification_frame, fg_color="transparent")
        notification_header_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        notification_label = ctk.CTkLabel(
            notification_header_frame, 
            text="🔔 Notifications", 
            font=("Segoe UI", 14, "bold"), 
            text_color="#00d4ff"
        )
        notification_label.pack(side="left")
        
        # Status indicator
        notification_status_label = ctk.CTkLabel(
            notification_header_frame, 
            text="●", 
            font=("Segoe UI", 16), 
            text_color="#00ff88"
        )
        notification_status_label.pack(side="right", padx=(0, 8))
        
        # Notification toggle with enhanced styling
        toggle_frame = ctk.CTkFrame(notification_frame, fg_color="#232946", corner_radius=8)
        toggle_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        self.notifications_enabled = tk.BooleanVar(value=True)
        notification_toggle = ctk.CTkCheckBox(
            toggle_frame, 
            text="Enable Desktop Notifications", 
            variable=self.notifications_enabled, 
            command=self.toggle_notifications,
            font=("Segoe UI", 12, "bold"),
            text_color="#ffffff",
            fg_color="#00d4ff",
            hover_color="#00b0cc",
            corner_radius=4
        )
        notification_toggle.pack(pady=12, padx=12, anchor="w")
        
        # Settings container
        settings_container = ctk.CTkFrame(notification_frame, fg_color="#232946", corner_radius=8)
        settings_container.pack(fill="x", padx=12, pady=(0, 12))
        
        settings_header = ctk.CTkLabel(
            settings_container,
            text="Notification Settings",
            font=("Segoe UI", 12, "bold"),
            text_color="#ffffff"
        )
        settings_header.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Minimum profit threshold for notifications
        profit_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        profit_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        profit_label = ctk.CTkLabel(
            profit_frame, 
            text="Min Profit Alert:", 
            font=("Segoe UI", 11, "bold"),
            text_color="#a0aec0"
        )
        profit_label.pack(side="left")
        
        self.notification_min_profit = tk.StringVar(value="200000")
        profit_entry = ctk.CTkEntry(
            profit_frame, 
            textvariable=self.notification_min_profit, 
            width=120, 
            font=("Segoe UI", 11),
            fg_color="#1a1d2e",
            border_color="#2d3748",
            text_color="#ffffff",
            corner_radius=6
        )
        profit_entry.pack(side="left", padx=(8, 4))
        
        profit_unit = ctk.CTkLabel(
            profit_frame, 
            text="silver", 
            font=("Segoe UI", 11),
            text_color="#718096"
        )
        profit_unit.pack(side="left")
        
        # Cooldown setting
        cooldown_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        cooldown_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        cooldown_label = ctk.CTkLabel(
            cooldown_frame, 
            text="Notification Cooldown:", 
            font=("Segoe UI", 11, "bold"),
            text_color="#a0aec0"
        )
        cooldown_label.pack(side="left")
        
        self.notification_cooldown_var = tk.StringVar(value="10")
        cooldown_entry = ctk.CTkEntry(
            cooldown_frame, 
            textvariable=self.notification_cooldown_var, 
            width=80, 
            font=("Segoe UI", 11),
            fg_color="#1a1d2e",
            border_color="#2d3748",
            text_color="#ffffff",
            corner_radius=6
        )
        cooldown_entry.pack(side="left", padx=(8, 4))
        
        cooldown_unit = ctk.CTkLabel(
            cooldown_frame, 
            text="seconds", 
            font=("Segoe UI", 11),
            text_color="#718096"
        )
        cooldown_unit.pack(side="left")
        
        # --- Divider ---
        divider2_5 = ctk.CTkLabel(parent, text="", height=2, fg_color="#444444", width=200)
        divider2_5.pack(fill="x", padx=8, pady=6)
        
        # Auto-updater section with enhanced styling
        updater_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        updater_frame.pack(fill="x", padx=8, pady=8)
        
        # Header with gradient effect
        header_frame = ctk.CTkFrame(updater_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        updater_label = ctk.CTkLabel(
            header_frame, 
            text="🔄 Auto-Updater", 
            font=("Segoe UI", 14, "bold"), 
            text_color="#00d4ff"
        )
        updater_label.pack(side="left")
        
        # Status indicator
        status_label = ctk.CTkLabel(
            header_frame, 
            text="●", 
            font=("Segoe UI", 16), 
            text_color="#00ff88"
        )
        status_label.pack(side="right", padx=(0, 8))
        
        # Version display with enhanced styling
        version_frame = ctk.CTkFrame(updater_frame, fg_color="#232946", corner_radius=8)
        version_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        version_label = ctk.CTkLabel(
            version_frame, 
            text=f"Current Version: {self.current_version}", 
            font=("Segoe UI", 12),
            text_color="#a0aec0"
        )
        version_label.pack(pady=8)
        
        # Check for updates button with enhanced styling
        check_update_btn = ctk.CTkButton(
            parent, 
            text="🔍 Check for Updates", 
            command=self.check_for_updates, 
            height=36,
            fg_color="#00d4ff",
            text_color="#181c24",
            corner_radius=18,
            font=("Segoe UI", 12, "bold"),
            hover_color="#00b0cc"
        )
        check_update_btn.pack(fill="x", padx=8, pady=(0, 8))
        
        # Auto-check for updates on startup with enhanced styling
        self.auto_check_updates = tk.BooleanVar(value=True)
        auto_check_frame = ctk.CTkFrame(updater_frame, fg_color="transparent")
        auto_check_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        auto_check_toggle = ctk.CTkCheckBox(
            auto_check_frame, 
            text="Check for updates on startup", 
            variable=self.auto_check_updates,
            font=("Segoe UI", 11),
            text_color="#e2e8f0",
            fg_color="#00d4ff",
            hover_color="#00b0cc",
            corner_radius=4
        )
        auto_check_toggle.pack(side="left")
        
        # Last checked info
        last_checked_label = ctk.CTkLabel(
            auto_check_frame, 
            text="Last checked: Never", 
            font=("Segoe UI", 10),
            text_color="#718096"
        )
        last_checked_label.pack(side="right")
        
        # --- Divider ---
        divider2_6 = ctk.CTkLabel(parent, text="", height=2, fg_color="#444444", width=200)
        divider2_6.pack(fill="x", padx=8, pady=6)
        
        # Flip management section
        flip_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        flip_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        flip_header = ctk.CTkLabel(
            flip_frame,
            text="🦁 Flip Management",
            font=("Segoe UI", 14, "bold"),
            text_color="#00d4ff"
        )
        flip_header.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Flip management buttons
        export_btn = ctk.CTkButton(
            flip_frame, 
            text="💾 Export Completed Flips", 
            command=self.export_opportunities, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        export_btn.pack(fill="x", padx=12, pady=(0, 8))
        
        clear_btn = ctk.CTkButton(
            flip_frame, 
            text="🗑️ Clear All Flips", 
            command=self.clear_results, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        clear_btn.pack(fill="x", padx=12, pady=(0, 8))
        
        reset_sort_btn = ctk.CTkButton(
            flip_frame, 
            text="🔄 Reset Sort", 
            command=self.reset_sort, 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        reset_sort_btn.pack(fill="x", padx=12, pady=(0, 12))
        
        # --- Divider ---
        divider4 = ctk.CTkLabel(parent, text="", height=2, fg_color="#2d3748", width=200)
        divider4.pack(fill="x", padx=8, pady=8)
        
        # Community and Support section
        community_frame = ctk.CTkFrame(parent, fg_color="#1a1d2e", corner_radius=12, border_width=1, border_color="#2d3748")
        community_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        community_header = ctk.CTkLabel(
            community_frame,
            text="💬 Community & Support",
            font=("Segoe UI", 14, "bold"),
            text_color="#00d4ff"
        )
        community_header.pack(pady=(12, 8), padx=12, anchor="w")
        
        # Discord server button
        discord_btn = ctk.CTkButton(
            community_frame, 
            text="📱 Join Discord Server", 
            command=lambda: self.open_url("https://discord.gg/JU43X7YVKB"), 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        discord_btn.pack(fill="x", padx=12, pady=(0, 8))
        
        # Support project button
        support_btn = ctk.CTkButton(
            community_frame, 
            text="❤️ Support Project", 
            command=lambda: self.open_url("https://ko-fi.com/ratflipper"), 
            height=36,
            fg_color="#232946",
            text_color="#ffffff",
            corner_radius=18,
            font=("Segoe UI", 11),
            hover_color="#2d3748"
        )
        support_btn.pack(fill="x", padx=12, pady=(0, 12))
        
        # Optionally, add more flip-related controls here

    def create_enchanting_panel(self, parent):
        """Create enchanting panel with opportunities table and controls"""
        # Create scrollable frame for enchanting panel
        scrollable_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)
        
        self.enchanting_min_profit_var = tk.StringVar(value="1000")
        enchanting_frame = ctk.CTkFrame(scrollable_frame, fg_color="#23272e", corner_radius=24, border_width=0)
        self._themed_widgets.append(enchanting_frame)
        enchanting_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        
        header = ctk.CTkLabel(
            enchanting_frame,
            text="✨ Enchanting Opportunities",
            font=HEADER_FONT,
            text_color=ACCENT_COLOR
        )
        self._themed_widgets.append(header)
        header.pack(pady=(16, 0), anchor="w", padx=24)
        
        # Controls: input prices, source city
        controls_frame = ctk.CTkFrame(enchanting_frame, fg_color="transparent")
        controls_frame.pack(fill="x", padx=24, pady=(8, 8))
        
        price_btn = AnimatedButton(controls_frame, text="Set Rune/Soul/Relic Prices", command=self.input_enchanting_prices, width=220, height=32)
        price_btn.grid(row=0, column=0, padx=(0, 20), sticky="w")
        
        ctk.CTkLabel(controls_frame, text="Source City:", font=MODERN_FONT).grid(row=0, column=1, padx=(0, 5), sticky="w")
        city_combo = ctk.CTkComboBox(controls_frame, values=['All Cities', 'Brecilien', 'Bridgewatch', 'Lymhurst', 'Fort Sterling', 'Thetford', 'Martlock', 'Caerleon'], variable=self.enchanting_source_city, width=150, font=MODERN_FONT, dropdown_font=MODERN_FONT)
        city_combo.grid(row=0, column=2, padx=(0, 20), sticky="w")
        
        # Add Min Profit label and entry
        ctk.CTkLabel(controls_frame, text="Min Profit:", font=MODERN_FONT).grid(row=0, column=3, padx=(0, 5), sticky="w")
        min_profit_entry = ctk.CTkEntry(controls_frame, textvariable=self.enchanting_min_profit_var, width=100, font=MODERN_FONT)
        min_profit_entry.grid(row=0, column=4, padx=(0, 20), sticky="w")
        min_profit_entry.bind("<KeyRelease>", lambda e: self.refresh_enchanting_table())
        
        # Table
        columns = ('City', 'Item', 'Quality', 'Path', 'City Price', 'Enchant Cost', 'BM Price', 'Total Profit', 'ROI', 'Last Update', 'Done')
        self.enchanting_tree = ttk.Treeview(enchanting_frame, columns=columns, show='headings', height=17, style='Custom.Treeview')
        col_config = {
            'City': (120, 'center'),
            'Item': (320, 'w'),
            'Quality': (100, 'center'),
            'Path': (220, 'center'),
            'City Price': (120, 'center'),
            'Enchant Cost': (120, 'center'),
            'BM Price': (120, 'center'),
            'Total Profit': (140, 'center'),
            'ROI': (100, 'center'),
            'Last Update': (140, 'center'),
            'Done': (70, 'center'),
        }
        for col, (width, anchor) in col_config.items():
            anchor_val = 'center' if anchor == 'center' else 'w'
            self.enchanting_tree.heading(col, text=col, anchor=anchor_val, command=lambda c=col: self.sort_enchanting_by_column(c, False))
            self.enchanting_tree.column(col, width=width, anchor=anchor_val, minwidth=60, stretch=True)
        
        self.enchanting_tree.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.enchanting_tree.configure(height=17)
        
        v_scrollbar = ttk.Scrollbar(enchanting_frame, orient='vertical', command=self.enchanting_tree.yview)
        h_scrollbar = ttk.Scrollbar(enchanting_frame, orient='horizontal', command=self.enchanting_tree.xview)
        self.enchanting_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview',
                        font=("Segoe UI", 11),
                        rowheight=34,
                        borderwidth=0,
                        relief='flat',
                        background='#23272e',
                        fieldbackground='#23272e',
                        foreground='#f8f8f2',
                        highlightthickness=0)
        style.configure('Custom.Treeview.Heading',
                        font=("Segoe UI", 12, "bold"),
                        background='#181c24',
                        foreground=ACCENT_COLOR,
                        borderwidth=0)
        style.map('Custom.Treeview',
                  background=[('selected', ACCENT_COLOR), ('active', '#232946')],
                  foreground=[('selected', '#181c24'), ('active', ACCENT_COLOR)])
        style.layout('Custom.Treeview', [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])
        
        self.enchanting_tree.tag_configure('oddrow', background='#23272e')
        self.enchanting_tree.tag_configure('evenrow', background='#2b2f36')
        enchanting_frame.grid_rowconfigure(2, weight=1)
        enchanting_frame.grid_columnconfigure(0, weight=1)
        
        # Add count label below the table
        self.enchanting_count_var = tk.StringVar(value="0 of 0 opportunities")
        enchanting_count_label = ctk.CTkLabel(
            enchanting_frame, textvariable=self.enchanting_count_var, font=MODERN_FONT, fg_color="#181c24"
        )
        enchanting_count_label.pack(anchor="e", padx=24, pady=(0, 8))
        
        # Bind click events
        self.enchanting_tree.bind("<Button-1>", self.on_enchanting_tree_click)
        
        # Add a method to refresh the enchanting table and count label with debug logs
        def refresh_enchanting_table():
            try:
                opportunities = getattr(self, 'enchanting_opportunities', [])
                print(f"[ENCHANT TABLE DEBUG] Called with {len(opportunities)} total opportunities before filtering.")
                # Filter by min profit
                try:
                    min_profit = int(self.enchanting_min_profit_var.get())
                except Exception:
                    min_profit = 0
                filtered_opportunities = []
                for opp in opportunities:
                    # Profit is in column 7 (index 7), formatted as string with commas and possibly 'M'
                    profit_str = opp[7].replace(',', '').replace('M', '000000')
                    try:
                        profit_val = int(float(profit_str))
                    except Exception:
                        profit_val = 0
                    if profit_val >= min_profit:
                        filtered_opportunities.append(opp)
                print(f"[ENCHANT TABLE DEBUG] Displaying {len(filtered_opportunities)} opportunities after filtering.")
                
                self.enchanting_tree.delete(*self.enchanting_tree.get_children())
                for i, opp in enumerate(filtered_opportunities):
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    city = opp[0]
                    item_name = opp[1]
                    quality_str = opp[2]
                    # Use bm_age and city_age from the row if present
                    bm_age = opp[10] if len(opp) > 10 else '?'
                    city_age = opp[11] if len(opp) > 11 else '?'
                    last_update = f'R{city_age}m/Bm{bm_age}m'
                    # Explicit column mapping for Treeview
                    col_indices = {col: idx for idx, col in enumerate(self.enchanting_tree['columns'])}
                    row_dict = {
                        'City': city,
                        'Item': item_name,
                        'Quality': quality_str,
                        'Path': opp[3],
                        'City Price': opp[4],
                        'Enchant Cost': opp[5],
                        'BM Price': opp[6],
                        'Total Profit': opp[7],
                        'ROI': opp[8],
                        'Last Update': last_update,
                        'Done': opp[9] if len(opp) > 9 else ""
                    }
                    values = [row_dict.get(col, "") for col in self.enchanting_tree['columns']]
                    if self.debug_enabled:
                        print(f"[ENCHANT TABLE DEBUG] Columns: {self.enchanting_tree['columns']}")
                        print(f"[ENCHANT TABLE DEBUG] Values: {values}")
                    self.enchanting_tree.insert('', 'end', values=values, tags=(tag,))
                
                self.enchanting_count_var.set(f"{len(filtered_opportunities)} of {len(opportunities)} opportunities")
                if hasattr(self, 'enchanting_debug_log'):
                    self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Refreshed enchanting table: {len(filtered_opportunities)} opportunities displayed.")
            except Exception as e:
                err_msg = f"[ERROR] Exception in refresh_enchanting_table: {e}"
                print(err_msg)
                if hasattr(self, 'enchanting_debug_log'):
                    self.enchanting_debug_log.appendleft(err_msg)
                if hasattr(self, 'enchanting_raw_debug_log'):
                    self.enchanting_raw_debug_log.append(err_msg)
        
        self.refresh_enchanting_table = refresh_enchanting_table

    def refresh_stats(self):
        """Refresh statistics display"""
        total_flips = len(self.completed_flips_history)
        total_profit = sum(flip['profit'] for flip in self.completed_flips_history)
        avg_profit = total_profit / total_flips if total_flips > 0 else 0
        
        self.total_flips_label.configure(text=f"Total Flips: {total_flips}")
        self.total_profit_label.configure(text=f"Total Profit: {total_profit:,}")
        self.avg_profit_label.configure(text=f"Average Profit: {avg_profit:,.0f}")

    def change_analytics_period(self, period):
        """Change the analytics time period and refresh the display."""
        self.analytics_time_period.set(period)
        self._highlight_analytics_button(period)
        self.refresh_analytics_tab()
    
    def _highlight_analytics_button(self, active_period):
        """Highlight the active time period button."""
        periods = ["Week", "Month", "Year", "All Time"]
        for period in periods:
            btn = getattr(self, f'analytics_btn_{period.lower().replace(" ", "_")}', None)
            if btn:
                if period == active_period:
                    btn.configure(fg_color="#00d4ff", text_color="#181c24")
                else:
                    btn.configure(fg_color="#232946", text_color="#a0aec0")
    
    def _get_filtered_flips_by_period(self, period):
        """Get flips filtered by the selected time period."""
        if not self.completed_flips_history:
            return []
        
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        if period == "Week":
            cutoff_date = now - timedelta(days=7)
        elif period == "Month":
            cutoff_date = now - timedelta(days=30)
        elif period == "Year":
            cutoff_date = now - timedelta(days=365)
        else:  # All Time
            return self.completed_flips_history
        
        filtered_flips = []
        for flip in self.completed_flips_history:
            try:
                flip_time = datetime.strptime(flip['time'], '%Y-%m-%d %H:%M:%S')
                if flip_time >= cutoff_date:
                    filtered_flips.append(flip)
            except (ValueError, KeyError):
                # Skip invalid entries
                continue
        
        return filtered_flips
    
    def _calculate_analytics_stats(self, filtered_flips):
        """Calculate detailed statistics for the filtered flips."""
        if not filtered_flips:
            return {
                'total_profit': 0,
                'flip_count': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'min_profit': 0,
                'best_item': '',
                'best_city': '',
                'profit_per_day': 0
            }
        
        total_profit = sum(flip['profit'] for flip in filtered_flips)
        flip_count = len(filtered_flips)
        avg_profit = total_profit // flip_count if flip_count > 0 else 0
        
        profits = [flip['profit'] for flip in filtered_flips]
        max_profit = max(profits)
        min_profit = min(profits)
        
        # Find best performing item and city
        item_profits = {}
        city_profits = {}
        for flip in filtered_flips:
            item = flip['item']
            city = flip['city']
            item_profits[item] = item_profits.get(item, 0) + flip['profit']
            city_profits[city] = city_profits.get(city, 0) + flip['profit']
        
        best_item = max(item_profits.items(), key=lambda x: x[1])[0] if item_profits else ''
        best_city = max(city_profits.items(), key=lambda x: x[1])[0] if city_profits else ''
        
        # Calculate profit per day
        if filtered_flips:
            from datetime import datetime, timedelta
            times = [datetime.strptime(flip['time'], '%Y-%m-%d %H:%M:%S') for flip in filtered_flips]
            time_span = max(times) - min(times)
            days = max(1, time_span.days + 1)  # At least 1 day
            profit_per_day = total_profit // days
        else:
            profit_per_day = 0
        
        return {
            'total_profit': total_profit,
            'flip_count': flip_count,
            'avg_profit': avg_profit,
            'max_profit': max_profit,
            'min_profit': min_profit,
            'best_item': best_item,
            'best_city': best_city,
            'profit_per_day': profit_per_day
        }

    def refresh_analytics_tab(self):
        """Refreshes the data and graph in the analytics tab."""
        if not hasattr(self, 'analytics_table'):
            return # Tab not initialized yet

        # Get the current time period
        period = self.analytics_time_period.get()
        filtered_flips = self._get_filtered_flips_by_period(period)

        self.analytics_table.configure(state="normal")
        self.analytics_table.delete("1.0", "end")
        self.analytics_table.insert("end", f"{'Item':30} {'City':10} {'Profit':>10} {'Time Completed':>20}\n")
        self.analytics_table.insert("end", "-"*80+"\n")
        
        total_profit = 0
        for flip in filtered_flips:
            self.analytics_table.insert("end", f"{flip['item'][:28]:30} {flip['city'][:10]:10} {flip['profit']:>10,} {flip['time']:>20}\n")
            total_profit += flip['profit']
        
        self.analytics_table.configure(state="disabled")
        
        # Calculate and update all stats
        stats = self._calculate_analytics_stats(filtered_flips)
        
        self.analytics_profit_label.configure(text=f"Total Profit: {stats['total_profit']:,}")
        self.analytics_flips_count_label.configure(text=f"Flips: {stats['flip_count']}")
        self.analytics_avg_profit_label.configure(text=f"Avg Profit: {stats['avg_profit']:,}")
        self.analytics_profit_per_day_label.configure(text=f"Profit/Day: {stats['profit_per_day']:,}")
        self.analytics_max_profit_label.configure(text=f"Max Profit: {stats['max_profit']:,}")
        
        # Truncate long item names for display
        best_item_display = stats['best_item'][:15] + "..." if len(stats['best_item']) > 15 else stats['best_item']
        self.analytics_best_item_label.configure(text=f"Best Item: {best_item_display}")
        self.analytics_best_city_label.configure(text=f"Best City: {stats['best_city']}")

    def create_results_panel(self, parent):
        # Create scrollable frame for results panel
        scrollable_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)
        
        results_frame = ctk.CTkFrame(scrollable_frame, fg_color="#23272e", corner_radius=24, border_width=0)
        self._themed_widgets.append(results_frame)
        results_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        results_header = ctk.CTkLabel(
            results_frame,
            text="📊  Flip Opportunities",
            font=HEADER_FONT,
            text_color=ACCENT_COLOR
        )
        self._themed_widgets.append(results_header)
        results_header.pack(pady=(16, 0), anchor="w", padx=24)

        filter_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=24, pady=(8, 8))
        
        # Using grid layout instead of pack for more predictable alignment
        ctk.CTkLabel(filter_frame, text="City:", font=MODERN_FONT).grid(row=0, column=0, padx=(0, 5), sticky="w")
        city_filter_combo = ctk.CTkComboBox(filter_frame, values=["All", 'Brecilien', 'Bridgewatch', 'Lymhurst', 'Fort Sterling', 'Thetford', 'Martlock', 'Caerleon'], variable=self.filter_city_var, command=self.apply_filters_and_refresh, width=150, font=MODERN_FONT, dropdown_font=MODERN_FONT)
        city_filter_combo.grid(row=0, column=1, padx=(0, 20), sticky="w")

        ctk.CTkLabel(filter_frame, text="Quality:", font=MODERN_FONT).grid(row=0, column=2, padx=(0, 5), sticky="w")
        quality_filter_combo = ctk.CTkComboBox(filter_frame, values=["All", "Normal", "Good", "Outstanding", "Excellent", "Masterpiece"], variable=self.filter_quality_var, command=self.apply_filters_and_refresh, width=150, font=MODERN_FONT, dropdown_font=MODERN_FONT)
        quality_filter_combo.grid(row=0, column=3, padx=(0, 20), sticky="w")

        ctk.CTkLabel(filter_frame, text="Tier:", font=MODERN_FONT).grid(row=0, column=4, padx=(0, 5), sticky="w")
        tier_filter_combo = ctk.CTkComboBox(filter_frame, values=["All"] + [str(i) for i in range(4, 9)], variable=self.filter_tier_var, command=self.apply_filters_and_refresh, width=100, font=MODERN_FONT, dropdown_font=MODERN_FONT)
        tier_filter_combo.grid(row=0, column=5, padx=(0, 20), sticky="w")

        ctk.CTkLabel(filter_frame, text="Min Profit:", font=MODERN_FONT).grid(row=0, column=6, padx=(20, 5), sticky="w")
        
        min_profit_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.min_profit_var,
            width=100,
            font=MODERN_FONT
        )
        min_profit_entry.grid(row=0, column=7, padx=(0, 20), sticky="w")
        min_profit_entry.bind("<KeyRelease>", self.apply_filters_and_refresh)
        self.create_tooltip(min_profit_entry, "Only show flips with profit greater than this amount.")

        clear_filters_btn = AnimatedButton(filter_frame, text="Clear Filters", command=self.clear_filters, width=120, height=30)
        clear_filters_btn.grid(row=0, column=8, padx=(20, 0), sticky="w")

        # Configure style BEFORE creating treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview',
                        font=("Segoe UI", 10),  # Font size 10 as requested
                        rowheight=20,  # Row height 20 to match enchanting table
                        borderwidth=0,
                        relief='flat',
                        background='#23272e',
                        fieldbackground='#23272e',
                        foreground='#f8f8f2',
                        highlightthickness=0)
        style.configure('Custom.Treeview.Heading',
                        font=("Segoe UI", 10, "bold"),
                        background='#181c24',
                        foreground=ACCENT_COLOR,
                        borderwidth=0)
        style.map('Custom.Treeview',
                  background=[('selected', ACCENT_COLOR), ('active', '#232946')],
                  foreground=[('selected', '#181c24'), ('active', ACCENT_COLOR)])
        style.layout('Custom.Treeview', [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])
        
        columns = ('Item', 'Quality', 'Buy City', 'Buy Price', 'Sell Price', 'Profit', 'Qty', 'Volume', 'Total Profit', 'ROI%', 'Price Age (BM/R)', 'Done')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=17, style='Custom.Treeview')
        col_config = {
            'Item': (300, 'w'),
            'Quality': (90, 'center'),
            'Buy City': (120, 'center'),
            'Buy Price': (110, 'center'),
            'Sell Price': (110, 'center'),
            'Profit': (130, 'center'),
            'Qty': (70, 'center'),
            'Volume': (100, 'center'),
            'Total Profit': (140, 'center'),
            'ROI%': (90, 'center'),
            'Price Age (BM/R)': (140, 'center'),
            'Done': (70, 'center'),
        }
        for col, (width, anchor) in col_config.items():
            anchor_val = 'center' if anchor == 'center' else 'w'
            self.tree.heading(col, text=col, anchor=anchor_val, command=lambda c=col: self.sort_by_column(c, False))
            self.tree.column(col, width=width, anchor=anchor_val, minwidth=60, stretch=True)
        self.tree.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.tree.configure(height=17)
        self.tree.master.update_idletasks()
        self.tree.master.winfo_toplevel().minsize(1400, 600)
        v_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.tree.tag_configure('oddrow', background='#23272e')
        self.tree.tag_configure('evenrow', background='#2b2f36')
        # Row hover effect
        def on_row_enter(event):
            rowid = self.tree.identify_row(event.y)
            if rowid:
                self.tree.tag_configure('hover', background='#1a2a3a')
                self.tree.item(rowid, tags=('hover',))
        def on_row_leave(event):
            for rowid in self.tree.get_children():
                tags = self.tree.item(rowid, 'tags')
                if 'hover' in tags:
                    self.tree.item(rowid, tags=tuple(t for t in tags if t != 'hover'))
        self.tree.bind('<Motion>', on_row_enter)
        self.tree.bind('<Leave>', on_row_leave)
        # Button frame with glass effect
        button_frame = ctk.CTkFrame(results_frame, fg_color="#232946", corner_radius=18)
        self._themed_widgets.append(button_frame)
        button_frame.pack(fill="x", padx=24, pady=(0, 24))
        export_btn = AnimatedButton(
            button_frame, text="💾  Export CSV", command=self.export_opportunities, width=140, height=40, fg_color=ACCENT_COLOR, text_color="#181c24", corner_radius=20
        )
        self._themed_widgets.append(export_btn)
        # export_btn.pack(side="left", padx=10)  # Hidden as per user request
        export_btn.pack_forget()
        clear_btn = AnimatedButton(
            button_frame, text="🗑️  Clear All", command=self.clear_results, width=140, height=40, fg_color=ACCENT_COLOR, text_color="#181c24", corner_radius=20
        )
        self._themed_widgets.append(clear_btn)
        # clear_btn.pack(side="left", padx=10)  # Hidden as per user request
        clear_btn.pack_forget()
        clear_btn.bind("<Enter>", lambda e: clear_btn.configure(fg_color="#00b0cc"))
        clear_btn.bind("<Leave>", lambda e: clear_btn.configure(fg_color=ACCENT_COLOR))
        self.create_tooltip(clear_btn, "Clear all results")
        self.results_count_var = tk.StringVar(value="0 opportunities")
        count_label = ctk.CTkLabel(
            button_frame, textvariable=self.results_count_var, font=MODERN_FONT, fg_color="#181c24"
        )
        self._themed_widgets.append(count_label)
        count_label.pack(side="right", padx=12)
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', self.on_item_double_click)
        self.create_context_menu()

    def _update_results_display(self):
        # Clear table
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Apply current sort before filtering (without triggering UI update)
        if hasattr(self, 'sort_column') and hasattr(self, 'sort_reverse'):
            self._apply_current_sort()
        
        filtered_opportunities = self._get_filtered_opportunities()
        if self.debug_enabled:
            print(f"[DEBUG] _update_results_display called: displaying {len(filtered_opportunities)} rows out of {len(self.flip_opportunities)} total opportunities.")
        for i, opp in enumerate(filtered_opportunities):
            item_name = self.item_manager.get_display_name(opp.item_name)
            quality_name = QUALITY_LEVEL_NAMES.get(opp.bm_quality, f"Q{opp.bm_quality}")
            city = opp.city
            done_status = '✔' if opp.flip_id in self.completed_flips else ''
            
            is_premium = self.premium_var.get()
            tax_rate = 0.065 if is_premium else 0.105
            
            profit = opp.bm_price - opp.city_price
            profit_after_tax = int(profit - (opp.bm_price * tax_rate))
            total_profit = profit_after_tax * opp.quantity
            roi_percentage = (profit_after_tax / opp.city_price) * 100 if opp.city_price > 0 else 0

            # Calculate price ages
            bm_age_str = 'N/A'
            city_age_str = 'N/A'
            bm_data = self.flip_detector.bm_price_data.get((opp.item_name, opp.bm_quality), {}).get('Black Market')
            if bm_data and bm_data.get('last_update'):
                bm_age = (datetime.now(timezone.utc) - bm_data['last_update']).total_seconds() / 60
                if bm_age < 1:
                    bm_age_str = 'Now'
                else:
                    bm_age_str = f"{int(bm_age)}m"
            city_qualities = self.flip_detector.city_price_data.get(opp.item_name, {}).get(opp.city, {})
            city_data = city_qualities.get(opp.city_quality)
            if city_data and city_data.get('last_update'):
                city_age = (datetime.now(timezone.utc) - city_data['last_update']).total_seconds() / 60
                if city_age < 1:
                    city_age_str = 'Now'
                else:
                    city_age_str = f"{int(city_age)}m"
            price_age_str = f"B{bm_age_str}/R{city_age_str}"
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            values = (
                item_name,
                quality_name,
                city,
                f"{opp.city_price:,}",
                f"{opp.bm_price:,}",
                f"{profit_after_tax:,}",
                opp.quantity,
                f"{opp.volume:,}",
                f"{total_profit:,}",
                f"{roi_percentage:.1f}%",
                price_age_str,
                done_status
            )
            if self.debug_enabled:
                print(f"[DEBUG] Inserting row: {values}")
            self.tree.insert('', 'end', values=values, tags=(tag,))
        self.results_count_var.set(f"{len(filtered_opportunities)} of {len(self.flip_opportunities)} opportunities")

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📋 Copy Item Name", command=self.copy_item_name)
        self.context_menu.add_command(label="✅ Mark as Completed", command=self.mark_completed)
        self.context_menu.add_command(label="🗑️ Delete from List", command=self.delete_flip)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def copy_item_name(self):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values:
                self.root.clipboard_clear()
                self.root.clipboard_append(values[0])

    def mark_completed(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get all currently displayed (and filtered) items
        current_items_in_view = self._get_filtered_opportunities()

        for sel_item in selection:
            try:
                # Find the index of the selected item in the visible list
                item_index_in_view = self.tree.index(sel_item)
                
                # Get the corresponding opportunity object
                if item_index_in_view < len(current_items_in_view):
                    opp = current_items_in_view[item_index_in_view]
                    
                    # Toggle completion status
                    if opp.flip_id in self.completed_flips:
                        self.completed_flips.remove(opp.flip_id)
                        self.completed_flips_history = [f for f in self.completed_flips_history if f.get('flip_id') != opp.flip_id]
                    else:
                        self.completed_flips.add(opp.flip_id)
                        # Add to completed history with timestamp and profit
                        from datetime import datetime
                        
                        is_premium = self.premium_var.get()
                        tax_rate = 0.065 if is_premium else 0.105
                        profit_at_completion = int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate))

                        self.completed_flips_history.append({
                            'item': opp.item_name,
                            'city': opp.city,
                            'profit': profit_at_completion,
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'flip_id': opp.flip_id
                        })
                else:
                    logger.warning(f"Selected item index {item_index_in_view} is out of bounds for the current view.")

            except (IndexError, KeyError, ValueError):
                logger.warning(f"Could not find opportunity for selected tree item: {sel_item}")
                continue
        
        self.save_completed_flips()
        self._update_results_display()
        self.refresh_analytics_tab()

    def delete_flip(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        current_items_in_view = self._get_filtered_opportunities()
        
        for sel_item in selection:
            try:
                item_index_in_view = self.tree.index(sel_item)
                
                if item_index_in_view < len(current_items_in_view):
                    opp_to_delete = current_items_in_view[item_index_in_view]
                    
                    # Find and remove the opportunity from the main list
                    self.flip_opportunities = [
                        opp for opp in self.flip_opportunities 
                        if opp.flip_id != opp_to_delete.flip_id
                    ]
                else:
                    logger.warning(f"Selected item index {item_index_in_view} is out of bounds for deletion.")
            except (IndexError, ValueError):
                logger.warning(f"Could not find opportunity for selected tree item to delete: {sel_item}")
                continue

        self._update_results_display()

    def clear_results(self):
        self.flip_opportunities = []
        self.completed_flips.clear()
        self._update_results_display()

    def apply_filters_and_refresh(self, _=None):
        """Callback for filter changes. Refreshes the view."""
        self.sort_by_column(self.sort_column, self.sort_reverse, toggle=False)

    def clear_filters(self):
        """Resets all filter dropdowns to 'All' and refreshes the view."""
        self.filter_city_var.set("All")
        self.filter_quality_var.set("All")
        self.filter_tier_var.set("All")
        self.apply_filters_and_refresh()

    def on_item_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values:
                details = f"Item: {values[0]}\nCity: {values[2]}\nBuy Price: {values[3]}\nSell Price: {values[4]}\n\nDouble-click to view detailed item information."
                messagebox.showinfo("Flip Details", details)

    def export_opportunities(self):
        if not self.flip_opportunities:
            messagebox.showwarning("Warning", "No opportunities to export")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Flip Opportunities"
        )
        if filename:
            try:
                import pandas as pd
                data = []
                is_premium = self.premium_var.get()
                tax_rate = 0.065 if is_premium else 0.105

                for opp in self.flip_opportunities:
                    status = "Completed" if opp.flip_id in self.completed_flips else "Active"
                    
                    profit_after_tax = int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate))
                    total_profit = profit_after_tax * opp.quantity
                    roi_percentage = (profit_after_tax / opp.city_price) * 100 if opp.city_price > 0 else 0

                    data.append({
                        'Item': opp.item_name,
                        'Buy City': opp.city,
                        'City_Price': opp.city_price,
                        'BM_Price': opp.bm_price,
                        'Quantity': opp.quantity,
                        'Volume': opp.volume,
                        'Profit': profit_after_tax,
                        'Total_Profit': total_profit,
                        'ROI_Percentage': round(roi_percentage, 2),
                        'Status': status,
                        'Last_Update': opp.last_update.isoformat() if opp.last_update else ''
                    })
                df = pd.DataFrame(data)
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Success", f"Exported {len(data)} opportunities to CSV")
            except Exception as e:
                messagebox.showerror("Export Error", f"Export failed: {e}")

    # NATS integration and flip detection
    def setup_nats_client(self):
        self.nats_client.add_connection_callback(self.on_nats_connection_change)
        self.nats_client.add_message_callback(self.on_nats_message)

    def start_event_loop(self):
        def run_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(self.connect_nats())
            self.event_loop.run_forever()
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()

    async def connect_nats(self):
        try:
            region = self.selected_nats_region.get()
            if region == "Auto":
                await self.nats_client.connect()
            else:
                server_url = NATS_SERVERS.get(region)
                await self.nats_client.connect(server_url=server_url)
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")

    def on_nats_connection_change(self, connected: bool, info: str):
        def update_ui():
            if connected:
                self.connection_label.configure(
                    text="🟢 Connected",
                    text_color="green"
                )
            else:
                self.connection_label.configure(
                    text="🔴 Disconnected",
                    text_color="red"
                )
        self.root.after(0, update_ui)

    def on_nats_message(self, message):
        # Store all NATS messages in buffer for debug window
        self.nats_data_buffer.appendleft(str(message))
        if message['topic'] == 'marketorders.deduped':
            try:
                # Each message may be a list of orders
                data = message['data']
                if isinstance(data, list):
                    for order_data in data:
                        order = MarketOrder(
                            item_id=order_data.get('ItemTypeId', ''),
                            location_id=order_data.get('LocationId', 0),
                            quality_level=order_data.get('QualityLevel', 1),
                            enchantment_level=order_data.get('EnchantmentLevel', 0),
                            unit_price_silver=order_data.get('UnitPriceSilver', 0),
                            amount=order_data.get('Amount', 0),
                            auction_type=order_data.get('AuctionType', ''),
                            expires=order_data.get('Expires', ''),
                            order_id=order_data.get('Id', ''),
                            timestamp=datetime.now(timezone.utc)
                        )
                        self.flip_detector.process_market_order(order)
                else:
                    order_data = data
                    order = MarketOrder(
                        item_id=order_data.get('ItemTypeId', ''),
                        location_id=order_data.get('LocationId', 0),
                        quality_level=order_data.get('QualityLevel', 1),
                        enchantment_level=order_data.get('EnchantmentLevel', 0),
                        unit_price_silver=order_data.get('UnitPriceSilver', 0),
                        amount=order_data.get('Amount', 0),
                        auction_type=order_data.get('AuctionType', ''),
                        expires=order_data.get('Expires', ''),
                        order_id=order_data.get('Id', ''),
                        timestamp=datetime.now(timezone.utc)
                    )
                    self.flip_detector.process_market_order(order)
            except Exception as e:
                logger.error(f"Error processing NATS market order: {e}")

    def setup_file_watcher(self):
        try:
            file_path = Path(self.file_path)
            if not file_path.exists():
                file_path.touch()
                logger.info(f"Created empty file: {self.file_path}")
            event_handler = FileWatcher(self.on_file_changed)
            self.file_observer = Observer()
            self.file_observer.schedule(
                event_handler,
                path=str(file_path.parent),
                recursive=False
            )
            self.file_observer.start()
            logger.info("File watcher started")
        except Exception as e:
            logger.error(f"Failed to setup file watcher: {e}")
            messagebox.showerror("File Watcher Error", f"Failed to monitor file changes: {e}")

    def on_file_changed(self):
        logger.info("items.txt has changed. Reloading item filters.")
        # Use 'after' to ensure this runs on the main GUI thread
        self.root.after(0, self.reload_item_filters)

    def on_closing(self):
        try:
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
            if self.event_loop and self.nats_client:
                # Wait for disconnect to finish before stopping the loop
                fut = asyncio.run_coroutine_threadsafe(
                    self.nats_client.disconnect(),
                    self.event_loop
                )
                try:
                    fut.result(timeout=5)  # Wait up to 5 seconds for disconnect
                except Exception as e:
                    # Suppress RuntimeError: Event loop stopped before Future completed (shutdown race)
                    if not (isinstance(e, RuntimeError) and 'Event loop stopped before Future completed' in str(e)):
                        logger.error(f"Error waiting for NATS disconnect: {e}")
            if self.event_loop:
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            self.root.destroy()
        except Exception as e:
            # Suppress RuntimeError: Event loop stopped before Future completed (shutdown race)
            if not (isinstance(e, RuntimeError) and 'Event loop stopped before Future completed' in str(e)):
                logger.error(f"Error during cleanup: {e}")
            self.root.destroy()

    def toggle_theme(self):
        # Always keep dark theme
        self.current_theme = 'dark'
        self.apply_theme()
        self.refresh_ui()

    def apply_theme(self):
        pass

    def change_font_size(self, value):
        try:
            self.current_font_size = int(value)
        except ValueError:
            pass

    def on_nats_server_change(self, value):
        """Handles NATS server selection change from the dropdown."""
        logger.info(f"User selected new NATS server: {value}. Triggering reconnect.")
        self.refresh_nats_server()

    def bind_shortcuts(self):
        # Bind Ctrl+L (both lowercase and uppercase) to show log window
        self.root.bind('<Control-l>', self.show_log_window)
        self.root.bind('<Control-L>', self.show_log_window)
        # Also bind globally to ensure it works even when other widgets have focus
        self.root.bind_all('<Control-l>', self.show_log_window)
        self.root.bind_all('<Control-L>', self.show_log_window)
        print("🔗 Keyboard shortcuts bound: Ctrl+L for debug logs")

    def test_shortcut(self, event=None):
        """Test method to verify keyboard shortcuts are working"""
        print("🎯 Test shortcut triggered!")
        messagebox.showinfo("Test", "Keyboard shortcut is working!")
        return "break"  # Prevent event propagation

    def create_tooltip(self, widget, text):
        # Simple tooltip for CTk widgets
        tip = tk.Toplevel(widget)
        tip.withdraw()
        tip.overrideredirect(True)
        label = tk.Label(tip, text=text, background="#232946", foreground="#00d4ff", font=("Segoe UI", 9), borderwidth=1, relief="solid")
        label.pack(ipadx=6, ipady=2)
        def enter(event):
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 2
            tip.geometry(f"+{x}+{y}")
            tip.deiconify()
        def leave(event):
            tip.withdraw()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def set_background_image(self):
        # Open a file dialog to select an image file
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=filetypes
        )
        if filepath:
            try:
                self._load_and_set_background_file(filepath)
            except Exception as e:
                self.show_error_popup(f"Failed to load background image from file.\nError: {e}")

    def _load_and_set_background_file(self, filepath):
        try:
            print(f"🖼️ Attempting to load background from file: {filepath}")
            im = Image.open(filepath).convert('RGBA')
            w, h = self.root.winfo_width(), self.root.winfo_height()
            if w < 100 or h < 100:
                w, h = 1600, 1000
            # Resize image to reasonable size to prevent memory issues
            max_size = 1920
            if im.width > max_size or im.height > max_size:
                ratio = min(max_size / im.width, max_size / im.height)
                new_width = int(im.width * ratio)
                new_height = int(im.height * ratio)
                im = im.resize((new_width, new_height), Image.Resampling.LANCZOS)
            im = im.resize((w, h), Image.Resampling.LANCZOS)
            # Add dark overlay for better text readability
            overlay = Image.new("RGBA", im.size, (20, 20, 30, 100))
            im = Image.alpha_composite(im, overlay)
            self.bg_image = im
            self.bg_image_tk = ctk.CTkImage(light_image=self.bg_image, dark_image=self.bg_image, size=(w,h))
            self.bg_url = filepath
            self.save_config()
            self.apply_background_image()
            self.refresh_ui()
            try:
                messagebox.showinfo("Success", "Background image loaded successfully!")
            except Exception as e:
                print(f"⚠️ Could not show success message: {e}")
        except Exception as e:
            print(f"❌ Error loading background from file: {e}")
            self.show_error_popup(f"Failed to load background image from file.\nError: {e}")

    def apply_background_image(self):
        try:
            print("🖼️ Starting apply_background_image...")
            if hasattr(self, 'bg_label') and self.bg_label:
                print("🗑️ Destroying old background label...")
                self.bg_label.destroy()
                self.bg_label = None
            if hasattr(self, 'bg_image_tk') and self.bg_image_tk:
                print("🖼️ Creating new background label...")
                self.bg_label = ctk.CTkLabel(self.root, image=self.bg_image_tk, text="")
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.bg_label.lower()
                print("✅ Background label created and placed")
            else:
                print("⚠️ No bg_image_tk available")
                if hasattr(self, 'bg_label') and self.bg_label:
                    self.bg_label.destroy()
                    self.bg_label = None
        except Exception as e:
            print(f"❌ Error in apply_background_image: {e}")
            # Don't crash the app, just log the error

    def on_resize(self, event):
        if self.bg_image is not None and self.bg_image_tk is not None:
            try:
                w, h = self.root.winfo_width(), self.root.winfo_height()
                self.bg_image_tk.configure(size=(w,h))
                self.apply_background_image()
            except Exception:
                pass

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = pyjson.load(f)
                self.bg_url = cfg.get("bg_url")
                if self.bg_url:
                    self.set_background_image_from_url(self.bg_url)
                
                # Load notification settings
                notifications_enabled = cfg.get("notifications_enabled", True)
                notification_min_profit = cfg.get("notification_min_profit", "200000")
                notification_cooldown = cfg.get("notification_cooldown", "10")
                
                self.notifications_enabled.set(notifications_enabled)
                self.notification_min_profit.set(notification_min_profit)
                self.notification_cooldown_var.set(notification_cooldown)
                
                # Load auto-updater settings
                auto_check_updates = cfg.get("auto_check_updates", True)
                if hasattr(self, 'auto_check_updates'):
                    self.auto_check_updates.set(auto_check_updates)
                self.auto_updater.enabled = cfg.get("updater_enabled", True)
                
                print(f"✅ Loaded notification settings: enabled={notifications_enabled}, min_profit={notification_min_profit}, cooldown={notification_cooldown}s")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            # Use defaults if config file doesn't exist or is corrupted
            pass

    def save_config(self):
        try:
            config_data = {
                "bg_url": self.bg_url,
                "notifications_enabled": self.notifications_enabled.get(),
                "notification_min_profit": self.notification_min_profit.get(),
                "notification_cooldown": self.notification_cooldown_var.get(),
                "auto_check_updates": self.auto_check_updates.get() if hasattr(self, 'auto_check_updates') else True,
                "updater_enabled": self.auto_updater.enabled
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                pyjson.dump(config_data, f)
            print("✅ Settings saved successfully")
        except Exception as e:
            print(f"❌ Error saving settings: {e}")

    def set_background_image_from_url(self, url):
        try:
            with urllib.request.urlopen(url) as u:
                raw_data = u.read()
            image = Image.open(io.BytesIO(raw_data)).convert("RGBA")
            w, h = self.root.winfo_width(), self.root.winfo_height()
            if w < 100 or h < 100:
                w, h = 1600, 1000
            image = image.resize((w, h), Image.Resampling.LANCZOS)
            overlay = Image.new("RGBA", image.size, (20, 20, 30, 180))
            image = Image.alpha_composite(image, overlay)
            self.bg_image = image
            self.bg_image_tk = ctk.CTkImage(light_image=self.bg_image, dark_image=self.bg_image, size=(w,h))
            self.apply_background_image()
            self.refresh_ui()
        except Exception:
            self.bg_image = None
            self.bg_image_tk = None
            self.apply_background_image()
            self.refresh_ui()

    def open_theme_picker(self):
        picker = tk.Toplevel(self.root)
        picker.title("Pick Font Color")
        picker.geometry("340x120")
        picker.configure(bg="#181c24")  # black background
        picker.attributes('-topmost', True)
        picker.attributes('-alpha', 0.0)
        picker.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 340) // 2
        y = self.root.winfo_y() + 120
        picker.geometry(f"340x120+{x}+{y+40}")
        def slide_and_fade(alpha=0.0, dy=40):
            if alpha < 1.0 or dy > 0:
                picker.attributes('-alpha', min(1.0, alpha))
                picker.geometry(f"340x120+{x}+{y+dy}")
                picker.after(12, lambda: slide_and_fade(alpha + 0.08, max(0, dy - 4)))
            else:
                picker.attributes('-alpha', 1.0)
                picker.geometry(f"340x120+{x}+{y}")
        slide_and_fade()
        label = ctk.CTkLabel(picker, text="Choose Font Color:", font=MODERN_FONT, text_color="#fafafa")
        label.pack(pady=8)
        colors = ["#f8f8f2", "#ffeb3b", "#ff4b91", "#00d4ff", "#00ff99", "#ffb300", "#a259ff", "#ff5757", "#00b894"]
        btns = []
        def set_color(c):
            self.current_font_color = c
            self.apply_background_image()
            self.refresh_ui()
            self.theme_btn.configure(text_color=c)
            picker.destroy()
        for i, c in enumerate(colors):
            b = AnimatedButton(picker, text="", width=36, height=36, fg_color=c, corner_radius=18, command=lambda c=c: set_color(c))
            b.pack(side="left", padx=8, pady=8)
            btns.append(b)

    def refresh_ui(self):
        if self._refreshing_ui:
            print("⚠️ refresh_ui already in progress, skipping...")
            return
        
        self._refreshing_ui = True
        try:
            print("🎨 Starting refresh_ui...")
            is_bg_active = self.bg_image is not None
            palette = self.get_palette()
            def is_light(color):
                color = color.lstrip('#')
                r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                luminance = (0.299*r + 0.587*g + 0.114*b)/255
                return luminance > 0.7
            font_color = self.current_font_color
            if font_color.lower() in ['#f8f8f2', '#ffffff', '#fff', '#fffffe', '#fafafa', '#f7f7f7'] or is_light(font_color):
                font_color = '#e0e0e0'
            
            bg_color = palette['panel']
            if is_bg_active:
                bg_color = "transparent"

            if is_light(font_color) and is_light(bg_color):
                bg_color = '#232946'
            
            print("🎨 Updating themed widgets...")
            for widget in self._themed_widgets:
                try:
                    if isinstance(widget, ctk.CTkFrame):
                        widget.configure(fg_color=bg_color)
                    elif isinstance(widget, ctk.CTkLabel):
                        widget.configure(text_color=font_color)
                    elif isinstance(widget, AnimatedButton):
                        widget.configure(text_color=font_color)
                        widget.configure(fg_color=palette['button_fg'])
                        widget._fg_normal = palette['button_fg']
                        widget._fg_hover = widget._darker(palette['button_fg'], 0.85)
                        widget._fg_press = widget._darker(palette['button_fg'], 0.7)
                        widget._animate_hover(widget._hovered)
                    elif isinstance(widget, ctk.CTkComboBox):
                        widget.configure(fg_color=bg_color, text_color=font_color)
                except Exception as e:
                    print(f"⚠️ Error updating widget: {e}")
                    continue
            
            print("🎨 Updating treeview style...")
            style = ttk.Style()
            
            tree_bg = palette['tree_bg']
            tree_even = palette['tree_even']
            if is_bg_active:
                tree_bg = "transparent"
                tree_even = "transparent"

            style.configure('Custom.Treeview',
                            background=tree_bg,
                            fieldbackground=tree_bg,
                            foreground=font_color,
                            rowheight=30)
            style.configure('Custom.Treeview.Heading',
                            background=palette['tree_header'],
                            foreground=font_color,
                            font=TABLE_HEADER_FONT)
            self.tree.tag_configure('oddrow', background=tree_bg, foreground=font_color)
            self.tree.tag_configure('evenrow', background=tree_even, foreground=font_color)
            style.map('Custom.Treeview',
                      background=[('selected', palette['accent']), ('active', bg_color)],
                      foreground=[('selected', font_color), ('active', palette['accent'])])
            
            print("🎨 Updating root background...")
            self.root.configure(bg=palette['bg'])
            self.root.update_idletasks()
            
            if hasattr(self, 'connection_label'):
                self.connection_label.configure(text_color=font_color)
            
            # Don't call apply_background_image here to prevent infinite loop
            print("✅ refresh_ui completed successfully!")

            # Schedule the update to ensure all style changes are processed first
            self.root.after(50, self._update_results_display)
            
        except Exception as e:
            print(f"❌ Error in refresh_ui: {e}")
            # Don't crash the app, just log the error
        finally:
            self._refreshing_ui = False

    def show_error_popup(self, message):
        messagebox.showerror("Error", message)

    def get_palette(self):
        return DARK_PALETTE

    def refresh_nats_server(self):
        """Forces a disconnection and reconnection to the selected NATS server."""
        if not (self.event_loop and self.nats_client):
            logger.warning("Cannot refresh NATS server: event loop or client not ready.")
            return

        logger.info(f"Refresh requested. Reconnecting to NATS server: {self.selected_nats_region.get()}")

        async def do_reconnect():
            # Update UI to show reconnecting status
            def update_status():
                self.connection_label.configure(text="🟡 Reconnecting...", text_color="orange")
            self.root.after(0, update_status)
            
            await self.nats_client.disconnect()
            await self.connect_nats()

        asyncio.run_coroutine_threadsafe(do_reconnect(), self.event_loop)

    def run_full_scan(self):
        """Runs a full scan on all collected data and updates the UI."""
        logger.info("Running full scan for flip opportunities...")
        
        # Clear the old log and run the scan
        self.scan_log.clear()
        all_found_opportunities = self.flip_detector.scan_for_all_flips(self.scan_log)
        
        # We can just replace the current list with the full scan result
        self.flip_opportunities = all_found_opportunities
        
        logger.info(f"Full scan found {len(self.flip_opportunities)} total opportunities.")
        
        # Prune the list to keep only the best flips
        is_premium = self.premium_var.get()
        tax_rate = 0.065 if is_premium else 0.105
        self.flip_opportunities.sort(key=lambda opp: int((opp.profit) - (opp.bm_price * tax_rate)), reverse=True)
        self.flip_opportunities = self.flip_opportunities[:self.MAX_OPPORTUNITIES]

        logger.info(f"Pruned opportunity list to top {len(self.flip_opportunities)} flips.")
        
        # Re-sort and update the display
        self.sort_by_column(self.sort_column, self.sort_reverse, toggle=False)
        # Update status bar
        now = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"Full scan at {now} found {len(self.flip_opportunities)} total flips.")

    def reload_item_filters(self):
        """Reloads items from items.txt and updates the flip detector filters."""
        logger.info("Reloading item filters from items.txt...")
        base_items = self.item_manager.load_items_from_file(self.file_path)
        
        all_item_ids = set() # Use a set to avoid duplicates
        for item in base_items:
            item_id = item.lower().strip()
            all_item_ids.add(item_id)
            
            # The new items.txt format seems to include enchanted items explicitly.
            # This logic can be a fallback.
            if '@' not in item_id and '.' not in item_id:
                for enchant in range(1, 5):
                    all_item_ids.add(f"{item_id}@{enchant}")
        
        all_cities = ['Brecilien', 'Bridgewatch', 'Lymhurst', 'Fort Sterling', 'Thetford', 'Martlock', 'Caerleon']
        self.flip_detector.set_filters(list(all_item_ids), all_cities)
        
        logger.info(f"Filters updated. {len(all_item_ids)} item variants loaded.")
        self.status_var.set(f"Loaded {len(base_items)} base items. Watching {len(all_item_ids)} variants.")

    def _on_new_opportunity(self, opportunity):
        """Adds a new opportunity to a batch and schedules a single UI update."""
        if self.debug_enabled:
            logger.info(f"Real-time opportunity detected: {opportunity.item_name} in {opportunity.city}")
        
        # Check for high profit notification
        self.check_and_notify_high_profit(opportunity)
        
        # Add to batch
        self.opportunity_batch.append(opportunity)
        
        # Log to debug log if enabled
        if self.debug_enabled:
            is_premium = self.premium_var.get()
            tax_rate = 0.065 if is_premium else 0.105
            profit_after_tax = int(opportunity.profit - (opportunity.bm_price * tax_rate))
            self.opportunity_batch_debug_log.appendleft(
                f"[{datetime.now().strftime('%H:%M:%S')}] New opportunity: "
                f"{opportunity.item_name} in {opportunity.city} - Profit: {profit_after_tax:,}"
            )
        
        # Schedule batch processing if not already scheduled
        if not self._update_scheduled:
            self._update_scheduled = True
            # Use a longer delay for better performance (increased from 100ms to 200ms)
            self._update_job_id = self.root.after(200, self._process_opportunity_batch)
            
        # Schedule UI update with longer delay for better performance
        if not hasattr(self, '_ui_update_scheduled') or not self._ui_update_scheduled:
            self._ui_update_scheduled = True
            self.root.after(100, self._update_ui_after_delay)

    def _update_ui_after_delay(self):
        """Update the UI with a small delay to prevent freezing."""
        self._update_results_display()
        self._ui_update_scheduled = False

    def _process_opportunity_batch(self):
        """Processes the batch of new opportunities and updates the UI."""
        try:
            batch_size = len(self.opportunity_batch)
            if batch_size == 0:
                return
                
            if self.debug_enabled:
                logger.info(f"Processing batch of {batch_size} opportunities.")
                self.opportunity_batch_debug_log.appendleft(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Processing {batch_size} opportunities. "
                    f"Total before: {len(self.flip_opportunities)}"
                )

            # Process batch
            if self.opportunity_batch:
                # Use a dictionary for faster lookups to update existing items
                existing_flips = {}
                
                # First add all existing opportunities
                for opp in self.flip_opportunities:
                    key = (opp.item_name, opp.city, opp.bm_quality)
                    existing_flips[key] = opp
                
                # Then update with new opportunities
                while self.opportunity_batch:
                    opportunity = self.opportunity_batch.popleft()
                    key = (opportunity.item_name, opportunity.city, opportunity.bm_quality)
                    existing_flips[key] = opportunity
                
                # Convert back to list
                self.flip_opportunities = list(existing_flips.values())

            # Only keep the most recent flips to maintain performance
            if len(self.flip_opportunities) > self.MAX_OPPORTUNITIES:
                # Sort by time to keep the most recent flips, then apply user's sort
                current_time = datetime.now(timezone.utc)
                min_time = datetime.min.replace(tzinfo=timezone.utc)
                
                def time_sort_key(opp):
                    # Time since update in minutes (negative for descending)
                    time_since_update = -int((current_time - (opp.last_update if opp.last_update else min_time)).total_seconds() / 60)
                    return time_since_update
                
                # Sort by time to get the most recent flips
                self.flip_opportunities.sort(key=time_sort_key)
                self.flip_opportunities = self.flip_opportunities[:self.MAX_OPPORTUNITIES]

            # Update status bar
            now = datetime.now().strftime("%H:%M:%S")
            self.status_var.set(f"Processed {batch_size} updates at {now}. Displaying {len(self.flip_opportunities)} flips.")
            
            # Update display
            self._update_results_display()
            
        except Exception as e:
            logger.error(f"Error in _process_opportunity_batch: {e}")
            if self.debug_enabled:
                import traceback
                self.opportunity_batch_debug_log.appendleft(
                    f"[ERROR] {datetime.now().strftime('%H:%M:%S')} {str(e)}\n{traceback.format_exc()}"
                )
        finally:
            # Always reset these flags, even if there was an error
            self._update_scheduled = False
            self._update_job_id = None

    def _apply_current_sort(self):
        """Apply the current sort without triggering UI update or changing sort indicators."""
        if not hasattr(self, 'sort_column') or not hasattr(self, 'sort_reverse'):
            return
            
        col = self.sort_column
        reverse = self.sort_reverse
        
        # Map column name to data attribute
        col_map = {
            'Item': 'item_name',
            'Quality': 'bm_quality',
            'Buy City': 'city',
            'Buy Price': 'city_price',
            'Sell Price': 'bm_price',
            'Qty': 'quantity',
            'Volume': 'volume',
            'Price Age': 'price_age',
            'Done': 'flip_id', # To sort by completed status
        }
        
        data_key = col_map.get(col)
        
        # Sort the data
        try:
            is_premium = self.premium_var.get()
            tax_rate = 0.065 if is_premium else 0.105

            if col == 'Profit':
                self.flip_opportunities.sort(key=lambda opp: int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate)), reverse=reverse)
            elif col == 'Total Profit':
                self.flip_opportunities.sort(key=lambda opp: opp.quantity * int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate)), reverse=reverse)
            elif col == 'ROI%':
                self.flip_opportunities.sort(key=lambda opp: ((int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate))) / opp.city_price * 100) if opp.city_price > 0 else 0, reverse=reverse)
            # Special handling for 'Status'/'Done'
            elif data_key == 'flip_id':
                self.flip_opportunities.sort(key=lambda opp: opp.flip_id in self.completed_flips, reverse=reverse)
            elif col == 'Price Age':
                # Sort by the maximum age between BM and city prices (smallest first)
                self.flip_opportunities.sort(key=lambda opp: max(
                    (datetime.now(timezone.utc) - self.flip_detector.bm_price_data.get((opp.item_name, opp.bm_quality), {}).get('Black Market', {}).get('last_update', datetime.min.replace(tzinfo=timezone.utc))).total_seconds(),
                    (datetime.now(timezone.utc) - self.flip_detector.city_price_data.get(opp.item_name, {}).get(opp.city, {}).get(opp.city_quality, {}).get('last_update', datetime.min.replace(tzinfo=timezone.utc))).total_seconds()
                ), reverse=not reverse)
            elif data_key:
                self.flip_opportunities.sort(key=lambda opp: getattr(opp, data_key), reverse=reverse)
            else:
                return  # Column not sortable

        except AttributeError as e:
            logger.error(f"Cannot sort by attribute '{data_key}': {e}")
            return

    def sort_by_column(self, col, reverse, toggle=True):
        """Sort treeview by a column."""
        # Map column name to data attribute
        col_map = {
            'Item': 'item_name',
            'Quality': 'bm_quality',
            'Buy City': 'city',
            'Buy Price': 'city_price',
            'Sell Price': 'bm_price',
            'Qty': 'quantity',
            'Volume': 'volume',
            'Price Age': 'price_age',
            'Done': 'flip_id', # To sort by completed status
        }
        
        data_key = col_map.get(col)
        
        # Toggle sort direction if the same column is clicked again
        if toggle:
            if self.sort_column == col:
                self.sort_reverse = not reverse
            else:
                self.sort_column = col
                self.sort_reverse = False  # Default to ascending for new columns
        
        # Apply the sort
        self._apply_current_sort()

        # Update sort indicators in header
        for c in self.tree['columns']:
            self.tree.heading(c, text=c)  # Reset all headers
            
        arrow = ' ▼' if self.sort_reverse else ' ▲'
        self.tree.heading(col, text=col + arrow)
        
        # Schedule UI update in the main thread
        self.root.after(0, self._update_results_display)

    def on_tree_click(self, event):
        """Handle clicks inside the treeview, specifically for the 'Done' column."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col_id = self.tree.identify_column(event.x)
        # In testing, headings can have leading spaces. strip() is safer.
        col_text = self.tree.heading(col_id, "text").strip()
        
        if col_text.startswith("Done"): # Check if it's the 'Done' column (might have sort arrow)
            row_id = self.tree.identify_row(event.y)
            if row_id:
                self.tree.selection_set(row_id) # Select the row that was clicked
                self.mark_completed() # Use the existing toggle logic

    def show_log_window(self, event: object = None) -> None:
        """Show the debug/log window with multiple tabs, including filter debug and test item."""
        # Enable debug logging when window opens
        self.debug_enabled = False
        self.debug_window_open = True
        
        log_win = tk.Toplevel(self.root)
        log_win.title("Debug / NATS Info")
        log_win.geometry("900x500")
        log_win.attributes('-alpha', 0.0)
        log_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 900) // 2
        y = self.root.winfo_y() + 60
        log_win.geometry(f"900x500+{x}+{y-40}")
        def slide_and_fade(alpha=0.0, dy=40):
            if alpha < 1.0 or dy > 0:
                log_win.attributes('-alpha', min(1.0, alpha))
                log_win.geometry(f"900x500+{x}+{y-dy}")
                log_win.after(12, lambda: slide_and_fade(alpha + 0.08, max(0, dy - 4)))
            else:
                log_win.attributes('-alpha', 1.0)
                log_win.geometry(f"900x500+{x}+{y}")
        slide_and_fade()
        
        # Handle window close to disable debug logging
        def on_debug_window_close():
            self.debug_enabled = False
            self.debug_window_open = False
            log_win.destroy()
        
        log_win.protocol("WM_DELETE_WINDOW", on_debug_window_close)
        notebook = ttk.Notebook(log_win)
        notebook.pack(fill="both", expand=True)
        # --- Restore create_log_tab function at the top ---
        def create_log_tab(title: str, log_source: deque, fg: str) -> tk.Frame:
            frame = tk.Frame(notebook)
            text = tk.Text(frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg=fg)
            text.pack(fill="both", expand=True)
            def update_tab():
                text.config(state="normal")
                text.delete("1.0", "end")
                for msg in list(log_source):
                    text.insert("end", str(msg) + "\n\n")
                text.config(state="disabled")
                # Only update if debug window is still open
                if self.debug_window_open:
                    text.after(1000, update_tab)
            update_tab()
            notebook.add(frame, text=title)
            return frame
        # --- REMOVE Analytics Tab from log window ---
        # Logs tab
        log_frame = tk.Frame(notebook)
        log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg="#00d4ff")
        log_text.pack(fill="both", expand=True)
        try:
            with open('item_monitor.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-200:]
                log_text.insert("end", ''.join(lines))
        except Exception as e:
            log_text.insert("end", f"Could not read log: {e}\n")
        log_text.config(state="disabled")
        notebook.add(log_frame, text="📝  Logs")
        # NATS Data tab
        nats_frame = tk.Frame(notebook)
        nats_text = tk.Text(nats_frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg="#00ff99")
        nats_text.pack(fill="both", expand=True)
        def copy_nats():
            self.root.clipboard_clear()
            self.root.clipboard_append(nats_text.get("1.0", "end"))
        copy_btn = tk.Button(nats_frame, text="Copy All", command=copy_nats)
        copy_btn.pack(anchor="ne", padx=8, pady=4)
        def update_nats_tab():
            nats_text.config(state="normal")
            nats_text.delete("1.0", "end")
            for msg in list(self.nats_data_buffer):
                nats_text.insert("end", msg + "\n\n")
            nats_text.config(state="disabled")
            # Only update if debug window is still open
            if self.debug_window_open:
                nats_text.after(1000, update_nats_tab)
        update_nats_tab()
        notebook.add(nats_frame, text="🌐  NATS Data")
        # Flip Debug tab
        create_log_tab("🔎 Flip Debug", self.flip_detector.flip_debug_log, "#ffeb3b")
        # Opportunity Batch tab with manual controls
        opp_batch_frame = tk.Frame(notebook)
        opp_batch_text = tk.Text(opp_batch_frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg="#ffb300")
        opp_batch_text.pack(fill="both", expand=True)
        
        # Button frame for opportunity batch controls
        opp_btn_frame = ctk.CTkFrame(opp_batch_frame, fg_color="#181c24")
        opp_btn_frame.pack(fill="x", padx=8, pady=4)
        
        def clear_opp_batch_log():
            self.opportunity_batch_debug_log.clear()
        
        tk.Button(opp_btn_frame, text="Clear Log", command=clear_opp_batch_log, bg="#232946", fg="#ffb300", font=("Consolas", 10, "bold")).pack(side="left", padx=4)
        
        def update_opp_batch_tab():
            opp_batch_text.config(state="normal")
            opp_batch_text.delete("1.0", "end")
            for msg in list(self.opportunity_batch_debug_log):
                opp_batch_text.insert("end", msg + "\n\n")
            opp_batch_text.config(state="disabled")
            # Only update if debug window is still open
            if self.debug_window_open:
                opp_batch_text.after(1000, update_opp_batch_tab)
        update_opp_batch_tab()
        notebook.add(opp_batch_frame, text="📦 Opportunity Batch")
        
        # Scan Log tab with manual controls
        scan_frame = tk.Frame(notebook)
        scan_text = tk.Text(scan_frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg="#673ab7")
        scan_text.pack(fill="both", expand=True)
        
        # Button frame for scan log controls
        scan_btn_frame = ctk.CTkFrame(scan_frame, fg_color="#181c24")
        scan_btn_frame.pack(fill="x", padx=8, pady=4)
        
        def clear_scan_log():
            self.scan_log.clear()
        
        tk.Button(scan_btn_frame, text="Clear Log", command=clear_scan_log, bg="#232946", fg="#673ab7", font=("Consolas", 10, "bold")).pack(side="left", padx=4)
        
        def update_scan_tab():
            scan_text.config(state="normal")
            scan_text.delete("1.0", "end")
            for msg in list(self.scan_log):
                scan_text.insert("end", msg + "\n\n")
            scan_text.config(state="disabled")
            scan_text.after(1000, update_scan_tab)
        update_scan_tab()
        notebook.add(scan_frame, text="📜 Scan Log")
        
        # Price Data tab
        price_frame = tk.Frame(notebook)
        price_summary_var = tk.StringVar()
        ctk.CTkLabel(price_frame, textvariable=price_summary_var, font=("Segoe UI", 11, "bold"), text_color="#a259ff").pack(anchor="nw", padx=8, pady=4)
        price_text = tk.Text(price_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#a259ff")
        price_text.pack(fill="both", expand=True)

        def reload_price_data():
            city_price_data = self.flip_detector.city_price_data
            bm_price_data = self.flip_detector.bm_price_data
            
            # Create summary
            total_city_items = len(city_price_data)
            total_bm_items = len(bm_price_data)
            
            # Count items with actual black market buy prices
            items_with_bm_buy = 0
            for item_key, bm_data in bm_price_data.items():
                if bm_data.get('Black Market', {}).get('buy_price') is not None:
                    items_with_bm_buy += 1
            
            summary = f"City Items: {total_city_items} | BM Items: {total_bm_items} | Items with BM Buy Prices: {items_with_bm_buy}"
            price_summary_var.set(summary)

            # Format data for display - combine both data sources
            combined_data = {
                'city_price_data': {str(k): v for k, v in city_price_data.items()},
                'bm_price_data': {str(k): v for k, v in bm_price_data.items()}
            }
            
            price_text.config(state="normal")
            price_text.delete("1.0", "end")
            try:
                pretty_data = pyjson.dumps(combined_data, indent=2, default=str)
                price_text.insert("end", pretty_data)
            except Exception as e:
                price_text.insert("end", f"Error formatting price data: {e}")
            price_text.config(state="disabled")

        reload_btn = tk.Button(price_frame, text="Reload Data", command=reload_price_data, bg="#232946", fg="#a259ff", font=("Consolas", 10, "bold"))
        reload_btn.pack(anchor="ne", padx=8, pady=2)
        reload_price_data() # Initial load
        notebook.add(price_frame, text="📈 Price Data")

        # Black Market Data tab
        bm_frame = tk.Frame(notebook)
        bm_summary_var = tk.StringVar()
        ctk.CTkLabel(bm_frame, textvariable=bm_summary_var, font=("Segoe UI", 11, "bold"), text_color="#ff6b6b").pack(anchor="nw", padx=8, pady=4)
        bm_text = tk.Text(bm_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#ff6b6b")
        bm_text.pack(fill="both", expand=True)

        def reload_bm_data():
            bm_price_data = self.flip_detector.bm_price_data
            
            # Create summary
            total_bm_items = len(bm_price_data)
            items_with_buy_prices = 0
            total_buy_amount = 0
            
            for item_key, bm_data in bm_price_data.items():
                if bm_data.get('Black Market', {}).get('buy_price') is not None:
                    items_with_buy_prices += 1
                    total_buy_amount += bm_data.get('Black Market', {}).get('buy_amount', 0)
            
            summary = f"BM Items: {total_bm_items} | With Buy Prices: {items_with_buy_prices} | Total Buy Amount: {total_buy_amount:,}"
            bm_summary_var.set(summary)

            # Format data for display
            printable_bm_data = {str(k): v for k, v in bm_price_data.items()}
            bm_text.config(state="normal")
            bm_text.delete("1.0", "end")
            try:
                pretty_data = pyjson.dumps(printable_bm_data, indent=2, default=str)
                bm_text.insert("end", pretty_data)
            except Exception as e:
                bm_text.insert("end", f"Error formatting BM data: {e}")
            bm_text.config(state="disabled")

        bm_reload_btn = tk.Button(bm_frame, text="Reload BM Data", command=reload_bm_data, bg="#232946", fg="#ff6b6b", font=("Consolas", 10, "bold"))
        bm_reload_btn.pack(anchor="ne", padx=8, pady=2)
        reload_bm_data() # Initial load
        notebook.add(bm_frame, text="🖤 Black Market Data")

        # City Data tab
        city_frame = tk.Frame(notebook)
        city_summary_var = tk.StringVar()
        ctk.CTkLabel(city_frame, textvariable=city_summary_var, font=("Segoe UI", 11, "bold"), text_color="#4ecdc4").pack(anchor="nw", padx=8, pady=4)
        city_text = tk.Text(city_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#4ecdc4")
        city_text.pack(fill="both", expand=True)

        def reload_city_data():
            city_price_data = self.flip_detector.city_price_data
            
            # Create summary
            total_city_items = len(city_price_data)
            total_cities = 0
            total_sell_orders = 0
            
            for item_id, city_dict in city_price_data.items():
                for city_name, qualities in city_dict.items():
                    total_cities += 1
                    for quality, data in qualities.items():
                        if data.get('sell_price') is not None:
                            total_sell_orders += 1
            
            summary = f"City Items: {total_city_items} | Total Cities: {total_cities} | Sell Orders: {total_sell_orders}"
            city_summary_var.set(summary)

            # Format data for display
            printable_city_data = {str(k): v for k, v in city_price_data.items()}
            city_text.config(state="normal")
            city_text.delete("1.0", "end")
            try:
                pretty_data = pyjson.dumps(printable_city_data, indent=2, default=str)
                city_text.insert("end", pretty_data)
            except Exception as e:
                city_text.insert("end", f"Error formatting city data: {e}")
            city_text.config(state="disabled")

        city_reload_btn = tk.Button(city_frame, text="Reload City Data", command=reload_city_data, bg="#232946", fg="#4ecdc4", font=("Consolas", 10, "bold"))
        city_reload_btn.pack(anchor="ne", padx=8, pady=2)
        reload_city_data() # Initial load
        notebook.add(city_frame, text="🏙️ City Data")

        # Summary tab
        summary_frame = tk.Frame(notebook)
        summary_text = tk.Text(summary_frame, wrap="word", font=("Consolas", 11), bg="#181c24", fg="#ffffff")
        summary_text.pack(fill="both", expand=True)

        def reload_summary():
            city_price_data = self.flip_detector.city_price_data
            bm_price_data = self.flip_detector.bm_price_data
            
            summary_text.config(state="normal")
            summary_text.delete("1.0", "end")
            
            # Calculate statistics
            total_city_items = len(city_price_data)
            total_bm_items = len(bm_price_data)
            
            # City statistics
            city_stats = {}
            total_city_orders = 0
            for item_id, city_dict in city_price_data.items():
                for city_name, qualities in city_dict.items():
                    if city_name not in city_stats:
                        city_stats[city_name] = {'items': 0, 'orders': 0}
                    city_stats[city_name]['items'] += 1
                    for quality, data in qualities.items():
                        if data.get('sell_price') is not None:
                            city_stats[city_name]['orders'] += 1
                            total_city_orders += 1
            
            # Black Market statistics
            bm_items_with_prices = 0
            total_bm_amount = 0
            bm_quality_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for item_key, bm_data in bm_price_data.items():
                if bm_data.get('Black Market', {}).get('buy_price') is not None:
                    bm_items_with_prices += 1
                    total_bm_amount += bm_data.get('Black Market', {}).get('buy_amount', 0)
                    # Extract quality from item_key (item_key is a tuple: (item_id, quality))
                    if isinstance(item_key, tuple) and len(item_key) == 2:
                        quality = item_key[1]
                        if quality in bm_quality_stats:
                            bm_quality_stats[quality] += 1
            
            # Display summary
            summary_text.insert("end", "=== RAT FLIPPER PRO DATA SUMMARY ===\n\n")
            summary_text.insert("end", f"📊 OVERALL STATISTICS:\n")
            summary_text.insert("end", f"• Total City Items Tracked: {total_city_items:,}\n")
            summary_text.insert("end", f"• Total Black Market Items Tracked: {total_bm_items:,}\n")
            summary_text.insert("end", f"• Black Market Items with Buy Prices: {bm_items_with_prices:,}\n")
            summary_text.insert("end", f"• Total City Sell Orders: {total_city_orders:,}\n")
            summary_text.insert("end", f"• Total Black Market Buy Amount: {total_bm_amount:,}\n\n")
            
            summary_text.insert("end", f"🏙️ CITY BREAKDOWN:\n")
            for city, stats in sorted(city_stats.items()):
                summary_text.insert("end", f"• {city}: {stats['items']} items, {stats['orders']} sell orders\n")
            
            summary_text.insert("end", f"\n🖤 BLACK MARKET QUALITY BREAKDOWN:\n")
            for quality, count in sorted(bm_quality_stats.items()):
                quality_name = QUALITY_LEVEL_NAMES.get(quality, f"Q{quality}")
                summary_text.insert("end", f"• {quality_name}: {count} items with buy prices\n")
            
            summary_text.insert("end", f"\n⏰ LAST UPDATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary_text.config(state="disabled")

        summary_reload_btn = tk.Button(summary_frame, text="Refresh Summary", command=reload_summary, bg="#232946", fg="#ffffff", font=("Consolas", 10, "bold"))
        summary_reload_btn.pack(anchor="ne", padx=8, pady=2)
        reload_summary() # Initial load
        notebook.add(summary_frame, text="📊 Summary")

        # Filter Debug tab with summary, test item, and clear log
        filter_frame = tk.Frame(notebook)
        summary_var = tk.StringVar()
        summary_label = ctk.CTkLabel(filter_frame, textvariable=summary_var, font=("Segoe UI", 11, "bold"), text_color="#00ff99")
        summary_label.pack(anchor="nw", padx=8, pady=4)
        filter_text = tk.Text(filter_frame, wrap="word", font=("Consolas", 10), bg="#181c24", fg="#00ff99", height=18)
        filter_text.pack(fill="both", expand=True, padx=4)
        def update_filter_tab():
            filter_text.config(state="normal")
            filter_text.delete("1.0", "end")
            checked = matched = skipped = 0
            for msg in list(self.flip_detector.filter_debug_log):
                filter_text.insert("end", msg + "\n\n")
                checked += 1
                if "not in filters, skipping" in msg:
                    skipped += 1
                elif "Checking item" in msg:
                    pass
                else:
                    matched += 1
            summary_var.set(f"Checked: {checked} | Matched: {checked-skipped} | Skipped: {skipped}")
            filter_text.config(state="disabled")
            filter_text.after(1000, update_filter_tab)
        update_filter_tab()
        # Test Item field
        test_frame = ctk.CTkFrame(filter_frame, fg_color="#181c24")
        test_frame.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(test_frame, text="Test Item ID:", font=("Segoe UI", 10), text_color="#00ff99").pack(side="left")
        test_entry = tk.Entry(test_frame, font=("Consolas", 10), bg="#232946", fg="#00ff99", width=32)
        test_entry.pack(side="left", padx=6)
        test_result = ctk.CTkLabel(test_frame, text="", font=("Segoe UI", 10, "bold"))
        test_result.pack(side="left", padx=8)
        def check_test_item(*_):
            val = test_entry.get().lower().strip()
            if not val:
                test_result.config(text="", fg="#00ff99")
                return
            if val in self.flip_detector.item_filters:
                test_result.config(text="✔ In Filter", fg="#00ff99")
            else:
                test_result.config(text="✖ Not in Filter", fg="#ff4b91")
        test_entry.bind("<KeyRelease>", check_test_item)
        # Clear Log button
        def clear_filter_log():
            self.flip_detector.filter_debug_log.clear()
        clear_btn = tk.Button(filter_frame, text="Clear Log", command=clear_filter_log, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold"))
        clear_btn.pack(anchor="ne", padx=8, pady=2)
        notebook.add(filter_frame, text="🧩 Filter Debug")
        log_win.focus()
        # Filter Set tab (shows all item IDs in the filter, with names)
        filter_set_frame = tk.Frame(notebook)
        filter_set_text = tk.Text(filter_set_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#00ff99")
        filter_set_text.pack(fill="both", expand=True)
        def get_item_name(item_id):
            # Use item_manager to get the display name
            return self.item_manager.get_display_name(item_id)
        def reload_filter_set():
            filter_set_text.config(state="normal")
            filter_set_text.delete("1.0", "end")
            for item_id in sorted(self.flip_detector.item_filters):
                name = get_item_name(item_id)
                filter_set_text.insert("end", f"{item_id}  :  {name}\n")
            filter_set_text.config(state="disabled")
        reload_btn = tk.Button(filter_set_frame, text="Reload", command=reload_filter_set, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold"))
        reload_btn.pack(anchor="ne", padx=8, pady=2)
        reload_filter_set()
        notebook.add(filter_set_frame, text="📋 Filter Set")
        
        # Enchanting Debug tabs
        enchanting_debug_frame = tk.Frame(notebook)
        enchanting_debug_text = tk.Text(enchanting_debug_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#00ff99")
        enchanting_debug_text.pack(fill="both", expand=True)
        def update_enchanting_debug_tab():
            enchanting_debug_text.config(state="normal")
            enchanting_debug_text.delete("1.0", "end")
            if hasattr(self, 'enchanting_debug_log'):
                for log_entry in list(self.enchanting_debug_log)[:100]:  # Show last 100 entries
                    enchanting_debug_text.insert("end", log_entry + "\n")
            else:
                enchanting_debug_text.insert("end", "No enchanting debug log found.\n")
            enchanting_debug_text.config(state="disabled")
            enchanting_debug_text.see("end")
        update_btn = tk.Button(enchanting_debug_frame, text="Update", command=update_enchanting_debug_tab, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold"))
        update_btn.pack(anchor="ne", padx=8, pady=2)
        update_enchanting_debug_tab()
        # Auto-update every 2 seconds if debug window is open
        if self.debug_window_open:
            self.root.after(2000, lambda: update_enchanting_debug_tab() if self.debug_window_open else None)
        notebook.add(enchanting_debug_frame, text="✨ Enchanting Debug")
        
        # Enchanting Raw Debug tab
        enchanting_raw_debug_frame = tk.Frame(notebook)
        enchanting_raw_debug_text = tk.Text(enchanting_raw_debug_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#00ff99")
        enchanting_raw_debug_text.pack(fill="both", expand=True)
        def update_enchanting_raw_debug_tab():
            enchanting_raw_debug_text.config(state="normal")
            enchanting_raw_debug_text.delete("1.0", "end")
            if hasattr(self, 'enchanting_raw_debug_log'):
                for log_entry in list(self.enchanting_raw_debug_log)[:100]:  # Show last 100 entries
                    enchanting_raw_debug_text.insert("end", log_entry + "\n")
            else:
                enchanting_raw_debug_text.insert("end", "No enchanting raw debug log found.\n")
            enchanting_raw_debug_text.config(state="disabled")
            enchanting_raw_debug_text.see("end")
        update_raw_btn = tk.Button(enchanting_raw_debug_frame, text="Update", command=update_enchanting_raw_debug_tab, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold"))
        update_raw_btn.pack(anchor="ne", padx=8, pady=2)
        update_enchanting_raw_debug_tab()
        # Auto-update every 2 seconds if debug window is open
        if self.debug_window_open:
            self.root.after(2000, lambda: update_enchanting_raw_debug_tab() if self.debug_window_open else None)
        notebook.add(enchanting_raw_debug_frame, text="✨ Enchanting Raw Debug")
        
        # Enchanting Opportunities tab
        enchanting_opps_frame = tk.Frame(notebook)
        enchanting_opps_text = tk.Text(enchanting_opps_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#ff6b6b")
        enchanting_opps_text.pack(fill="both", expand=True)
        def update_enchanting_opps_tab():
            enchanting_opps_text.config(state="normal")
            enchanting_opps_text.delete("1.0", "end")
            if hasattr(self, 'enchanting_opportunities'):
                for i, opp in enumerate(self.enchanting_opportunities[:50]):  # Show last 50 opportunities
                    enchanting_opps_text.insert("end", f"Opportunity {i+1}: {opp}\n")
            else:
                enchanting_opps_text.insert("end", "No enchanting opportunities found yet.\n")
            enchanting_opps_text.config(state="disabled")
            enchanting_opps_text.see("end")
        update_opps_btn = tk.Button(enchanting_opps_frame, text="Update", command=update_enchanting_opps_tab, bg="#232946", fg="#ff6b6b", font=("Consolas", 10, "bold"))
        update_opps_btn.pack(anchor="ne", padx=8, pady=2)
        update_enchanting_opps_tab()
        notebook.add(enchanting_opps_frame, text="💎 Enchanting Opportunities")
        
        # Enchanting Calculation tab
        enchanting_calc_frame = tk.Frame(notebook)
        enchanting_calc_text = tk.Text(enchanting_calc_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#4ecdc4")
        enchanting_calc_text.pack(fill="both", expand=True)
        def update_enchanting_calc_tab():
            enchanting_calc_text.config(state="normal")
            enchanting_calc_text.delete("1.0", "end")
            if hasattr(self, 'enchanting_prices'):
                enchanting_calc_text.insert("end", "=== ENCHANTING PRICES ===\n")
                for mat, prices in self.enchanting_prices.items():
                    enchanting_calc_text.insert("end", f"\n{mat.upper()}:\n")
                    for tier, price in prices.items():
                        enchanting_calc_text.insert("end", f"  T{tier}: {price:,} silver\n")
                enchanting_calc_text.insert("end", "\n=== MATERIAL QUANTITIES ===\n")
                mat_qty_map = {
                    'OFF': 96, '2H': 384, 'MAIN': 288, 'HEAD': 96,
                    'ARMOR': 192, 'SHOES': 96, 'CAPE': 96, 'BAG': 192
                }
                for item_type, qty in mat_qty_map.items():
                    enchanting_calc_text.insert("end", f"{item_type}: {qty} materials\n")
            else:
                enchanting_calc_text.insert("end", "Enchanting prices not loaded.\n")
            enchanting_calc_text.config(state="disabled")
            enchanting_calc_text.see("end")
        update_calc_btn = tk.Button(enchanting_calc_frame, text="Update", command=update_enchanting_calc_tab, bg="#232946", fg="#4ecdc4", font=("Consolas", 10, "bold"))
        update_calc_btn.pack(anchor="ne", padx=8, pady=2)
        update_enchanting_calc_tab()
        notebook.add(enchanting_calc_frame, text="🧮 Enchanting Calculation")
        
        # Enchanting Prices tab
        enchanting_prices_frame = tk.Frame(notebook)
        enchanting_prices_text = tk.Text(enchanting_prices_frame, wrap="none", font=("Consolas", 10), bg="#181c24", fg="#ffd93d")
        enchanting_prices_text.pack(fill="both", expand=True)
        def update_enchanting_prices_tab():
            enchanting_prices_text.config(state="normal")
            enchanting_prices_text.delete("1.0", "end")
            try:
                with open('enchanting_prices.json', 'r', encoding='utf-8') as f:
                    prices_data = json.load(f)
                    enchanting_prices_text.insert("end", "=== ENCHANTING PRICES FROM FILE ===\n")
                    enchanting_prices_text.insert("end", json.dumps(prices_data, indent=2))
            except Exception as e:
                enchanting_prices_text.insert("end", f"Error reading enchanting_prices.json: {e}\n")
            enchanting_prices_text.config(state="disabled")
            enchanting_prices_text.see("end")
        update_prices_btn = tk.Button(enchanting_prices_frame, text="Update", command=update_enchanting_prices_tab, bg="#232946", fg="#ffd93d", font=("Consolas", 10, "bold"))
        update_prices_btn.pack(anchor="ne", padx=8, pady=2)
        update_enchanting_prices_tab()
        notebook.add(enchanting_prices_frame, text="💰 Enchanting Prices")

    # Enchanting methods
    def on_enchanting_toggle(self):
        self.root.update_idletasks()  # Force UI update before reading the variable
        if self.enchanting_enabled is not None and self.enchanting_enabled.get():
            self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Enchanting enabled.")
        else:
            self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Enchanting disabled.")

    def load_enchanting_prices(self):
        """Automatically load enchanting prices from file or create defaults"""
        try:
            if os.path.exists('enchanting_prices.json'):
                with open('enchanting_prices.json', 'r', encoding='utf-8') as f:
                    self.enchanting_prices = json.load(f)
                print("✅ Enchanting prices loaded automatically")
            else:
                # Create default prices if file doesn't exist
                self.enchanting_prices = {
                    'rune': {str(tier): 1000 for tier in range(4, 9)},
                    'soul': {str(tier): 5000 for tier in range(4, 9)},
                    'relic': {str(tier): 25000 for tier in range(4, 9)}
                }
                print("✅ Default enchanting prices set")
        except Exception as e:
            print(f"❌ Failed to load enchanting prices: {e}")
            # Set default prices on error
            self.enchanting_prices = {
                'rune': {str(tier): 1000 for tier in range(4, 9)},
                'soul': {str(tier): 5000 for tier in range(4, 9)},
                'relic': {str(tier): 25000 for tier in range(4, 9)}
            }
    
    def input_enchanting_prices(self):
        # Load enchanting prices from file if available
        try:
            if os.path.exists('enchanting_prices.json'):
                with open('enchanting_prices.json', 'r', encoding='utf-8') as f:
                    self.enchanting_prices = json.load(f)
        except Exception as e:
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(f"[ERROR] Failed to load enchanting prices: {e}")
        # Ensure enchanting_prices is always initialized
        if not hasattr(self, 'enchanting_prices') or not self.enchanting_prices or \
           any(mat not in self.enchanting_prices for mat in ['rune', 'soul', 'relic']):
            self.enchanting_prices = {
                'rune': {str(tier): 0 for tier in range(4, 9)},
                'soul': {str(tier): 0 for tier in range(4, 9)},
                'relic': {str(tier): 0 for tier in range(4, 9)}
            }
        import customtkinter as ctk
        price_win = ctk.CTkToplevel(self.root)
        price_win.title("Set Enchanting Material Prices")
        price_win.geometry("750x800")
        price_win.configure(fg_color="#181c24")
        price_win.focus_force()
        price_win.attributes('-topmost', True)
        price_win.lift()
        # Glassmorphism main frame
        glass_frame = ctk.CTkFrame(price_win, fg_color="#232946", corner_radius=24, border_width=2, border_color="#00d4ff")
        glass_frame.pack(fill="both", expand=True, padx=24, pady=24)
        # Title
        ctk.CTkLabel(glass_frame, text="Set Enchanting Material Prices", font=("Segoe UI", 22, "bold"), text_color="#00d4ff").pack(pady=(18, 24))
        # Section builder
        entries = {}
        def section(title, icon, mat):
            section_frame = ctk.CTkFrame(glass_frame, fg_color="#232946", corner_radius=18, border_width=2, border_color="#00d4ff")
            section_frame.pack(fill="x", padx=0, pady=(0, 18))
            ctk.CTkLabel(section_frame, text=f"{icon}  {title}", font=("Segoe UI", 16, "bold"), text_color="#00d4ff").pack(anchor="w", pady=(10, 8), padx=18)
            grid_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            grid_frame.pack(fill="x", padx=18, pady=(0, 12))
            for i, tier in enumerate(["T4", "T5", "T6", "T7", "T8"]):
                t = 4 + i
                var = tk.StringVar(value=str(self.enchanting_prices[mat][str(t)]))
                entry = ctk.CTkEntry(grid_frame, textvariable=var, width=100, font=("Segoe UI", 18), fg_color="#181c24", border_color="#00d4ff", border_width=2, corner_radius=12, justify="center")
                entry.grid(row=0, column=i, padx=8, pady=8)
                entry.bind("<FocusIn>", lambda e, ent=entry: ent.configure(border_color="#00fff7"))
                entry.bind("<FocusOut>", lambda e, ent=entry: ent.configure(border_color="#00d4ff"))
                entries[(mat, t)] = var
                ctk.CTkLabel(grid_frame, text=tier, font=("Segoe UI", 14, "bold"), text_color="#00d4ff").grid(row=1, column=i, padx=8, pady=(0, 0))
        # Place sections
        section("Runes", "🪄", "rune")
        section("Souls", "💠", "soul")
        section("Relics", "🔮", "relic")
        # Save button with glow
        def save_prices():
            debug_msg = []
            for (mat, t), var in entries.items():
                try:
                    value = int(float(var.get()))
                    self.enchanting_prices[mat][str(t)] = value
                    var.set(str(value))
                except Exception:
                    self.enchanting_prices[mat][str(t)] = 0
                    var.set("0")
                debug_msg.append(f"{mat.capitalize()} T{t}: {self.enchanting_prices[mat][str(t)]}")
            try:
                save_dict = {mat: {str(t): v for t, v in self.enchanting_prices[mat].items()} for mat in self.enchanting_prices}
                with open('enchanting_prices.json', 'w', encoding='utf-8') as f:
                    json.dump(save_dict, f, indent=2)
            except Exception as e:
                if hasattr(self, 'enchanting_debug_log'):
                    self.enchanting_debug_log.appendleft(f"[ERROR] Failed to save enchanting prices: {e}")
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Saved enchanting prices: " + ", ".join(debug_msg))
            price_win.destroy()
        save_btn = AnimatedButton(glass_frame, text="💾 Save Prices", command=save_prices, fg_color="#00d4ff", text_color="#181c24", font=("Segoe UI", 18, "bold"), corner_radius=16, width=240, height=54)
        save_btn.pack(pady=18)
        save_btn.bind("<Enter>", lambda e: save_btn.configure(fg_color="#00fff7"))
        save_btn.bind("<Leave>", lambda e: save_btn.configure(fg_color="#00d4ff"))

    def scan_for_enchanting_flips(self):
        """Generate enchanting opportunities for every city and every valid stepwise enchantment upgrade (e.g., 4.0→4.1, 4.1→4.2, 4.2→4.3, etc.). BM is not a source city. Deduplicate by (city, item, from_enchant, to_enchant) with lowest city price."""
        if not hasattr(self, 'enchanting_raw_debug_log'):
            self.enchanting_raw_debug_log = []
        try:
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Starting enchanting scan...")
            all_opps = self.flip_detector.scan_for_all_flips(self.scan_log)
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Checking {len(all_opps)} total flip opportunities for enchanting...")
            enchanting_opps = []
            dedup_map = {}  # key: (city, from_item_id, to_enchant), value: (city_price, row)
            city_price_data = self.flip_detector.city_price_data
            all_cities = [c for c in self.flip_detector.city_filters if c != 'Black Market'] if hasattr(self.flip_detector, 'city_filters') else ['Caerleon', 'Bridgewatch', 'Martlock', 'Lymhurst', 'Fort Sterling', 'Thetford', 'Brecilien']
            for item_id in city_price_data:
                tier, base, _ = parse_item_id(item_id)
                if tier is None:
                    continue
                for city in all_cities:
                    available_enchants = set()
                    city_qualities_by_enchant = {}
                    for possible_enchant in range(0, 4):
                        city_item_id = f"{base}@{possible_enchant}" if possible_enchant > 0 else base
                        city_qualities = city_price_data.get(city_item_id, {}).get(city, {})
                        if any(data.get('sell_price') is not None for data in city_qualities.values()):
                            available_enchants.add(possible_enchant)
                            city_qualities_by_enchant[possible_enchant] = city_qualities
                    for from_enchant in sorted(available_enchants):
                        for to_enchant in range(from_enchant+1, 4):
                            if to_enchant not in available_enchants:
                                continue
                            from_qualities = city_qualities_by_enchant[from_enchant]
                            min_from_price = None
                            min_from_data = None
                            for q, data in from_qualities.items():
                                if data.get('sell_price') is not None:
                                    if min_from_price is None or data['sell_price'] < min_from_price:
                                        min_from_price = data['sell_price']
                                        min_from_data = data
                            if min_from_price is None:
                                continue
                            bm_item_id = f"{base}@{to_enchant}"
                            for bm_quality in range(1, 6):
                                bm_key = (bm_item_id, bm_quality)
                                bm_data = self.flip_detector.bm_price_data.get(bm_key, {}).get('Black Market')
                                if not bm_data or not bm_data.get('buy_price'):
                                    continue
                                from_item_id = f"{base}@{from_enchant}" if from_enchant > 0 else base
                                dedup_key = (city, from_item_id, to_enchant)
                                # Only keep the row with the lowest city price for each dedup_key
                                if dedup_key in dedup_map and min_from_price >= dedup_map[dedup_key][0]:
                                    continue
                                bm_age = 0
                                city_age = 0
                                if bm_data.get('last_update'):
                                    bm_age = int((datetime.now(timezone.utc) - bm_data['last_update']).total_seconds() / 60)
                                if min_from_data and min_from_data.get('last_update'):
                                    city_age = int((datetime.now(timezone.utc) - min_from_data['last_update']).total_seconds() / 60)
                                item_type = None
                                item_id_upper = bm_item_id.upper()
                                if 'OFF' in item_id_upper:
                                    item_type = 'OFF'
                                elif '2H' in item_id_upper:
                                    item_type = '2H'
                                elif 'MAIN' in item_id_upper:
                                    item_type = 'MAIN'
                                elif 'HEAD' in item_id_upper:
                                    item_type = 'HEAD'
                                elif 'ARMOR' in item_id_upper:
                                    item_type = 'ARMOR'
                                elif 'SHOES' in item_id_upper:
                                    item_type = 'SHOES'
                                elif 'CAPE' in item_id_upper:
                                    item_type = 'CAPE'
                                elif 'BAG' in item_id_upper:
                                    item_type = 'BAG'
                                else:
                                    item_type = 'OFF'  # fallback
                                mat_qty_map = {
                                    'OFF': 96,
                                    '2H': 384,
                                    'MAIN': 288,
                                    'HEAD': 96,
                                    'ARMOR': 192,
                                    'SHOES': 96,
                                    'CAPE': 96,
                                    'BAG': 192
                                }
                                mat_qty = mat_qty_map.get(item_type, 96)
                                total_enchant_cost = 0
                                mat_zero_warning = False
                                path_steps = []
                                for step in range(from_enchant+1, to_enchant+1):
                                    if step == 1:
                                        mat = 'rune'
                                    elif step == 2:
                                        mat = 'soul'
                                    elif step == 3:
                                        mat = 'relic'
                                    else:
                                        mat = 'rune'  # fallback
                                    mat_prices = self.enchanting_prices.get(mat, {})
                                    if not mat_prices:
                                        warn_msg = f"[ENCHANT DEBUG] Missing enchanting material: {mat} for step {step} (tier {tier})"
                                        print(warn_msg)
                                        if hasattr(self, 'enchanting_raw_debug_log'):
                                            self.enchanting_raw_debug_log.append(warn_msg)
                                    mat_price = int(mat_prices.get(str(tier), 0))
                                    if mat_price == 0:
                                        warn_msg = f"[ENCHANT DEBUG] Missing price for {mat} at tier {tier} (step {step})"
                                        print(warn_msg)
                                        if hasattr(self, 'enchanting_raw_debug_log'):
                                            self.enchanting_raw_debug_log.append(warn_msg)
                                    step_cost = mat_price * mat_qty
                                    debug_msg = f"[ENCHANT DEBUG] Step {step}: {mat} (tier {tier}) price {mat_price} x qty {mat_qty} = {step_cost}"
                                    print(debug_msg)
                                    if hasattr(self, 'enchanting_raw_debug_log'):
                                        self.enchanting_raw_debug_log.append(debug_msg)
                                    total_enchant_cost += step_cost
                                    path_steps.append(f"T{tier}.{step}")
                                path_str = f"T{tier}.{from_enchant} ({city}) → T{tier}.{to_enchant}"
                                total_cost = min_from_price + total_enchant_cost
                                # Apply premium tax rate to the profit calculation
                                is_premium = self.premium_var.get()
                                tax_rate = 0.065 if is_premium else 0.105
                                profit_before_tax = bm_data['buy_price'] - total_cost
                                profit = int(profit_before_tax - (bm_data['buy_price'] * tax_rate))
                                roi = (profit / total_cost * 100) if total_cost else 0
                                display_name = self.item_manager.get_display_name(from_item_id) if base else bm_item_id
                                def format_large(n):
                                    if n >= 1_000_000:
                                        return f"{n/1_000_000:.1f}M"
                                    elif n >= 1_000:
                                        return f"{n:,}"
                                    else:
                                        return str(n)
                                if bm_age > 20:
                                    continue
                                row = (
                                    city,
                                    display_name,
                                    QUALITY_LEVEL_NAMES.get(bm_quality, str(bm_quality)),
                                    path_str,
                                    f"{format_large(min_from_price)}",
                                    f"{format_large(total_enchant_cost)}" + (" ⚠️" if mat_zero_warning else ""),
                                    f"{format_large(bm_data['buy_price'])}",
                                    f"{format_large(profit)}",
                                    f"{roi:.1f}%",
                                    "✔" if f"{city}_{display_name}_{path_str}" in self.completed_flips else "",
                                    bm_age,
                                    city_age
                                )
                                dedup_map[dedup_key] = (min_from_price, row)
                                bm_age_str = f"{bm_age}"
                                city_age_str = f"{city_age}"
                                self.enchanting_raw_debug_log.append(f"[RAW] Opportunity: {display_name} in {city} | BM price: {bm_data['buy_price']} (age: {bm_age_str}m), City price: {min_from_price} (age: {city_age_str}m)")
                                self.enchanting_raw_debug_log.append(f"[RAW] City: {city}, Item: {display_name}, Path: {path_str}, EnchantCost: {total_enchant_cost}, BM: {bm_data['buy_price']}, Profit: {profit}, ROI: {roi:.1f}%, MatZero: {mat_zero_warning}")
                                if hasattr(self, 'enchanting_debug_log'):
                                    self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Enchanting opp: {bm_item_id} in {city} | Start: T{tier}.{from_enchant} | Path: {path_str} | Enchant Cost: {total_enchant_cost} | Profit: {profit}")
            enchanting_opps = [row for _, row in dedup_map.values()]
            self.enchanting_opportunities = enchanting_opps
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(enchanting_opps)} enchanting opportunities.")
                sample = enchanting_opps[:10]
                for row in sample:
                    city, item, quality, path, *_ = row
                    self.enchanting_debug_log.appendleft(f"[SAMPLE] City: {city}, Item: {item}, Quality: {quality}, Path: {path}")
            if hasattr(self, 'refresh_enchanting_table'):
                self.refresh_enchanting_table()
        except Exception as e:
            err_msg = f"[ERROR] Exception in scan_for_enchanting_flips: {e}"
            print(err_msg)
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(err_msg)
            if hasattr(self, 'enchanting_raw_debug_log'):
                self.enchanting_raw_debug_log.append(err_msg)

    def on_enchanting_tab_selected(self):
        self.scan_for_enchanting_flips()

    def _on_tab_changed(self, value=None):
        # customtkinter may call this with no argument, so fetch the current tab if needed
        if value is None and hasattr(self.tabview, 'get'):  # Defensive: get current tab
            value = self.tabview.get()
        # No longer call scan_for_enchanting_flips here; handled by auto scan
        pass

    def schedule_auto_enchanting_scan(self):
        """Automatically scan for enchanting flips every 5 seconds for better performance."""
        self.scan_for_enchanting_flips()
        self.root.after(5000, self.schedule_auto_enchanting_scan)

    def on_enchanting_tree_click(self, event):
        region = self.enchanting_tree.identify_region(event.x, event.y)
        col_id = self.enchanting_tree.identify_column(event.x)
        col_text = self.enchanting_tree.heading(col_id, "text").strip()
        if region == "cell" and col_text.startswith("Done"):
            row_id = self.enchanting_tree.identify_row(event.y)
            if row_id:
                self.enchanting_tree.selection_set(row_id)
                self.toggle_enchanting_done(row_id)

    def toggle_enchanting_done(self, row_id):
        try:
            item = self.enchanting_tree.item(row_id)
            values = item['values']
            if not values:
                return
            # Use city+item+path as a unique key
            flip_id = f"{values[0]}_{values[1]}_{values[3]}"
            if flip_id in self.completed_flips:
                self.completed_flips.remove(flip_id)
            else:
                self.completed_flips.add(flip_id)
            self.refresh_enchanting_table()
        except Exception as e:
            err_msg = f"[ERROR] Exception in toggle_enchanting_done: {e}"
            print(err_msg)
            if hasattr(self, 'enchanting_debug_log'):
                self.enchanting_debug_log.appendleft(err_msg)
            if hasattr(self, 'enchanting_raw_debug_log'):
                self.enchanting_raw_debug_log.append(err_msg)

    def sort_enchanting_by_column(self, col, reverse, toggle=True):
        # Get all rows from the treeview
        rows = [(self.enchanting_tree.set(k, col), k) for k in self.enchanting_tree.get_children('')]
        
        def safe_str(val):
            return str(val) if not isinstance(val, dict) else ''
            
        def get_price_age_sort_key(row):
            # Extract the price age string (e.g., "B5m/R10m")
            price_age_str = safe_str(row[0])
            if not price_age_str or not ('B' in price_age_str and 'R' in price_age_str):
                return float('inf')  # Put invalid formats at the end
                
            try:
                # Extract BM and city ages (e.g., "5m" and "10m" from "B5m/R10m")
                bm_part, city_part = price_age_str.replace('B', '').split('/R')
                bm_age = int(bm_part.replace('m', '')) if 'm' in bm_part else 0
                city_age = int(city_part.replace('m', '')) if 'm' in city_part else 0
                # Return the maximum age (so newest will be first when sorted in ascending order)
                return max(bm_age, city_age)
            except (ValueError, AttributeError):
                return float('inf')  # Put invalid formats at the end
        
        if col == 'Price Age':
            # Sort by price age with newest (smallest age) first by default
            rows.sort(key=lambda t: get_price_age_sort_key(t), reverse=not reverse)
        elif col == 'Total Profit' or col == 'Enchant Cost' or col == 'BM Price':
            rows.sort(key=lambda t: float(safe_str(t[0]).replace(',', '').replace('N/A', '0')), reverse=not reverse)
        elif col == 'ROI':
            rows.sort(key=lambda t: float(safe_str(t[0]).replace('%', '').replace('N/A', '0')), reverse=not reverse)
        elif col == 'Last Update':
            from datetime import datetime
            rows.sort(key=lambda t: datetime.strptime(safe_str(t[0]), '%Y-%m-%d %H:%M:%S') if safe_str(t[0]) else datetime.min, reverse=not reverse)
        else:
            rows.sort(reverse=not reverse)
            
        # Rearrange items in the treeview
        for index, (val, k) in enumerate(rows):
            self.enchanting_tree.move(k, '', index)

    def save_filter_preset(self, name: str) -> None:
        """Save the current item and city filters as a preset with the given name."""
        preset = {
            'items': list(self.flip_detector.item_filters),
            'cities': list(self.flip_detector.city_filters)
        }
        presets = self.load_filter_presets()
        presets[name] = preset
        with open('filter_presets.json', 'w', encoding='utf-8') as f:
            json.dump(presets, f, indent=2)
    def load_filter_presets(self) -> dict:
        """Load all filter presets from file."""
        try:
            with open('filter_presets.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    def apply_filter_preset(self, name: str) -> None:
        """Apply the item and city filters from the named preset."""
        presets = self.load_filter_presets()
        if name in presets:
            preset = presets[name]
            self.flip_detector.set_filters(preset['items'], preset['cities'])
    def show_filter_preset_dialog(self) -> None:
        """Show a dialog to save/load filter presets."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Filter Presets")
        dialog.geometry("400x300")
        dialog.configure(bg="#181c24")
        ctk.CTkLabel(dialog, text="Filter Presets", font=("Segoe UI", 13, "bold"), text_color="#00d4ff").pack(pady=8)
        presets = self.load_filter_presets()
        listbox = tk.Listbox(dialog, font=("Consolas", 11), bg="#232946", fg="#00ff99")
        for name in presets:
            listbox.insert("end", name)
        listbox.pack(fill="both", expand=True, padx=12, pady=8)
        def load_selected():
            sel = listbox.curselection()
            if sel:
                name = listbox.get(sel[0])
                self.apply_filter_preset(name)
                dialog.destroy()
        def save_new():
            name = tkinter.simpledialog.askstring("Save Preset", "Preset name:", parent=dialog)
            if name:
                self.save_filter_preset(name)
                dialog.destroy()
        btn_frame = ctk.CTkFrame(dialog, fg_color="#181c24")
        btn_frame.pack(fill="x", pady=6)
        tk.Button(btn_frame, text="Load Selected", command=load_selected, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold")).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Save Current as New", command=save_new, bg="#232946", fg="#00ff99", font=("Consolas", 10, "bold")).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Close", command=dialog.destroy, bg="#232946", fg="#00d4ff", font=("Consolas", 10)).pack(side="right", padx=8)

    def _get_filtered_opportunities(self):
        """Returns the list of opportunities that match the current UI filters (BM quality only)."""
        filtered_opportunities = self.flip_opportunities
        selected_city = self.filter_city_var.get()
        if selected_city != "All":
            filtered_opportunities = [opp for opp in filtered_opportunities if opp.city == selected_city]
        selected_quality_str = self.filter_quality_var.get()
        if selected_quality_str != "All":
            quality_map = {v: k for k, v in QUALITY_LEVEL_NAMES.items()}
            selected_quality_level = quality_map.get(selected_quality_str)
            if selected_quality_level:
                filtered_opportunities = [opp for opp in filtered_opportunities if opp.bm_quality == selected_quality_level]
        selected_tier_str = self.filter_tier_var.get()
        if selected_tier_str != "All":
            try:
                selected_tier = int(selected_tier_str)
                filtered_opportunities = [opp for opp in filtered_opportunities if opp.tier == selected_tier]
            except (ValueError, TypeError):
                pass
        
        try:
            min_profit = int(self.min_profit_var.get())
            is_premium = self.premium_var.get()

            if is_premium:
                tax_rate = 0.065
            else:
                tax_rate = 0.105

            profitable_opportunities = []
            for opp in filtered_opportunities:
                profit = int((opp.bm_price - opp.city_price) - (opp.bm_price * tax_rate))
                if profit >= min_profit:
                    profitable_opportunities.append(opp)
            
            filtered_opportunities = profitable_opportunities

        except (ValueError, TypeError):
            pass # Ignore if entry is not a valid number, or if vars not init yet

        return filtered_opportunities

    def schedule_auto_scan_and_refresh(self):
        """Automatically run a full scan and refresh the table every 30 seconds."""
        print('[AutoScan] Triggering automatic full scan and refresh...')
        self.run_full_scan() # This already updates the view at the end
        self.root.after(30_000, self.schedule_auto_scan_and_refresh)  # 30 seconds

    def load_completed_flips(self):
        try:
            if os.path.exists(self.completed_flips_file):
                with open(self.completed_flips_file, 'r', encoding='utf-8') as f:
                    self.completed_flips_history = json.load(f)
                logger.info(f"Loaded {len(self.completed_flips_history)} completed flips from {self.completed_flips_file}")
        except Exception as e:
            logger.error(f"Error loading completed flips: {e}")
            self.completed_flips_history = [] # Start fresh on error

    def save_completed_flips(self):
        try:
            with open(self.completed_flips_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_flips_history, f, indent=2)
            logger.info(f"Saved {len(self.completed_flips_history)} completed flips to {self.completed_flips_file}")
        except Exception as e:
            logger.error(f"Error saving completed flips: {e}")

    def create_analytics_section(self, parent):
        """Create analytics section with original functionality and modern styling"""
        try:
            # Time period filter frame
            filter_frame = ctk.CTkFrame(parent, fg_color="#232946", corner_radius=12, border_width=1, border_color="#2d3748")
            filter_frame.pack(fill="x", padx=8, pady=(8, 4))
            
            filter_header = ctk.CTkLabel(
                filter_frame,
                text="⏰ Time Period Filter",
                font=("Segoe UI", 12, "bold"),
                text_color="#ffffff"
            )
            filter_header.pack(pady=(12, 8), padx=12, anchor="w")
            
            # Time period variable
            self.analytics_time_period = ctk.StringVar(value="All Time")
            
            # Time period buttons
            time_buttons_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
            time_buttons_frame.pack(side="left", padx=12, pady=(0, 12))
            
            periods = [("Week", "Week"), ("Month", "Month"), ("Year", "Year"), ("All Time", "All Time")]
            for text, value in periods:
                btn = ctk.CTkButton(
                    time_buttons_frame, 
                    text=text, 
                    command=lambda v=value: self.change_analytics_period(v),
                    fg_color="#232946",
                    text_color="#a0aec0",
                    font=("Segoe UI", 11, "bold"),
                    corner_radius=18,
                    height=32,
                    hover_color="#2d3748",
                    border_width=1,
                    border_color="#2d3748"
                )
                btn.pack(side="left", padx=2)
                # Store button reference for highlighting
                setattr(self, f'analytics_btn_{value.lower().replace(" ", "_")}', btn)
            
            # Highlight the default button
            self._highlight_analytics_button("All Time")
            
            # Stats frame
            stats_frame = ctk.CTkFrame(parent, fg_color="#232946", corner_radius=12, border_width=1, border_color="#2d3748")
            stats_frame.pack(fill="x", padx=8, pady=4)
            
            stats_header = ctk.CTkLabel(
                stats_frame,
                text="📊 Performance Statistics",
                font=("Segoe UI", 12, "bold"),
                text_color="#ffffff"
            )
            stats_header.pack(pady=(12, 8), padx=12, anchor="w")
            
            # First row of stats
            stats_row1 = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stats_row1.pack(fill="x", padx=12, pady=(0, 8))
            
            # Profit label
            self.analytics_profit_label = ctk.CTkLabel(
                stats_row1, 
                text="Total Profit: 0", 
                font=("Segoe UI", 14, "bold"), 
                text_color="#00d4ff"
            )
            self.analytics_profit_label.pack(side="left")
            
            # Additional stats labels
            self.analytics_flips_count_label = ctk.CTkLabel(
                stats_row1, 
                text="Flips: 0", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_flips_count_label.pack(side="left", padx=(20, 0))
            
            self.analytics_avg_profit_label = ctk.CTkLabel(
                stats_row1, 
                text="Avg Profit: 0", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_avg_profit_label.pack(side="left", padx=(20, 0))
            
            self.analytics_profit_per_day_label = ctk.CTkLabel(
                stats_row1, 
                text="Profit/Day: 0", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_profit_per_day_label.pack(side="left", padx=(20, 0))
            
            # Second row of stats
            stats_row2 = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stats_row2.pack(fill="x", padx=12, pady=(0, 12))
            
            self.analytics_max_profit_label = ctk.CTkLabel(
                stats_row2, 
                text="Max Profit: 0", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_max_profit_label.pack(side="left")
            
            self.analytics_best_item_label = ctk.CTkLabel(
                stats_row2, 
                text="Best Item: None", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_best_item_label.pack(side="left", padx=(20, 0))
            
            self.analytics_best_city_label = ctk.CTkLabel(
                stats_row2, 
                text="Best City: None", 
                font=("Segoe UI", 12), 
                text_color="#e2e8f0"
            )
            self.analytics_best_city_label.pack(side="left", padx=(20, 0))
            
            # Table
            table_frame = ctk.CTkFrame(parent, fg_color="#232946", corner_radius=12, border_width=1, border_color="#2d3748")
            table_frame.pack(fill="both", expand=True, padx=8, pady=4)
            
            table_header = ctk.CTkLabel(
                table_frame,
                text="📋 Flip History",
                font=("Segoe UI", 14, "bold"),
                text_color="#00d4ff"
            )
            table_header.pack(pady=(16, 12), padx=16, anchor="w")
            
            self.analytics_table = ctk.CTkTextbox(
                table_frame, 
                font=("Segoe UI", 11), 
                fg_color="#1a1d2e", 
                text_color="#e2e8f0", 
                height=300,
                wrap="none",
                corner_radius=8
            )
            self.analytics_table.pack(fill="both", expand=True, padx=16, pady=(0, 16))
            

            
            # Refresh button
            refresh_btn = ctk.CTkButton(
                parent, 
                text="🔄 Refresh Analytics", 
                command=self.refresh_analytics_tab, 
                fg_color="#00d4ff",
                text_color="#181c24",
                font=("Segoe UI", 12, "bold"),
                corner_radius=20,
                height=40,
                hover_color="#00b0cc"
            )
            refresh_btn.pack(anchor="ne", padx=16, pady=16)
            
            self.refresh_analytics_tab()
        except Exception as e:
            # Create error display with modern styling
            error_frame = ctk.CTkFrame(parent, fg_color="#2d1b1b", corner_radius=12, border_width=1, border_color="#ff4b91")
            error_frame.pack(fill="x", padx=8, pady=8)
            
            error_label = ctk.CTkLabel(
                error_frame, 
                text=f"❌ Error loading Analytics: {e}", 
                font=("Segoe UI", 11, "bold"),
                text_color="#ff4b91"
            )
            error_label.pack(pady=12)
            
            # Add retry button
            retry_btn = ctk.CTkButton(
                error_frame,
                text="🔄 Retry",
                command=lambda: self.rebuild_analytics_section(parent),
                fg_color="#ff4b91",
                text_color="#ffffff",
                font=("Segoe UI", 10, "bold"),
                corner_radius=8,
                height=28
            )
            retry_btn.pack(pady=(0, 12))

    def rebuild_analytics_section(self, parent):
        """Rebuild the analytics section from scratch"""
        try:
            # Clear existing widgets
            for widget in parent.winfo_children():
                widget.destroy()
            
            # Recreate the analytics section
            self.create_analytics_section(parent)
            print("✅ Analytics section rebuilt successfully")
        except Exception as e:
            print(f"❌ Error rebuilding analytics section: {e}")

    def open_url(self, url):
        """Open URL in default browser"""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"❌ Error opening URL: {e}")
    
    def check_for_updates(self):
        """Check for updates using the auto-updater"""
        try:
            print("🔍 Checking for updates...")
            self.auto_updater.check_for_updates(parent=self.root)
        except Exception as e:
            print(f"❌ Error checking for updates: {e}")
            messagebox.showerror("Update Error", f"Failed to check for updates: {str(e)}")
    
    def check_for_updates_silent(self):
        """Check for updates silently (no user interaction unless update is found)"""
        try:
            print("🔍 Checking for updates silently...")
            self.auto_updater.check_for_updates(parent=self.root, silent=True)
        except Exception as e:
            print(f"❌ Error checking for updates silently: {e}")
    
    def reset_sort(self):
        """Reset sort to default (Total Profit, descending)"""
        self.sort_column = "Total Profit"
        self.sort_reverse = True
        self._apply_current_sort()
        self._update_results_display()
        
        # Update sort indicators in header
        for c in self.tree['columns']:
            self.tree.heading(c, text=c)  # Reset all headers
            
        arrow = ' ▼' if self.sort_reverse else ' ▲'
        self.tree.heading(self.sort_column, text=self.sort_column + arrow)
        
        print("🔄 Sort reset to default (Total Profit, descending)")

    def toggle_notifications(self):
        """Toggle notifications on/off"""
        status = "enabled" if self.notifications_enabled.get() else "disabled"
        print(f"🔔 Desktop notifications {status}")
    
    def show_notification(self, title, message, duration=5000):
        """Show a beautiful desktop notification popup with modern styling"""
        if not self.notifications_enabled.get():
            return
            
        # Check cooldown to prevent spam
        current_time = time.time()
        try:
            cooldown = int(self.notification_cooldown_var.get())
        except ValueError:
            cooldown = 10  # Default fallback
            
        if current_time - self.last_notification_time < cooldown:
            return
            
        # Close any existing notification
        if self.active_notification and self.active_notification.winfo_exists():
            try:
                self.active_notification.destroy()
            except:
                pass
            
        try:
            # Play notification sound
            self.play_notification_sound()
            
            # Create notification window with modern styling
            notification = tk.Toplevel(self.root)
            notification.title("")
            notification.configure(bg="#1a1d2e")
            
            # Position in bottom-right corner with smooth animation
            screen_width = notification.winfo_screenwidth()
            screen_height = notification.winfo_screenheight()
            
            # Calculate dynamic height based on message content
            notification_width = 380
            base_height = 140
            
            # Create a temporary label to measure text height
            temp_label = tk.Label(notification, text=message, font=("Segoe UI", 10), 
                                wraplength=340, justify="left")
            temp_label.pack_forget()  # Don't actually show it
            
            # Get the required height for the text
            temp_label.update_idletasks()
            text_height = temp_label.winfo_reqheight()
            temp_label.destroy()
            
            # Calculate total height needed
            header_height = 45  # Header space
            padding = 35  # Total padding
            progress_height = 4  # Progress bar height
            
            required_height = header_height + text_height + padding + progress_height
            
            # Ensure minimum and maximum heights
            notification_height = max(140, min(required_height, 400))  # Min 140px, Max 400px
            
            x = max(20, screen_width - notification_width - 20)  # 20px margin from right
            y = max(20, screen_height - notification_height - 20)  # 20px margin from bottom
            
            # Set initial geometry and start off-screen for slide-in animation
            notification.geometry(f"{notification_width}x{notification_height}+{screen_width}+{y}")
            
            # Make it stay on top
            notification.attributes('-topmost', True)
            
            # Remove window decorations
            notification.overrideredirect(True)
            
            # Create main container with glassmorphism effect
            main_frame = tk.Frame(notification, bg="#1a1d2e", relief="flat", bd=0)
            main_frame.pack(fill="both", expand=True, padx=2, pady=2)
            
            # Create inner frame with gradient-like effect
            inner_frame = tk.Frame(main_frame, bg="#232946", relief="flat", bd=0)
            inner_frame.pack(fill="both", expand=True, padx=1, pady=1)
            
            # Add subtle border effect
            border_frame = tk.Frame(inner_frame, bg="#00d4ff", height=3)
            border_frame.pack(fill="x", side="top")
            
            # Header frame with icon and title
            header_frame = tk.Frame(inner_frame, bg="#232946", relief="flat", bd=0)
            header_frame.pack(fill="x", padx=16, pady=(10, 6))
            
            # App icon
            icon_label = tk.Label(header_frame, text="🦁", font=("Segoe UI Emoji", 14), 
                                bg="#232946", fg="#00d4ff")
            icon_label.pack(side="left")
            
            # Title with enhanced styling
            title_label = tk.Label(header_frame, text=title, font=("Segoe UI", 12, "bold"), 
                                 bg="#232946", fg="#00d4ff", anchor="w")
            title_label.pack(side="left", padx=(8, 0), fill="x", expand=True)
            
            # Close button with modern styling
            close_btn = tk.Button(header_frame, text="×", font=("Segoe UI", 16, "bold"), 
                                bg="#ff4444", fg="white", bd=0, padx=4, pady=0,
                                relief="flat", cursor="hand2",
                                command=lambda: self.close_notification(notification))
            close_btn.pack(side="right")
            
            # Message frame with more space
            message_frame = tk.Frame(inner_frame, bg="#232946", relief="flat", bd=0)
            message_frame.pack(fill="both", expand=True, padx=16, pady=(6, 10))
            
            # Message with enhanced styling and proper wrapping
            message_label = tk.Label(message_frame, text=message, font=("Segoe UI", 10), 
                                   bg="#232946", fg="#e2e8f0", anchor="nw", justify="left",
                                   wraplength=340, padx=0, pady=6)
            message_label.pack(fill="both", expand=True, anchor="nw", padx=0, pady=6)
            
            # Progress bar for auto-close
            progress_frame = tk.Frame(inner_frame, bg="#1a1d2e", height=2)
            progress_frame.pack(fill="x", side="bottom")
            progress_frame.pack_propagate(False)
            
            progress_bar = tk.Frame(progress_frame, bg="#00d4ff", height=2)
            progress_bar.pack(side="left")
            
            # Animate progress bar
            def animate_progress(progress=0):
                if notification.winfo_exists():
                    progress_width = int((progress / 100) * notification_width)
                    progress_bar.configure(width=progress_width)
                    if progress < 100:
                        notification.after(duration // 100, lambda: animate_progress(progress + 1))
            
            # Start progress animation
            animate_progress()
            
            # Auto-close after duration
            notification.after(duration, lambda: self.close_notification(notification))
            
            # Enhanced hover effects
            def on_enter(e):
                close_btn.configure(bg="#ff6666")
            def on_leave(e):
                close_btn.configure(bg="#ff4444")
            
            close_btn.bind("<Enter>", on_enter)
            close_btn.bind("<Leave>", on_leave)
            
            # Slide-in animation
            def slide_in(step=0):
                if notification.winfo_exists():
                    current_x = screen_width - (step * 20)  # Slide in from right
                    if current_x <= x:
                        notification.geometry(f"{notification_width}x{notification_height}+{x}+{y}")
                    else:
                        notification.geometry(f"{notification_width}x{notification_height}+{current_x}+{y}")
                        notification.after(10, lambda: slide_in(step + 1))
            
            # Start slide-in animation
            slide_in()
            
            # Store reference and update time
            self.active_notification = notification
            self.last_notification_time = current_time
            
            # Bring to front
            notification.lift()
            notification.focus_force()
            
        except Exception as e:
            print(f"❌ Error showing notification: {e}")
    
    def close_notification(self, notification):
        """Safely close notification window with smooth slide-out animation"""
        try:
            if notification and notification.winfo_exists():
                # Get current position
                current_x = notification.winfo_x()
                screen_width = notification.winfo_screenwidth()
                
                # Slide-out animation
                def slide_out(step=0):
                    if notification.winfo_exists():
                        new_x = current_x + (step * 20)  # Slide out to the right
                        if new_x >= screen_width:
                            notification.destroy()
                            if self.active_notification == notification:
                                self.active_notification = None
                        else:
                            notification.geometry(f"+{new_x}+{notification.winfo_y()}")
                            notification.after(10, lambda: slide_out(step + 1))
                
                # Start slide-out animation
                slide_out()
        except:
            # Fallback: destroy immediately if animation fails
            try:
                if notification and notification.winfo_exists():
                    notification.destroy()
                    if self.active_notification == notification:
                        self.active_notification = None
            except:
                pass
    
    def play_notification_sound(self):
        """Play a notification sound"""
        try:
            import winsound
            # Play Windows system notification sound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except ImportError:
            # Fallback for non-Windows systems
            try:
                import os
                os.system("echo -e '\a'")  # Terminal bell
            except:
                pass  # Silent fallback
        except Exception as e:
            print(f"❌ Error playing notification sound: {e}")
    
    def check_and_notify_high_profit(self, opportunity):
        """Check if opportunity meets notification criteria and show notification"""
        if not self.notifications_enabled.get():
            return
            
        try:
            # Get minimum profit threshold
            min_profit = int(self.notification_min_profit.get())
        except ValueError:
            min_profit = 200000  # Default fallback
            
        # Calculate profit after tax
        is_premium = self.premium_var.get()
        tax_rate = 0.065 if is_premium else 0.105
        profit_after_tax = int((opportunity.bm_price - opportunity.city_price) - (opportunity.bm_price * tax_rate))
        
        if profit_after_tax >= min_profit:
            # Format the notification
            title = f"🦁 RatFlipper - High Profit Alert!"
            
            item_name = self.item_manager.get_display_name(opportunity.item_name)
            quality_name = QUALITY_LEVEL_NAMES.get(opportunity.bm_quality, f"Q{opportunity.bm_quality}")
            
            message = f"💰 {item_name} ({quality_name})\n"
            message += f"📍 City: {opportunity.city}\n"
            message += f"💵 Profit: {profit_after_tax:,} silver\n"
            message += f"📦 Quantity: {opportunity.quantity}"
            
            self.show_notification(title, message)
            print(f"🔔 Notification sent for {item_name} - {profit_after_tax:,} profit")

    def toggle_debug_logging(self):
        """Toggle debug logging on/off"""
        self.debug_enabled = not self.debug_enabled
        self.debug_toggle_var.set(self.debug_enabled)
        
        # Update button text to show current state
        status = "ON" if self.debug_enabled else "OFF"
        print(f"🔧 Debug logging {status}")
        
        # If debug window is open, update its state too
        if hasattr(self, 'debug_window_open'):
            self.debug_window_open = self.debug_enabled

# Main entry point

def main():
    print("🚀 Starting main function...")
    try:
        # STANDALONE MODE: No license check needed
        print("🎭 STANDALONE MODE - No license check required")
        app = RatFlipperGUI()
        print("✅ RatFlipperGUI created successfully")
        if hasattr(app, 'root') and app.root:
            print("✅ Main window exists, binding shortcuts...")
            app.bind_shortcuts()
            print("✅ Shortcuts bound, starting mainloop...")
            app.root.mainloop()
            print("✅ Mainloop finished")
        else:
            print("❌ Main window not created!")
    except Exception as e:
        print(f"❌ Error in main function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
