import json

def extract_trade_details(order_response, going):
	try:
		# Extract data from the order_response object
		order = order_response["orders"][0]  # Assuming there is only one order in the response
		id = order["id"]
		side = order["side"]
		time = order["created_at"]
		base_units = float(order["total_quantity"])
		quote_units = float(order["fee_amount"])
		avg_price = float(order["avg_price"])

		return avg_price, quote_units, id

	except (KeyError, IndexError) as e:
		print(f"Error extracting data from order_response: {e}")
	except Exception as e:
		print(f"An unexpected error occurred: {e}")    
		
def extract_updated_trade_details(order_response, going):
	try:
		# Extract data from the order_response object
		order = order_response
		id = order["id"]
		side = order["side"]
		time = order["created_at"]
		base_units = float(order["total_quantity"])
		quote_units = float(order["fee_amount"])
		avg_price = float(order["avg_price"])
		
		return avg_price, quote_units, id

	except (KeyError, IndexError) as e:
		print(f"Error extracting data from order_response: {e}")
	except Exception as e:
		print(f"An unexpected error occurred: {e}")
