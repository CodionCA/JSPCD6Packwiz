#!/usr/bin/env python3
"""
CurseForge to Modrinth Packwiz Converter v2
Converts CurseForge mod TOML files to Modrinth equivalents with smart matching
"""

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
import threading
import queue

class ModConverter:
    def __init__(self):
        self.mods_dir = Path("mods")
        self.converted_count = 0
        self.skipped_count = 0
        self.failed_count = 0
    
    def extract_mod_name(self, toml_content: str) -> Optional[str]:
        """Extract mod name from TOML content"""
        match = re.search(r'name\s*=\s*"([^"]+)"', toml_content)
        return match.group(1) if match else None
    
    def is_curseforge_mod(self, toml_content: str) -> bool:
        """Check if mod is from CurseForge"""
        return ('mode = "metadata:curseforge"' in toml_content or 
                '[update.curseforge]' in toml_content)
    
    def clean_mod_name(self, mod_name: str) -> str:
        """Clean mod name by removing platform tags"""
        # Remove common platform indicators
        cleaned = re.sub(r'\s*\[(Forge|Fabric|NeoForge|Quilt).*?\]', '', mod_name)
        cleaned = re.sub(r'\s*\((Forge|Fabric|NeoForge|Quilt).*?\)', '', cleaned)
        return cleaned.strip()
    
    def find_matching_option(self, output: str, mod_name: str) -> Optional[str]:
        """Find matching option number from packwiz output"""
        lines = output.split('\n')
        
        print(f"  → Searching for matches for: '{mod_name}'")
        print(f"  → Available options:")
        
        # Show all available options for debugging
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\)', line):
                print(f"    {line}")
        
        # First check for starred option (packwiz's best match)
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\)', line):
                # Check if this line contains an asterisk anywhere after the number
                number_match = re.search(r'^(\d+)\)', line)
                if number_match and '*' in line:
                    print(f"  → Found starred option: {line}")
                    return number_match.group(1)
        
        # Then try exact match
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\)', line):
                # Extract option text (everything after the number, parenthesis, and optional asterisk)
                option_match = re.search(r'^\d+\)\s*\*?\s*(.+)', line)
                if option_match:
                    option_text = option_match.group(1).strip()
                    if option_text.lower() == mod_name.lower():
                        number_match = re.search(r'^(\d+)\)', line)
                        if number_match:
                            print(f"  → Found exact match: {line}")
                            return number_match.group(1)
        
        # Try partial match with cleaned name
        cleaned_name = self.clean_mod_name(mod_name)
        if cleaned_name != mod_name:
            print(f"  → Trying with cleaned name: '{cleaned_name}'")
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\)', line):
                    option_match = re.search(r'^\d+\)\s*\*?\s*(.+)', line)
                    if option_match:
                        option_text = option_match.group(1).strip()
                        if option_text.lower() == cleaned_name.lower():
                            number_match = re.search(r'^(\d+)\)', line)
                            if number_match:
                                print(f"  → Found cleaned match: {line}")
                                return number_match.group(1)
        
        # Try fuzzy match (contains) - but be more selective
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\)', line):
                option_match = re.search(r'^\d+\)\s*\*?\s*(.+)', line)
                if option_match:
                    option_text = option_match.group(1).strip()
                    # Only match if there's significant overlap
                    if (len(cleaned_name) > 3 and 
                        (cleaned_name.lower() in option_text.lower() or 
                         option_text.lower() in cleaned_name.lower())):
                        number_match = re.search(r'^(\d+)\)', line)
                        if number_match:
                            print(f"  → Found fuzzy match: {line}")
                            return number_match.group(1)
        
        print(f"  → No match found for '{mod_name}'")
        return None
    
    def read_output_threaded(self, process, output_queue):
        """Read process output in a separate thread"""
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_queue.put(line)
        except Exception as e:
            output_queue.put(f"Error reading output: {e}")
    
    def convert_mod(self, mod_name: str) -> Tuple[bool, str]:
        """Convert a single mod from CurseForge to Modrinth"""
        try:
            # Run packwiz mr add
            process = subprocess.Popen(
                ['packwiz', 'mr', 'add', mod_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Use a queue to handle output in a separate thread
            output_queue = queue.Queue()
            output_thread = threading.Thread(target=self.read_output_threaded, args=(process, output_queue))
            output_thread.daemon = True
            output_thread.start()
            
            full_output = ""
            selection_made = False
            dependency_prompt_seen = False
            waiting_for_deps = False
            
            while process.poll() is None:
                try:
                    # Get output with timeout
                    line = output_queue.get(timeout=0.1)
                    full_output += line
                    print(line, end='')
                    
                    # Check for dependency-related prompts
                    if "Finding dependencies..." in line:
                        waiting_for_deps = True
                        print("  → Detected dependency search...")
                    
                    elif "Dependencies found:" in line:
                        waiting_for_deps = True
                        print("  → Dependencies found, waiting for prompt...")
                    
                    # Check for explicit dependency prompt (multiple possible formats)
                    elif (waiting_for_deps and not dependency_prompt_seen and 
                          (re.search(r'\[Y/n\]', line, re.IGNORECASE) or
                           re.search(r'\[y/N\]', line, re.IGNORECASE) or
                           "Would you like to add them?" in line or
                           "Add dependencies?" in line or
                           (line.strip().endswith("?") and ("add" in line.lower() or "install" in line.lower())))):
                        
                        print("  → Auto-accepting dependencies (Y)")
                        process.stdin.write("Y\n")
                        process.stdin.flush()
                        dependency_prompt_seen = True
                        waiting_for_deps = False
                        continue

                    
                    # Check if we hit a mod selection prompt - ONLY respond to "Choose a number:"
                    if "Choose a number:" in line and not selection_made:
                        # Wait a bit for any remaining output to be flushed
                        time.sleep(0.1)
                        
                        # Look for a matching option
                        matching_option = self.find_matching_option(full_output, mod_name)
                        
                        if matching_option:
                            print(f"  → Auto-selecting option {matching_option}")
                            process.stdin.write(f"{matching_option}\n")
                            process.stdin.flush()
                            selection_made = True
                        else:
                            print(f"  → No good match found, cancelling")
                            process.stdin.write("0\n")
                            process.stdin.flush()
                            selection_made = True
                    
                except queue.Empty:
                    # Check if we're stuck waiting for dependencies
                    if (waiting_for_deps and not dependency_prompt_seen):
                        current_time = time.time()
                        if not hasattr(self, '_last_deps_time'):
                            self._last_deps_time = current_time
                        
                        # If we've been waiting for more than 2 seconds, assume we need to respond
                        if current_time - self._last_deps_time > 2:
                            print("  → Timeout waiting for dependency prompt, sending Y")
                            process.stdin.write("Y\n")
                            process.stdin.flush()
                            dependency_prompt_seen = True
                            waiting_for_deps = False
                            self._last_deps_time = current_time
                    
                    continue
            
            # Get any remaining output
            while not output_queue.empty():
                try:
                    line = output_queue.get_nowait()
                    full_output += line
                    print(line, end='')
                except queue.Empty:
                    break
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0 and "successfully added" in full_output.lower():
                return True, "Successfully converted"
            elif "no valid versions found" in full_output:
                return False, "No valid versions found"
            elif "failed to add project" in full_output:
                return False, "Failed to add project"
            elif "project selection cancelled" in full_output:
                return False, "Project selection cancelled"
            else:
                return False, "No suitable match found"
                
        except FileNotFoundError:
            return False, "packwiz command not found"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def process_all_mods(self):
        """Process all mod files in the mods directory"""
        if not self.mods_dir.exists():
            print("Error: mods directory not found!")
            return 1
        
        toml_files = list(self.mods_dir.glob("*.pw.toml"))
        total_mods = len(toml_files)
        
        if total_mods == 0:
            print("No .pw.toml files found in mods directory!")
            return 0
        
        print(f"Found {total_mods} mod files to process")
        print("=" * 50)
        
        for counter, file_path in enumerate(toml_files, 1):
            try:
                # Read TOML file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract mod name
                mod_name = self.extract_mod_name(content)
                
                if not mod_name:
                    print(f"[{counter}/{total_mods}] ⚠️  {file_path.name}: Couldn't extract mod name")
                    self.failed_count += 1
                    continue
                
                # Check if it's a CurseForge mod
                if not self.is_curseforge_mod(content):
                    print(f"[{counter}/{total_mods}] ⏭️  {mod_name}: Already converted")
                    self.skipped_count += 1
                    continue
                
                print(f"[{counter}/{total_mods}] 🔄 Processing: {mod_name}")
                
                # Convert the mod
                success, message = self.convert_mod(mod_name)
                
                if success:
                    print(f"  ✅ {message}")
                    self.converted_count += 1
                else:
                    print(f"  ❌ {message}")
                    self.failed_count += 1
                
                print()  # Add spacing between mods
                
            except Exception as e:
                print(f"[{counter}/{total_mods}] ⚠️  Error processing {file_path.name}: {e}")
                self.failed_count += 1
        
        # Print summary
        print("=" * 50)
        print("CONVERSION SUMMARY:")
        print(f"✅ Successfully converted: {self.converted_count}")
        print(f"⏭️  Already converted: {self.skipped_count}")
        print(f"❌ Failed/Skipped: {self.failed_count}")
        print(f"📊 Total processed: {self.converted_count + self.skipped_count + self.failed_count}")
        
        return 0

def main():
    converter = ModConverter()
    return converter.process_all_mods()

# ──── entry‑point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    raise SystemExit(main())