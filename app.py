from flask import Flask, request, render_template
from googleapiclient.discovery import build
from textblob import TextBlob

# Set up the Flask app
app = Flask(__name__)

# YouTube API setup
API_KEY = 'YOUR_YOUTUBE_API_KEY'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Function to retrieve top 10 YouTube videos based on query
def get_youtube_data(query):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    
    # Search for videos related to the query
    search_response = youtube.search().list(
        q=query,
        type='video',
        part='id,snippet',
        maxResults=10
    ).execute()

    video_data = []

    for search_result in search_response.get('items', []):
        video_id = search_result['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get video statistics
        video_response = youtube.videos().list(
            id=video_id,
            part='statistics'
        ).execute()

        stats = video_response['items'][0]['statistics']
        likes = int(stats.get('likeCount', 0))
        views = int(stats.get('viewCount', 1))

        # Get comments
        comment_response = youtube.commentThreads().list(
            videoId=video_id,
            part='snippet',
            maxResults=10
        ).execute()

        comments = [item['snippet']['topLevelComment']['snippet']['textDisplay'] for item in comment_response.get('items', [])]

        video_data.append({
            'url': video_url,
            'likes': likes,
            'views': views,
            'comments': comments
        })

    return video_data

# Function to calculate sentiment and rank videos
def rank_videos(video_data):
    positive_list, neutral_list, negative_list = [], [], []

    for video in video_data:
        sentiment_score = 0
        for comment in video['comments']:
            sentiment_score += TextBlob(comment).sentiment.polarity
        
        likes_per_view_ratio = video['likes'] / video['views'] if video['views'] != 0 else 0
        
        video_info = {'url': video['url'], 'likes_per_view': likes_per_view_ratio}
        
        if sentiment_score > 0:
            positive_list.append(video_info)
        elif sentiment_score == 0:
            neutral_list.append(video_info)
        else:
            negative_list.append(video_info)

    # Sort each list based on likes per view ratio
    positive_list.sort(key=lambda x: x['likes_per_view'], reverse=True)
    neutral_list.sort(key=lambda x: x['likes_per_view'], reverse=True)
    negative_list.sort(key=lambda x: x['likes_per_view'], reverse=True)

    # Combine the lists
    ranked_videos = positive_list + neutral_list + negative_list

    return ranked_videos

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    video_data = get_youtube_data(query)
    ranked_videos = rank_videos(video_data)
    
    return render_template('results.html', videos=ranked_videos)

if __name__ == '__main__':
    app.run(debug=True)
