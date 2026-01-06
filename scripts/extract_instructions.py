#!/usr/bin/env python3
"""
Extract instructions from HTML pages in Markdown format for GitHub Copilot consumption.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import subprocess
from bs4 import BeautifulSoup
import re

def call_copilot_api(prompt: str) -> Optional[str]:
    """
    Call the GitHub Copilot API to extract instructions.
    
    Args:
        prompt: The prompt to send to Copilot
        
    Returns:
        Markdown formatted response or None if failed
    """
    try:
        # Use GitHub CLI with Copilot extension
        # Note: Requires 'gh copilot' CLI to be installed/available
        result = subprocess.run(
            ["gh", "models", "run", "openai/gpt-4.1", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Error calling Copilot API: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Exception calling Copilot API: {e}")
        return None


def extract_text_from_html(html_content: str) -> str:
    """
    Extract clean text from HTML content.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Clean text content
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return html_content


def extract_instructions_from_html(html_content: str) -> str:
    """
    Extract instructions from HTML content and format as Markdown for Copilot.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Markdown formatted instructions
    """
    # Extract text from HTML
    clean_text = extract_text_from_html(html_content)
    
    # Truncate to reasonable size for API
    text_preview = clean_text[:4000]
    
    prompt = f"""Extract clear, actionable instructions from this content. Format the output as markdown that GitHub Copilot can consume.

Structure your response as:
1. A clear title (as # Markdown heading)
2. Prerequisites section (if applicable)
3. Step-by-step instructions (numbered list)
4. Warnings or Important Notes (if applicable)
5. Key Concepts (brief explanations of technical terms)

Content to analyze:
{text_preview}

Provide ONLY the markdown output, no additional explanation."""

    # For now, generate a template markdown structure
    # In production, this would call the actual Copilot API and return the result
    markdown = call_copilot_api(prompt)
    
    if markdown:
        return markdown
    else:
        # Fallback template if API fails
        return generate_markdown_template(clean_text)


def generate_markdown_template(text_content: str) -> str:
    """
    Generate a markdown template when API is unavailable.
    
    Args:
        text_content: Clean text content from HTML
        
    Returns:
        Markdown formatted template
    """
    # Extract first meaningful line as title
    lines = [l for l in text_content.split('\n') if l.strip() and len(l.strip()) > 10]
    title = lines[0] if lines else "Instructions"
    
    markdown = f"""# {title}

## Prerequisites

- Placeholder: Add prerequisites here

## Instructions

1. Step 1: Placeholder instruction
2. Step 2: Placeholder instruction
3. Step 3: Placeholder instruction

## Important Notes

⚠️ **Note:** This is a template. Replace with actual extracted instructions when Copilot API is integrated.

## Key Concepts

- **Concept 1**: Description placeholder
- **Concept 2**: Description placeholder

---
*Generated instructions - Review and verify before using*
"""
    return markdown


def process_pages_directory(pages_dir: str = "pages", output_dir: str = "instructions") -> None:
    """
    Process all HTML files in the pages directory.
    
    Args:
        pages_dir: Directory containing HTML files
        output_dir: Directory to save extracted instructions
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    
    # Create output directory
    output_path.mkdir(exist_ok=True)
    
    # Process each HTML file
    html_files = list(pages_path.glob("*.html"))
    print(f"Found {len(html_files)} HTML files to process")
    
    if not html_files:
        print("No HTML files found in pages directory")
        return
    
    for html_file in html_files:
        print(f"\nProcessing: {html_file.name}")
        
        try:
            # Read HTML content
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Extract instructions
            markdown_instructions = extract_instructions_from_html(html_content)
            
            # Save to output file
            output_file = output_path / f"{html_file.stem}_instructions.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown_instructions)
            
            print(f"  ✓ Saved to: {output_file}")
            
        except Exception as e:
            print(f"  ✗ Error processing {html_file.name}: {e}")
            continue


if __name__ == "__main__":
    process_pages_directory()
    print("\n✓ All files processed!")
