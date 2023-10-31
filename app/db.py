import streamlit as st
from sqlalchemy.sql import text

if st.secrets["deploy_location"]["location"]=="local":
    conn = st.connection('local', type='sql')

else:
    # e.g. "mysql://jdoe:******@staging.acmecorp.com:3306/staging_db"
    """
    dialect = st.secrets["connections_users_db"]["dialect"]
    host = st.secrets["connections_users_db"]["host"]
    port = st.secrets["connections_users_db"]["port"]
    database = st.secrets["connections_users_db"]["database"]
    username = st.secrets["connections_users_db"]["username"]
    password = st.secrets["connections_users_db"]["password"]
    connection_string = dialect+"://"+username+":"+password+"@"+host+":"+port+"/"+database
    conn = st.experimental_connection(connection_string, type='sql')
    """
    print("Before connection")
    conn = st.connection('users_db', type='sql')
    print(conn)
    print("After connection")

# Retrieve all user's data from database
def get_all_users():
    with conn.session as s:
        s.execute(text('CREATE TABLE IF NOT EXISTS drea_users (username varchar(255) NOT NULL PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL, passwordhash TEXT NOT NULL, approved BOOLEAN NOT NULL);'))
    drea_users = conn.query('select * from drea_users where approved = TRUE')
    return drea_users.to_dict('index')

# Update all user's data in database
def update_all_users(usernames):
    # Insert some data with conn.session.
    with conn.session as s:
        for username in usernames['usernames']:
            s.execute(
                text('INSERT INTO drea_users (username, email, name, passwordhash, approved) VALUES (:username, :email, :name, :passwordhash, TRUE);'),
                params=flatten(username, usernames)
            )
        s.commit()

# Flatten dictionary to database row
def flatten(username, users):
    print("users::::", users)
    return {
            'username': username,
            'email': users['usernames'][username]['email'],
            'name': users['usernames'][username]['name'],
            'passwordhash': users['usernames'][username]['password'],
        }

# Add one user retrieved from database row to the usernames dictionary
def add_user(user, usernames):
    usernames.setdefault('usernames', {})
    usernames['usernames'].update({ 
                                user['username'] : { 
                                                        'email'     : user['email'],
                                                        'name'      : user['name'],
                                                        'password'  : user['passwordhash']
                                                   }
                             })

# Add several users retrieved from database rows to the usernames dictionary
def add_users(users, usernames):
    for idx in users:
        add_user(users[idx], usernames)

def get_credentials():
    usernames = {}
    add_users(get_all_users(), usernames)
    return usernames if usernames else {'usernames': {}}

if __name__ == '__main__':
    print( get_all_users() )
