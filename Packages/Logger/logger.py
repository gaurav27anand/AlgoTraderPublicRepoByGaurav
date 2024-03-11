import os
from datetime import datetime

def print_log_file(symbol, id, exchange, message):
    if exchange == "coindcx":
        file_path = r"C:\Users\gaura\OneDrive\Desktop\Algo Trader Bots\Cryptos\Logs\coindcx\\"
        # Check if the file exists
        file_name = os.path.join(file_path, f"{symbol}_{id}_{datetime.now().strftime('%Y-%m-%d')}.txt")
        if not os.path.exists(file_name):
            # Create a new file if it doesn't exist
            with open(file_name, "w", encoding='utf-8') as file:
                file.write("File created on: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        # Open the file in append mode
        with open(file_name, "a", encoding='utf-8') as file:
            print(f"{message}", file=file)
            print(f"\n ---------------------------------------------------------------\n", file=file)
        
        file.close()
    
    elif exchange == "wazirx":
        file_path = r"C:\Users\gaura\OneDrive\Desktop\Algo Trader Bots\Logs\wazirx\\"
        # Check if the file exists
        file_name = os.path.join(file_path, f"{symbol}_{id}_{datetime.now().strftime('%Y-%m-%d')}.txt")
        if not os.path.exists(file_name):
            # Create a new file if it doesn't exist
            with open(file_name, "w", encoding='utf-8') as file:
                file.write("File created on: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        # Open the file in append mode
        with open(file_name, "a", encoding='utf-8') as file:
            print(f"{message}", file=file)
            print(f"\n ---------------------------------------------------------------\n", file=file)
        
        file.close()
        
    
def print_centered_box(symbol="", id="NA", type="star", content="", exchange="coindcx"):
    # Calculate the padding on both sides
    box_width = min(len(content) + 15, 180)
    padding = (box_width - len(content) - 4) // 2  # 4 accounts for the extra characters and spaces
    # Create the centered box based on input
    if type == "hyphen":
        box_line = f"{'-' * box_width}"
    elif type == "plus":
        box_line = f"{'+' * box_width}"
    elif type == "star":
        box_line = f"{'*' * box_width}"
    elif type == "equal":
        box_line = f"{'=' * box_width}"
    elif type == "dot":
        box_line = f"{'. ' * box_width}"
    else:
        box_line = f"{'_' * box_width}"

    content_line = f"{' ' * padding}\t {content} \t{' ' * padding}"

    # Print the box using UTF-8 encoding
    print("\n")
    print(box_line.encode('utf-8').decode('utf-8'))
    print(content_line.encode('utf-8').decode('utf-8'))
    print(box_line.encode('utf-8').decode('utf-8'))
    print_log_file(symbol=symbol, id=id, exchange="coindcx", message=content.encode('utf-8').decode('utf-8'))

