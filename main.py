from Website import create_app

app = create_app()

if __name__ == '__main__':  
    app.run(debug=True) #debug feat means it refreshes the server automatically when you make changes to the code.
