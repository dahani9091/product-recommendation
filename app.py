import streamlit as st
import pandas as pd
import pickle


# Security
#passlib,hashlib,bcrypt,scrypt
import hashlib
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False


def recommender(brand_name,keywords=None,price_min=0,price_max=1000000,flavors=None):

    dataset = []
    df = pd.read_csv('tokens/combine_token_for_app.csv')
    use_cos = pickle.load(open('model/cos_similarity.pkl','rb'))
    if keywords:
        keywords = keywords.split(';')
        keywords = [ky.strip() for ky in keywords]
    try:
        makeup_id = df[df['brand_name']==brand_name].index.values[0]
    except :
        return dataset
    scores = list(enumerate(use_cos[makeup_id]))
    sorted_scores = sorted(scores, key = lambda x: x[1], reverse=True)

    items = [item[0] for item in sorted_scores]
    df = df.iloc[items]
    df["number_of_flavors"].replace({"Unavailable": 1}, inplace=True)
    df["number_of_flavors"] = pd.to_numeric(df["number_of_flavors"])
    if keywords != None :
        df = df[(df['product_description'].str.contains('|'.join(keywords))) & (df['price']>=price_min) & (df['price']<=price_max)]
    else:
        df = df[(df['price']>=price_min) & (df['price']<=price_max) ]
    df.drop_duplicates(subset=['id'], keep='first',inplace=True)
    df = df.reset_index(drop=True)
    if flavors != None :
        for i in range(df.shape[0]) :
            if df['top_flavor_rated'][i].strip() not in flavors :
                df = df.drop([i])
            else:
                dataset.append({'Brand':df['brand_name'][i],'price':df['price'][i],'flavor':df['top_flavor_rated'][i]})
    return dataset


###############################################################################################################
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')

def add_userdata(username,password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
    conn.commit()

def login_user(username,password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data

############################################################################################################

def main():
    """Login"""

    st.title("Login")

    menu = ["Home","Login","SignUp"]
    choice = st.sidebar.selectbox("Menu",menu)

    if choice == "Home":
        st.subheader("Home")

    elif choice == "Login":
        st.subheader("Login Section")

        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password",type='password')
        if st.sidebar.checkbox("Login"):
            # if password == '12345':
            create_usertable()
            hashed_pswd = make_hashes(password)

            result = login_user(username,check_hashes(password,hashed_pswd))
            if result:

                st.success("Logged In as {}".format(username))

                task = st.selectbox("Task",["Personal information","Analytics"])
                if task == "Personal information":
                    st.subheader("Information")

                elif task == "Analytics":
                    def get_brand_names():
                        df = pd.read_csv('tokens/combine_token_for_app.csv')
                        df = df.drop_duplicates(subset=['brand_name'], keep='first')
                        return list(df['brand_name'])
                    st.subheader("Analytics")
                    st.title("Suppliment Recommandation")

                    with st.form(key = "form1"):
                        brand_name = st.selectbox(label = "Enter the product brand",options=get_brand_names())
                        keywords = st.text_input(label = "Enter the keywords (They should be separated by ';' | Example : keyword1;keyword2;keyword3 )")
                        price = st.slider("Enter your budget", 1, 1000,(1, 1000))
                        flavors_options_single = st.multiselect(
                                'Enter single flavorss',
                                ['unflavored', 'strawberry', 'lemonade', 'cookie', 'pineapple', 'grape', 'raspberry', 'mint', 'pina colada', 'blueberry', 'cherry', 'candy', 'gingerbread', 'chocolate', 'peanut butter', 'maple waffle', 'fruit', 'orange', 'lemon', 'mango', 'peach', 'watermelon', 'coconut', 'vanilla', 'banana', 'apple', 'caramel', 'hazelnut', 'margarita', 'cinnamon', 'coffee', 'buttermilk', 'kiwi', 'dragon fruit', 'brownie', 'rocky road'])

                        flavors_options_mix = st.multiselect(
                        'Enter mix flavors',
                        ['lemonade + raspberry', 'lemonade + blueberry', 'lemonade + strawberry', 'chocolate + mint', 'chocolate + peanut butter', 'chocolate + coconut', 'chocolate + hazelnut', 'mango + peach', 'mango + lemon', 'mango + orange', 'mango + pineapple', 'banana + peanut butter', 'cherry + watermelon', 'candy + watermelon', 'cookie + peanut butter', 'coffee + caramel', 'apple + cinnamon', 'strawberry + pina colada', 'vanilla + caramel'])
                        submit = st.form_submit_button(label = "Submit")
                    dataset = []
                    if submit :
                        if keywords.replace('Example : keyword1;keyword2;keyword3',"").strip() != "" :
                            dataset = recommender(brand_name.strip(),keywords,int(price[0]),int(price[1]),flavors_options_single+flavors_options_mix)
                        else:

                            dataset = recommender(brand_name.strip(),price_min=int(price[0]),price_max=int(price[1]),flavors=flavors_options_single+flavors_options_mix)
                        if len(dataset) >10 :
                            df = pd.DataFrame(dataset[:10])
                            st.table(df)
                        elif len(dataset) == 0:
                            st.write("No results found")

                        else:
                            df = pd.DataFrame(dataset)
                            st.table(df)      
                        submit = False
                
            else:
                st.warning("Incorrect Username/Password")





    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password",type='password')

        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user,make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")

if __name__ == '__main__':
	main()
