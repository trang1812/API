# -*- coding: utf-8 -*-
"""
Created on Tue May 16 11:17:21 2023

@author: Win 10
"""
#import library
from googleapiclient.discovery import build
import pandas as pd
from IPython.display import JSON
from dateutil import parser
import isodate


#api_key
api_key = 'AIzaSyCUoJ0NtNduNHCsgArk2dC9-t1jhg2FtU4'
api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(api_service_name, api_version, developerKey=api_key)

#get information about channels
def get_channel(youtube_channel_id):
    request = youtube.channels().list(part="snippet,contentDetails,statistics", id=','.join(youtube_channel_id))
    response = request.execute()
    all_data = []
    for i in range(len(response['items'])):
        data = dict(Channel_name = response['items'][i]['snippet']['title'],
                    Channel_description=response['items'][i]['snippet']['description'],
                    Subscribers = response['items'][i]['statistics']['subscriberCount'],
                    Views = response['items'][i]['statistics']['viewCount'],
                    Total_videos = response['items'][i]['statistics']['videoCount'],
                    playlist_id = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'])
        all_data.append(data)
    return all_data


#get video_id of above channels

def get_video_ids(playlist_id):
    
    request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId =playlist_id,
                maxResults = 50)
    response = request.execute()
    
    video_ids = []
    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])
        
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId = playlist_id,
            maxResults = 50,
            pageToken = next_page_token)
        response = request.execute()
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])
        
        next_page_token = response.get('nextPageToken')
        
    return video_ids


#get information about videos
def get_video_details(video_ids):
    all_video_stats = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids[i:i+50]))
        response = request.execute()
        
        for video in response['items']:
            video_stats = dict(Title = video['snippet']['title'],
                               Channel=video['snippet']['channelTitle'],
                               Description=video['snippet']['description'],
                               Published_date = video['snippet']['publishedAt'],
                               Views = video['statistics']['viewCount'],
                               Likes = video['statistics']['likeCount'],
                               Comments = video['statistics']['commentCount'],
                               Durations = video['contentDetails']['duration']
                               )
            all_video_stats.append(video_stats)
    
    return all_video_stats

# get comments
def get_comments_in_videos(video_ids):
    all_comments = []
    
    for video_id in video_ids:
        try:   
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id)
            response = request.execute()
            
            for comment in response['items'][0:50]:
                comments_info=dict(video_id=comment['snippet']['videoId'],
                              comments= comment['snippet']['topLevelComment']['snippet']['textOriginal'])
                all_comments.append(comments_info)
            
        except: 
            # When error occurs - most likely because comments are disabled on a video
            print('Could not get comments for video ' + video_id)
    return all_comments

        
#Explore youtube channel named "StatQuest with Josh Starmer"

channel_name=["UCtYLUTtgS3k1Fg4y5tAhLbw", "UCCezIgC97PvUuR4_gbFUs5g"]
channel_info = get_channel(channel_name)
channel_info_df=pd.DataFrame(channel_info)
video_ids = []
for i in range(len(channel_info)):
    video_id= get_video_ids(channel_info[i]['playlist_id'])
    video_ids.extend(video_id)

channel_video=pd.DataFrame(get_video_details(video_ids))

###data processing###
cols = ['Views', 'Likes', 'Comments']
channel_video[cols] = channel_video[cols].apply(pd.to_numeric, errors='coerce', axis=1)

# Create publish day (in the week) column
channel_video['Published_date'] =  channel_video['Published_date'].apply(lambda x: parser.parse(x)) 
channel_video['pushblishDayName'] = channel_video['Published_date'].apply(lambda x: x.strftime("%A")) 

# convert duration to seconds
channel_video['DurationSecs'] = channel_video['Durations'].apply(lambda x: isodate.parse_duration(x)).astype('timedelta64[s]')

channel_video.to_csv('channel_video.csv') 
channel_info_df.to_csv('channel_info.csv')

