#!/usr/bin/env python3
"""
Robust mod file comparison script
Compares .jar files in mods directory against TOML configuration files
"""

import os
import sys
from pathlib import Path
import re
from typing import Dict, List, Tuple, Set
import difflib

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # fallback for older Python versions
    except ImportError:
        print("Error: tomllib/tomli not available. Install with: pip install tomli")
        sys.exit(1)


def safe_read_toml(file_path: Path) -> Dict:
    """Safely read a TOML file with error handling."""
    try:
        with open(file_path, 'rb') as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return {}


def extract_mod_info_from_toml(toml_content: Dict) -> Dict:
    """Extract mod information from TOML content."""
    info = {
        'name': toml_content.get('name', 'Unknown'),
        'filename': toml_content.get('filename', ''),
        'side': toml_content.get('side', ''),
        'mod_id': '',
        'version': ''
    }
    
    # Try to extract mod-id and version from update section
    if 'update' in toml_content:
        update_section = toml_content['update']
        if 'modrinth' in update_section:
            modrinth = update_section['modrinth']
            info['mod_id'] = modrinth.get('mod-id', '')
            info['version'] = modrinth.get('version', '')
        elif 'curseforge' in update_section:
            curseforge = update_section['curseforge']
            info['mod_id'] = str(curseforge.get('project-id', ''))
            info['version'] = str(curseforge.get('file-id', ''))
    
    return info


def normalize_filename(filename: str) -> str:
    """Normalize filename by removing version numbers and common suffixes."""
    # Remove .jar extension
    base = filename.replace('.jar', '')
    
    # Remove common version patterns
    patterns = [
        r'-\d+\.\d+\.\d+.*$',  # -1.21.4, -1.21.4-forge, etc.
        r'-v\d+\.\d+.*$',      # -v1.21, -v1.21.4, etc.
        r'-\d+\.\d+.*$',       # -1.21, -1.21-forge, etc.
        r'-forge.*$',          # -forge, -forge-1.21, etc.
        r'-neoforge.*$',       # -neoforge, -neoforge-1.21, etc.
        r'-fabric.*$',         # -fabric, -fabric-1.21, etc.
        r'-quilt.*$',          # -quilt variants
        r'-\d+\.\d+\.\d+\+.*$' # -1.21.4+forge, etc.
    ]
    
    normalized = base
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    return normalized.lower()


def find_similar_names(target: str, candidates: List[str], threshold: float = 0.6) -> List[Tuple[str, float]]:
    """Find similar names using difflib."""
    similarities = []
    for candidate in candidates:
        ratio = difflib.SequenceMatcher(None, target.lower(), candidate.lower()).ratio()
        if ratio >= threshold:
            similarities.append((candidate, ratio))
    
    return sorted(similarities, key=lambda x: x[1], reverse=True)


def main():
    # Define paths
    mods_dir = Path(r"S:\Portable\Programs\PrismLauncher\instances\JSPCD6Minecolonies25Q3PrismINST\minecraft\mods")
    toml_dir = Path(r"S:\Portable\Code\JSPCD6Packwiz\mods")
    
    # Validate directories exist
    if not mods_dir.exists():
        print(f"Error: Mods directory does not exist: {mods_dir}")
        sys.exit(1)
    
    if not toml_dir.exists():
        print(f"Error: TOML directory does not exist: {toml_dir}")
        sys.exit(1)
    
    print("=== MOD FILE COMPARISON REPORT ===\n")
    print(f"Mods directory: {mods_dir}")
    print(f"TOML directory: {toml_dir}")
    print("-" * 60)
    
    # Get all .jar files
    jar_files = list(mods_dir.glob("*.jar"))
    print(f"Found {len(jar_files)} .jar files in mods directory")
    
    # Get all .toml files
    toml_files = list(toml_dir.glob("*.toml"))
    print(f"Found {len(toml_files)} .toml files in packwiz directory")
    print()
    
    # Read all TOML files and extract mod info
    toml_mods = {}
    toml_filenames = []
    
    for toml_file in toml_files:
        toml_content = safe_read_toml(toml_file)
        if toml_content:
            mod_info = extract_mod_info_from_toml(toml_content)
            toml_mods[toml_file.name] = mod_info
            if mod_info['filename']:
                toml_filenames.append(mod_info['filename'])
    
    # Analysis results
    exact_matches = []
    version_mismatches = []
    missing_from_toml = []
    missing_from_mods = []
    potential_matches = []
    
    # Check each jar file against TOML files
    jar_filenames = [jar.name for jar in jar_files]
    
    for jar_file in jar_files:
        jar_name = jar_file.name
        found_exact = False
        found_similar = False
        
        # Check for exact filename match
        for toml_name, mod_info in toml_mods.items():
            if mod_info['filename'] == jar_name:
                exact_matches.append((jar_name, toml_name, mod_info))
                found_exact = True
                break
        
        if not found_exact:
            # Check for similar filenames (potential version mismatches)
            normalized_jar = normalize_filename(jar_name)
            
            for toml_name, mod_info in toml_mods.items():
                if mod_info['filename']:
                    normalized_toml = normalize_filename(mod_info['filename'])
                    
                    if normalized_jar == normalized_toml:
                        version_mismatches.append((jar_name, mod_info['filename'], toml_name, mod_info))
                        found_similar = True
                        break
            
            if not found_similar:
                # Try fuzzy matching
                similar_names = find_similar_names(jar_name, toml_filenames, threshold=0.7)
                if similar_names:
                    # Find the corresponding TOML file
                    for toml_name, mod_info in toml_mods.items():
                        if mod_info['filename'] == similar_names[0][0]:
                            potential_matches.append((jar_name, similar_names[0][0], similar_names[0][1], toml_name, mod_info))
                            found_similar = True
                            break
        
        if not found_exact and not found_similar:
            missing_from_toml.append(jar_name)
    
    # Check for TOML files without corresponding jar files
    for toml_name, mod_info in toml_mods.items():
        if mod_info['filename'] and mod_info['filename'] not in jar_filenames:
            # Check if it's just a version mismatch we already found
            already_found = any(mod_info['filename'] == item[1] for item in version_mismatches)
            if not already_found:
                missing_from_mods.append((mod_info['filename'], toml_name, mod_info))
    
    # Print results
    print("=== EXACT MATCHES ===")
    if exact_matches:
        for jar_name, toml_name, mod_info in exact_matches:
            print(f"✓ {jar_name}")
            print(f"  → {toml_name} ({mod_info['name']})")
    else:
        print("No exact matches found")
    print()
    
    print("=== VERSION MISMATCHES ===")
    if version_mismatches:
        for jar_name, toml_filename, toml_name, mod_info in version_mismatches:
            print(f"⚠ {jar_name}")
            print(f"  Expected: {toml_filename}")
            print(f"  TOML: {toml_name} ({mod_info['name']})")
            print()
    else:
        print("No version mismatches found")
    print()
    
    print("=== POTENTIAL MATCHES (Similar Names) ===")
    if potential_matches:
        for jar_name, toml_filename, similarity, toml_name, mod_info in potential_matches:
            print(f"? {jar_name}")
            print(f"  Similar to: {toml_filename} (similarity: {similarity:.2f})")
            print(f"  TOML: {toml_name} ({mod_info['name']})")
            print()
    else:
        print("No potential matches found")
    print()
    
    print("=== MISSING FROM TOML (jar files without TOML) ===")
    if missing_from_toml:
        for jar_name in missing_from_toml:
            print(f"✗ {jar_name}")
    else:
        print("All jar files have corresponding TOML entries")
    print()
    
    print("=== MISSING FROM MODS (TOML files without jar files) ===")
    if missing_from_mods:
        for toml_filename, toml_name, mod_info in missing_from_mods:
            print(f"✗ {toml_filename}")
            print(f"  From: {toml_name} ({mod_info['name']})")
    else:
        print("All TOML files have corresponding jar files")
    print()
    
    # Summary
    print("=== SUMMARY ===")
    print(f"Total jar files: {len(jar_files)}")
    print(f"Total TOML files: {len(toml_files)}")
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Version mismatches: {len(version_mismatches)}")
    print(f"Potential matches: {len(potential_matches)}")
    print(f"Missing from TOML: {len(missing_from_toml)}")
    print(f"Missing from mods: {len(missing_from_mods)}")
    
    if version_mismatches or missing_from_toml or missing_from_mods:
        print("\n⚠ Issues found that need attention!")
        return 1
    else:
        print("\n✓ All files are properly matched!")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)