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
    'password': '123456',
}

# Connect to the MySQL server
conn = mysql.connector.connect(**db_config)
# print(conn)
# exit()

@app.route('/db_token', methods=["GET", "POST"])
def df_func():
    if request.method == "POST":
        inp_t = request.form["token"]
        if inp_t is not None:
        # Create a MySQL cursor
            cursor = conn.cursor()

            numb = random.randint(1, 1000)
            value_to_check = inp_t

            query = "INSERT INTO credentials (user_id, token) VALUES (%s, %s)"

            # Execute the update query
            cursor.execute(query, (numb, value_to_check))

            # Commit the changes
            conn.commit()

            dic = {
                 "Your_id": numb,
                 "token": value_to_check
            }

            # cursor.close()
            # conn.close()
            return dic
            
        else:
             return "Enter the token"
        


if __name__ == '__main__':
     app.run(port=8986)



# tok = input("Enter your token: ")
# if tok is not None:
#     # Replace with your SELECT query
#     value_to_check = tok
#     select_query = f"SELECT * FROM credentials WHERE token = '{value_to_check}';"

#     # Execute the SELECT query
#     cursor.execute(select_query)

#     # Fetch the result
#     result = cursor.fetchone()
#     print(result," dcdc")
#     if result:
#         user_id = result[0]
#         print(f"User ID {user_id} for token is '{value_to_check}' ")
#     else:
#         print(f"No matching user ID found for token '{value_to_check}' or token is not true.")


        # Replace with your SELECT query
        
        # select_query = f"SELECT * FROM credentials WHERE token = '{value_to_check}';"

        # Execute the SELECT query
        # cursor.execute(select_query)

        # # Fetch the result
        # result = cursor.fetchone()

        # if result is True:
        #     print(f"Here is your id: {result[0]}")
        # else:
        #     print(f"Value '{value_to_check}' does not exist in the database.")


# except
    # user_d = int(input("Enter the user id: "))
    # if user_d is not None:
    #     ser_qu = f"SELECT * FROM credentials WHERE user_id = {user_d};"
    #     cursor.execute(ser_qu)
    #     res = cursor.fetchone()
    #     res_t = res[1]
    #     print(f"your token {res_t}")
    # else:
    #     print("provide the id")

# finally:
#     # Close the cursor and connection
#     cursor.close()
#     conn.close()