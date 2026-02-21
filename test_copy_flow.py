import pyperclip
import time
import os

def test_copy_flow():
    print("Simulating copy of problem data...")
    test_data = "input = [1,2,3,6,4]\noutput = [1,2,3,4,6]"
    pyperclip.copy(test_data)
    print(f"Copied: {test_data}")
    print("Wait 2 seconds for monitor to detect...")
    time.sleep(2)
    print("Check logs for 'Clipboard question detected' and 'Processing TECH request'...")

if __name__ == "__main__":
    test_copy_flow()
