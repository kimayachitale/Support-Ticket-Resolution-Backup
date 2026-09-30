import json

# JSON file मधून orders वाचणे
with open("mock_orders.json", "r") as file:
    orders = json.load(file)

# Order शोधण्यासाठी function
def order_lookup(order_id):
    for order in orders:
        if order["order_id"] == order_id:
            return order
    return None

# Testing
order_id = input("Enter Order ID: ")

result = order_lookup(order_id)

if result:
    print("\nOrder Found!")
    print(f"Order ID: {result['order_id']}")
    print(f"Item: {result['item']}")
    print(f"Status: {result['status']}")
    print(f"Amount: ₹{result['amount']}")
    print(f"Payment Method: {result['payment_method']}")
else:
    print("\nOrder Not Found!")