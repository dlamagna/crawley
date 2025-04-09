#!/usr/bin/env python3
"""
send_to_prompt.py

This script:
1. Takes in the following arguments:
   - input directory
   - prompt URL
   - output directory (default: prompted/)
   - debug directory (default: debug)
   - verbose (boolean)
2. Iterates over all .md files in the input directory (recursively).
3. Sends the contents of each file via POST to an API (prompt URL).
4. Saves the JSON response in the output directory, preserving subfolder structure.
   The output filename is the same as the .md file name, but with a .json extension.
5. Logs all activity using DualLogger and log_print from crawl_tools.
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path

from crawl_tools import DualLogger, log_print


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send Markdown files to a prompt API and store JSON responses."
    )
    parser.add_argument(
        "-i", "--input-directory",
        required=True,
        help="Path to the input directory containing .md files."
    )
    parser.add_argument(
        "-p", "--prompt-url",
        required=True,
        help="URL endpoint to which the markdown contents will be sent (HTTP POST)."
    )
    parser.add_argument(
        "-o", "--output-directory",
        default="prompted",
        help="Path to the base output directory for the JSON responses (default: 'prompted')."
    )
    parser.add_argument(
        "-d", "--debug-directory",
        default="debug",
        help="Path to the directory where debug logs will be stored (default: 'debug')."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose mode. Logs will also be printed to the console."
    )
    return parser.parse_args()


def send_file_to_api(file_path: str, prompt_url: str) -> dict:
    """
    Reads the .md file at file_path, sends it to the prompt_url via POST,
    using the updated JSON format:
    {
      "chat": [
        { "role": "user", "content": "<file contents>" }
      ]
    }
    and returns the JSON response.
    """
    # Read markdown content
    with open(file_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Prepare request payload
    payload = {
        "chat": [
            {
                "role": "user",
                "content": markdown_content
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "X-Authorization": "freedom"
    }

    # Send request
    response = requests.post(prompt_url, json=payload, headers=headers)
    response.raise_for_status()  # Raise HTTPError if the request was unsuccessful

    # Return parsed JSON response
    return response.json()


def main():
    args = parse_args()

    os.makedirs(args.debug_directory, exist_ok=True)
    # The log file name can be anything. Let's store a single file for this script:
    log_file_path = os.path.join(args.debug_directory, "send_to_prompt")

    # Replace stdout with DualLogger to capture logs in a file and optionally stdout
    sys.stdout = DualLogger(log_file_path, verbose=args.verbose)

    # Log the received arguments
    log_print(f"[DEBUG] Input directory: {args.input_directory}")
    log_print(f"[DEBUG] Prompt URL: {args.prompt_url}")
    log_print(f"[DEBUG] Output directory: {args.output_directory}")
    log_print(f"[DEBUG] Debug directory: {args.debug_directory}")
    log_print(f"[DEBUG] Verbose: {args.verbose}")

    # Absolute paths for clarity
    input_dir = os.path.abspath(args.input_directory)
    output_dir = os.path.abspath(args.output_directory)
    prompt_url = args.prompt_url

    # Walk the input directory for .md files
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(".md"):
                file_path = os.path.join(root, filename)

                # Build mirrored output path
                relative_path = os.path.relpath(file_path, start=input_dir)
                output_file_path = os.path.join(output_dir, relative_path)
                output_file_path = os.path.splitext(output_file_path)[0] + ".json"

                # Ensure the output directory structure exists
                Path(os.path.dirname(output_file_path)).mkdir(parents=True, exist_ok=True)

                log_print(f"[INFO] Processing file: {file_path}")

                # Send to API and save response
                try:
                    response_json = send_file_to_api(file_path, prompt_url)
                    with open(output_file_path, "w", encoding="utf-8") as out_f:
                        if isinstance(response_json, (dict, list)):
                            json.dump(response_json, out_f, indent=2, ensure_ascii=False)
                        else:
                            out_f.write(str(response_json))

                    log_print(f"[DEBUG] Output JSON saved to: {output_file_path}")

                except Exception as e:
                    log_print(f"[ERROR] Failed to process file {file_path}: {e}")

    log_print("[DEBUG] Finished processing all markdown files.")


if __name__ == "__main__":
    main()
