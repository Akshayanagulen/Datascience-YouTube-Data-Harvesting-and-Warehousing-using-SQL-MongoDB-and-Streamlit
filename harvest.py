import collections
import pymongo
import sys
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector

#API key connection
def Api_connect():
    Api_Id="AIzaSyASN9ZhsoGzeRIvXFCJgrz0nsFeIsvMknQ"

    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name,api_version,developerKey=Api_Id)
    return youtube

youtube=Api_connect()

#get channel information
def get_channel_info(channel_id):
    
    request = youtube.channels().list(
                part = "snippet,contentDetails,Statistics",
                id = channel_id)
            
    response1=request.execute()

    for i in range(0,len(response1["items"])):
        data = dict(
                    Channel_Name = response1["items"][i]["snippet"]["title"],
                    Channel_Id = response1["items"][i]["id"],
                    Subscription_Count= response1["items"][i]["statistics"]["subscriberCount"],
                    Views = response1["items"][i]["statistics"]["viewCount"],
                    Total_Videos = response1["items"][i]["statistics"]["videoCount"],
                    Channel_Description = response1["items"][i]["snippet"]["description"],
                    Playlist_Id = response1["items"][i]["contentDetails"]["relatedPlaylists"]["uploads"],
                    )
        return data
    
#get playlist ids
def get_playlist_info(channel_id):
    All_data = []
    next_page_token = None
    next_page = True
    while next_page:

        request = youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token
            )
        response = request.execute()

        for item in response['items']: 
            data={'PlaylistId':item['id'],
                    'Title':item['snippet']['title'],
                    'ChannelId':item['snippet']['channelId'],
                    'ChannelName':item['snippet']['channelTitle'],
                    'PublishedAt':item['snippet']['publishedAt'],
                    'VideoCount':item['contentDetails']['itemCount']}
            All_data.append(data)
        next_page_token = response.get('nextPageToken')
        if next_page_token is None:
            next_page=False
    return All_data

#get video ids
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list( 
                                           part = 'snippet',
                                           playlistId = playlist_id, 
                                           maxResults = 50,
                                           pageToken = next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids

#get video information
def get_video_info(video_ids):

    video_data = []

    for video_id in video_ids:
        request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id= video_id)
        response = request.execute()

        for item in response["items"]:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Channel_Id = item['snippet']['channelId'],
                        Video_Id = item['id'],
                        Title = item['snippet']['title'],
                        Tags = item['snippet'].get('tags'),
                        Thumbnail = item['snippet']['thumbnails']['default']['url'],
                        Description = item['snippet']['description'],
                        Published_Date = item['snippet']['publishedAt'],
                        Duration = item['contentDetails']['duration'],
                        Views = item['statistics']['viewCount'],
                        Likes = item['statistics'].get('likeCount'),
                        Comments = item['statistics'].get('commentCount'),
                        Favorite_Count = item['statistics']['favoriteCount'],
                        Definition = item['contentDetails']['definition'],
                        Caption_Status = item['contentDetails']['caption']
                        )
            video_data.append(data)
    return video_data


#get comment information
def get_comment_info(video_ids):
        Comment_Information = []
        try:
                for video_id in video_ids:

                        request = youtube.commentThreads().list(
                                part = "snippet",
                                videoId = video_id,
                                maxResults = 50
                                )
                        response5 = request.execute()
                        
                        for item in response5["items"]:
                                comment_information = dict(
                                        Channel_Id = item["snippet"]["channelId"],
                                        Comment_Id = item["snippet"]["topLevelComment"]["id"],
                                        Video_Id = item["snippet"]["videoId"],
                                        Comment_Text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"],
                                        Comment_Author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                        Comment_Published = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"])

                                Comment_Information.append(comment_information)
        except:
                pass
                
        return Comment_Information
        
#MongoDB Connection
client = pymongo.MongoClient("mongodb+srv://akshayanagulen:akshayan@cluster0.hznm4m2.mongodb.net/?retryWrites=true&w=majority")
db = client["Youtube_Project"]
mongo_collection = db['channel_information']

# upload to MongoDB

def channel_details(channel_id):
    ch_details = get_channel_info(channel_id)
    pl_details = get_playlist_info(channel_id)
    vi_ids = get_channel_videos(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)

    coll1 = db["channel data"]
    coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,"video_information":vi_details,
                     "comment_information":com_details})
    
    return "upload completed successfully"

def channels_table(selected_channel_id):
    mydb = mysql.connector.connect(host="localhost",
            user="root",
            password="akshayan",
            database= "Youtube_Project",
            port = "3306"
            )
    cursor = mydb.cursor()

    drop_query = "drop table if exists channels"
    cursor.execute(drop_query)
    mydb.commit()
    try:
        create_query = '''create table if not exists channels(Channel_Name varchar(100),
                        Channel_Id varchar(80) primary key, 
                        Subscription_Count bigint, 
                        Views bigint,
                        Total_Videos int,
                        Channel_Description text,
                        Playlist_Id varchar(50))'''
        cursor.execute(create_query)
        mydb.commit()
    except:
        st.write("Channels Table alredy created")      
    ch_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"]   
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
         if ch_data["channel_information"]["Channel_Id"] == selected_channel_id:
            ch_list.append(ch_data["channel_information"])
    df = pd.DataFrame(ch_list)
    for index,row in df.iterrows():
        insert_query = '''INSERT into channels(Channel_Name,
                                                    Channel_Id,
                                                    Subscription_Count,
                                                    Views,
                                                    Total_Videos,
                                                    Channel_Description,
                                                    Playlist_Id)
                                        VALUES(%s,%s,%s,%s,%s,%s,%s)'''
            

        values =(
                row['Channel_Name'],
                row['Channel_Id'],
                row['Subscription_Count'],
                row['Views'],
                row['Total_Videos'],
                row['Channel_Description'],
                row['Playlist_Id'])
        try:                     
            cursor.execute(insert_query,values)
            mydb.commit()    
        except:
            st.write("Channels values are already inserted")
        

def playlists_table(selected_channel_id):
    mydb = mysql.connector.connect(host="localhost",
            user="root",
            password="akshayan",
            database= "Youtube_Project",
            port = "3306"
            )
    cursor = mydb.cursor()

    drop_query = "drop table if exists playlists"
    cursor.execute(drop_query)
    mydb.commit()

    try:
        create_query = '''create table if not exists playlists(PlaylistId varchar(100) primary key,
                        Title varchar(80), 
                        ChannelId varchar(100), 
                        ChannelName varchar(100),
                        PublishedAt varchar(30),
                        VideoCount int
                        )'''
        cursor.execute(create_query)
        mydb.commit()
    except:
        st.write("Playlists Table alredy created")    


    db = client["Youtube_Project"]
    coll1 =db["channel data"]
    pl_list = []
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for playlist_info in pl_data["playlist_information"]:
            if "ChannelId" in playlist_info and playlist_info["ChannelId"] == selected_channel_id:
                for i in range(len(pl_data["playlist_information"])):
                    pl_list.append(pl_data["playlist_information"][i])
    df = pd.DataFrame(pl_list)

    for index,row in df.iterrows():
        insert_query = '''INSERT into playlists(PlaylistId,
                                                    Title,
                                                    ChannelId,
                                                    ChannelName,
                                                    PublishedAt,
                                                    VideoCount)
                                        VALUES(%s,%s,%s,%s,%s,%s)'''            
        values =(
                row['PlaylistId'],
                row['Title'],
                row['ChannelId'],
                row['ChannelName'],
                row['PublishedAt'],
                row['VideoCount'])
                
        try:                     
            cursor.execute(insert_query,values)
            mydb.commit()    
        except:
            st.write("Playlists values are already inserted")

def videos_table(selected_channel_id):

    mydb = mysql.connector.connect(host="localhost",
            user="root",
            password="akshayan",
            database= "Youtube_Project",
            port = "3306"
            )
    cursor = mydb.cursor()

    drop_query = "drop table if exists videos"
    cursor.execute(drop_query)
    mydb.commit()

    try:
        create_query = '''create table if not exists videos(
                        Channel_Name varchar(150),
                        Channel_Id varchar(100),
                        Video_Id varchar(50) primary key, 
                        Title varchar(150), 
                        Tags text,
                        Thumbnail varchar(225),
                        Description text, 
                        Published_Date varchar(30),
                        Duration varchar(15), 
                        Views bigint, 
                        Likes bigint,
                        Comments int,
                        Favorite_Count int, 
                        Definition varchar(10), 
                        Caption_Status varchar(50) 
                        )''' 
                        
        cursor.execute(create_query)             
        mydb.commit()
    except:
        st.write("Processing")

    vi_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for video_info in vi_data["video_information"]:
            if "Channel_Id" in video_info and video_info["Channel_Id"] == selected_channel_id:
                for i in range(len(vi_data["video_information"])):
                    vi_list.append(vi_data["video_information"][i])
    df2 = pd.DataFrame(vi_list)
        
    
    for index, row in df2.iterrows():
        insert_query = '''
                    INSERT INTO videos (Channel_Name,
                        Channel_Id,
                        Video_Id, 
                        Title, 
                        Tags,
                        Thumbnail,
                        Description, 
                        Published_Date,
                        Duration, 
                        Views, 
                        Likes,
                        Comments,
                        Favorite_Count, 
                        Definition, 
                        Caption_Status 
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

                '''
        tags_str = ', '.join(row['Tags']) if row['Tags'] else None
        values = (
                    row['Channel_Name'],
                    row['Channel_Id'],
                    row['Video_Id'],
                    row['Title'],
                    tags_str,
                    row['Thumbnail'],
                    row['Description'],
                    row['Published_Date'],
                    row['Duration'],
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favorite_Count'],
                    row['Definition'],
                    row['Caption_Status'])
                                
        try:    
            cursor.execute(insert_query,values)
            mydb.commit()
        except:
            st.write("videos values already inserted in the table")

def comments_table(selected_channel_id):
    mydb = mysql.connector.connect(host="localhost",
                user="root",
                password="akshayan",
                database= "Youtube_Project",
                port = "3306"
                )

    # Ensure the connection is open
    if not mydb.is_connected():
        mydb.reconnect()

    # Use a context manager for the cursor
    with mydb.cursor() as cursor:
        # Drop table if exists
        drop_query = "DROP TABLE IF EXISTS comments"
        cursor.execute(drop_query)
        mydb.commit()

        create_query = '''CREATE TABLE if not exists comments(Comment_Id varchar(100) primary key,
                        Channel_Id varchar(115),
                        Video_Id varchar(80),
                        Comment_Text text, 
                        Comment_Author varchar(150),
                        Comment_Published varchar(30))'''
        cursor.execute(create_query)
        mydb.commit()

        
    com_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for com_info in com_data["comment_information"]:
            if "Channel_Id" in com_info and com_info["Channel_Id"] == selected_channel_id:
                for i in range(len(com_data["comment_information"])):
                    com_list.append(com_data["comment_information"][i])
    df3 = pd.DataFrame(com_list)

    for index, row in df3.iterrows():
        insert_query = '''
            INSERT INTO comments (Comment_Id,
                                Channel_Id,
                                Video_Id ,
                                Comment_Text,
                                Comment_Author,
                                Comment_Published)
            VALUES (%s, %s, %s, %s, %s, %s)

        '''
        values = (
            row['Comment_Id'],
            row["Channel_Id"],
            row['Video_Id'],
            row['Comment_Text'],
            row['Comment_Author'],
            row['Comment_Published']
        )
        # Ensure the connection is open
        if not mydb.is_connected():
            mydb.reconnect()

        # Use a context manager for the cursor
        with mydb.cursor() as cursor:
            cursor.execute(insert_query,values)
            mydb.commit()
            

def tables(selected_channel_id):
    channels_table(selected_channel_id)
    playlists_table(selected_channel_id)
    videos_table(selected_channel_id)
    comments_table(selected_channel_id)
    return "Tables Created successfully"

def show_channels_table():
    ch_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"] 
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        if ch_data["channel_information"]["Channel_Id"] == selected_channel_id:
            ch_list.append(ch_data["channel_information"])
    channels_table = st.dataframe(ch_list)
    return channels_table

def show_playlists_table():
    db = client["Youtube_Project"]
    coll1 =db["channel data"]
    pl_list = []
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for playlist_info in pl_data["playlist_information"]:
            if "ChannelId" in playlist_info and playlist_info["ChannelId"] == selected_channel_id:
                for i in range(len(pl_data["playlist_information"])):
                    pl_list.append(pl_data["playlist_information"][i])
    playlists_table = st.dataframe(pl_list)
    return playlists_table

def show_videos_table():
    vi_list = []
    db = client["Youtube_Project"]
    coll2 = db["channel data"]
    for vi_data in coll2.find({},{"_id":0,"video_information":1}):
        for video_info in vi_data["video_information"]:
            if "Channel_Id" in video_info and video_info["Channel_Id"] == selected_channel_id:
                for i in range(len(vi_data["video_information"])):
                    vi_list.append(vi_data["video_information"][i])
    videos_table = st.dataframe(vi_list)
    return videos_table

def show_comments_table():
    com_list = []
    db = client["Youtube_Project"]
    coll3 = db["channel data"]
    for com_data in coll3.find({},{"_id":0,"comment_information":1}):
        for com_info in com_data["comment_information"]:
            if "Channel_Id" in com_info and com_info["Channel_Id"] == selected_channel_id:
                for i in range(len(com_data["comment_information"])):
                    com_list.append(com_data["comment_information"][i])
    comments_table = st.dataframe(com_list)
    return comments_table

#streamlit part web application display
st.set_page_config(layout='wide')
st.header("Youtube Data Harvesting and Warehousing")


with st.sidebar:
    selected = option_menu(menu_title = "Home",
        options = ["Youtube Channel", "Channel Detail", "Migrate to Mysql", "Data Analysis" ])

if selected == "Youtube Channel":
    channel_id = st.text_input("Enter the Channel id")
    channels = channel_id.split(',')
    channels = [ch.strip() for ch in channels if ch]

    if st.button("Collect and Store data"):
        for channel in channels:
            ch_ids = []
            db = client["Youtube_Project"]
            coll1 = db["channel data"]
            for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
                ch_ids.append(ch_data["channel_information"]["Channel_Id"])
            if channel in ch_ids:
                st.success("Channel details of the given channel id: " + channel + " already exists")
            else:
                insert = channel_details(channel)
                st.success(insert)

if selected == "Channel Detail":
    ch_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = pd.DataFrame(ch_list)
    st.subheader("The channels available in Mongo DB")
    st.write(df)

elif selected == "Migrate to Mysql":
    ch_list = []
    db = client["Youtube_Project"]
    coll1 = db["channel data"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = pd.DataFrame(ch_list)
    selected_channel = st.selectbox("Select a channel", df['Channel_Name'])
    st.write("Select the  channel:", selected_channel)
    selected_channel_id = df[df['Channel_Name'] == selected_channel]['Channel_Id'].iloc[0]
    st.write("Selected channel ID:", selected_channel_id)
    # Retrieve data from selected collection
    if st.button("Migrate to SQL"):        
        st.write("Migrating the Channel :", selected_channel_id)
        display = tables(selected_channel_id)
        st.success(display)         

    #we are creating a radio button to view the tables and data
    show_table = st.selectbox("SELECT THE TABLE FOR VIEW",("Channels info","Playlists info","Videos info","Comments info"))

    if show_table == "Channels info":
        show_channels_table()

    elif show_table == "Playlists info":
        show_playlists_table()

    elif show_table =="Videos info":
        show_videos_table()

    elif show_table == "Comments info":
        show_comments_table()


elif selected == "Data Analysis":
    #SQL connection
    mydb = mysql.connector.connect(host="localhost",
                    user="root",
                    password="akshayan",
                    database= "Youtube_Project",
                    port = "3306"
                    )
    # Ensure the connection is open
    if not mydb.is_connected():
        mydb.reconnect()

    # Create a cursor
    cursor = mydb.cursor()

    question = st.selectbox(
        'Please Select Your Question',
        ('1. All the videos and the Channel Name',
        '2. Channels with most number of videos',
        '3. 10 most viewed videos',
        '4. Comments in each video',
        '5. Videos with highest likes',
        '6. likes of all videos',
        '7. views of each channel',
        '8. videos published in the year 2022',
        '9. average duration of all videos in each channel',
        '10. videos with highest number of comments'))

    if question == '1. All the videos and the Channel Name':
        query1 = "select Title as videos, Channel_Name as ChannelName from videos;"
        cursor.execute(query1)
        result1 = cursor.fetchall()
        t1 = pd.DataFrame(result1, columns=["Video Title", "Channel Name"])
        st.write(t1)
        mydb.commit()

    elif question == '2. Channels with most number of videos':
        query2 = "select Channel_Name as ChannelName,Total_Videos as NO_Videos from channels order by Total_Videos desc;"
        cursor.execute(query2)
        result2 = cursor.fetchall()
        t2 = pd.DataFrame(result2, columns=["Channel Name","No Of Videos"])
        st.write(t2)
        mydb.commit()
        
    elif question == '3. 10 most viewed videos':
        query3 = '''select Views as views , Channel_Name as ChannelName,Title as VideoTitle from videos 
                            where Views is not null order by Views desc limit 10;'''
        cursor.execute(query3)
        result3 = cursor.fetchall()
        t3 = pd.DataFrame(result3, columns = ["views","channel Name","video title"])
        st.write(t3)
        mydb.commit()
    
    elif question == '4. Comments in each video':
        query4 = "select Comments as No_comments ,Title as VideoTitle from videos where Comments is not null;"
        cursor.execute(query4)
        result4 = cursor.fetchall()
        t4 = pd.DataFrame(result4, columns=["No Of Comments", "Video Title"])
        mydb.commit()
        
    elif question == '5. Videos with highest likes':
        query5 = '''select Title as VideoTitle, Channel_Name as ChannelName, Likes as LikesCount from videos 
                        where Likes is not null order by Likes desc;'''
        cursor.execute(query5)
        result5 =  cursor.fetchall()
        t5 = pd.DataFrame(result5, columns=["video Title","channel Name","like count"])
        mydb.commit()
        
    elif question == '6. likes of all videos':
        query6 = '''select Likes as likeCount,Title as VideoTitle from videos;'''
        cursor.execute(query6)
        result6 = cursor.fetchall()
        t6 = pd.DataFrame(result6, columns=["like count","video title"])
        st.write(t6)
        mydb.commit()
        
    elif question == '7. views of each channel':
        query7 = "select Channel_Name as ChannelName, Views as Channelviews from channels;"
        cursor.execute(query7)
        result7 = cursor.fetchall()
        t7 = pd.DataFrame(result7, columns=["channel name","total views"])
        st.write(t7)
        mydb.commit()

    elif question == '8. videos published in the year 2022':
        query8 = '''select Title as Video_Title, Published_Date as VideoRelease, Channel_Name as ChannelName from videos 
                    where extract(year from Published_Date) = 2022;'''
        cursor.execute(query8)
        result8 = cursor.fetchall()
        t8 = pd.DataFrame(result8,columns=["Name", "Video Publised On", "ChannelName"])
        st.write(t8)
        mydb.commit()
    

    elif question == '9. average duration of all videos in each channel':
        query9 = """ select Channel_Name as Channel, AVG(TIME_TO_SEC(STR_TO_DATE(duration, 'PT%iM%sS'))) AS AverageDurationInSeconds
        FROM videos GROUP BY Channel_Name;
        """
        cursor.execute(query9)
        result9 = cursor.fetchall()
        t9 = pd.DataFrame(result9, columns=['Channel', 'Average_Duration_Seconds'])
        st.write(t9)
        mydb.commit()


    elif question == '10. videos with highest number of comments':
        query10 = '''select Title as VideoTitle, Channel_Name as ChannelName, Comments as Comments from videos 
                        where Comments is not null order by Comments desc;'''
        cursor.execute(query10)
        result10 = cursor.fetchall()
        t10 = pd.DataFrame(result10, columns=['Video Title', 'Channel Name', 'NO Of Comments'])
        st.write(t10)
        mydb.commit()
        

