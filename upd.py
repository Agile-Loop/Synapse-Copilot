import mysql.connector
import random
from flask import Flask, request, render_template
import os
app = Flask(__name__)

# Replace with your database connection details
db_config = {
    'host': 'localhost',
    'database': 'llamadb',
    'user': 'root',
    'password': '',
}

# Connect to the MySQL server
conn = mysql.connector.connect(**db_config)

try:
    # Create a MySQL cursor
    cursor = conn.cursor()

    # Replace with your UPDATE query
    user_id_to_update = int(input("Enter your id: "))
    new_token_value = input("Enter the new token: ")

    update_query = f"UPDATE credentials SET token = '{new_token_value}' WHERE user_id = {user_id_to_update};"

    # Execute the UPDATE query
    cursor.execute(update_query)

    # Commit the changes
    conn.commit()

    print(f"Token updated successfully for user ID '{user_id_to_update}'.")

finally:
    # Close the cursor and connection
    cursor.close()
    conn.close()