import sqlite3


def get_config(user_id, name="Anonymous User"):
    conn = sqlite3.connect('stocker.db')
    config = {
        "id": user_id,
        "name": name,
        "portfolio": {}
    }
    user_rows = conn.execute(
        'SELECT NAME FROM USER WHERE ID={};'.format(user_id)).fetchall()
    if len(user_rows) == 1:
        config["name"] = user_rows[0][0]
        portfolio_rows = conn.execute(
            'SELECT SYMBOL, NUM_SHARES, MARGIN FROM STOCK WHERE USERID={};'.format(user_id)).fetchall()
        for row in portfolio_rows:
            symbol = row[0]
            num_shares = int(row[1])
            margin = float(row[2])
            config["portfolio"][symbol] = {
                "num_shares": num_shares,
                "margin": margin
            }
        newuser = False
    else:
        conn.execute(
            'INSERT INTO USER (ID, NAME) VALUES ({}, "{}");'.format(user_id, name))
        newuser = True
    conn.commit()
    conn.close()
    return newuser, config
