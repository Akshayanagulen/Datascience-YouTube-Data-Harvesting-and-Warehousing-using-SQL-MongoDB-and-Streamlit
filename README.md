Project Title: YouTube Data Harvesting and Warehousing using SQL, MongoDB and Streamlit
Skills take away From This Project: Python scripting, Data Collection,
MongoDB, Streamlit, API integration, Data Management using MongoDB (Atlas) and SQL 

Streamlit application that allows users to access and analyze data from multiple YouTube channels. 

Approach: 

Set up a Streamlit app: 
Streamlit is a great choice for building data visualization and analysis tools quickly and easily. 
I have used Streamlit to create a simple UI where users can enter a YouTube channel ID, view the channel details, and select channels to migrate to the data warehouse.

Connect to the YouTube API: 
I have used the YouTube API to retrieve channel and video data. 
I used the Google API client library for Python to make requests to the API.

Store data in a MongoDB data lake: 
Once you retrieve the data from the YouTube API, we can store it in a MongoDB data lake. 
MongoDB is a great choice for a data lake because it can handle unstructured and semi-structured data easily.

Migrate data to a SQL data warehouse: 
After the collected data for multiple channels, you can migrate it to a SQL data warehouse. 
I have used PostgreSQL for this.

Query the SQL data warehouse: 
I have used SQL queries to join the tables in the SQL data warehouse and retrieve data for specific channels based on user input. 
You can use a Python SQL library to interact with the SQL database.

Display data in the Streamlit app: 
Finally, we can display the retrieved data in the Streamlit app. 
Streamlit's data visualization features to create charts and graphs to help users analyze the data.

Overall, this approach involves building a simple UI with Streamlit, retrieving data from the YouTube API, 
storing it in a MongoDB data lake, migrating it to a SQL data warehouse, querying the data warehouse with SQL, and displaying the data in the Streamlit app.
