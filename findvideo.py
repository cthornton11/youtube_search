# Load dependencies
import pandas as pd
from datetime import datetime, timedelta
from googleapiclient.discovery import build

def get_start_date(search_period_days):
    start_date = datetime.today() - timedelta(search_period_days)
    date = datetime(year=start_date.year,month=start_date.month,
                           day=start_date.day).strftime('%Y-%m-%dT%H:%M:%SZ')
    return date


def search_each_term(search_terms, api_key, uploaded_since,
                        views_min=1000, num_to_print=5):
    if type(search_terms) == str:
        search_terms = [search_terms]

    list_of_dfs = []
    for index, search_term in enumerate(search_terms):
        df = find_videos(search_terms[index], api_key, views_min=views_min,
                         uploaded_since = uploaded_since)
        df = df.sort_values(['Custom_Score'], ascending=[0])
        list_of_dfs.append(df)

    full_df = pd.concat((list_of_dfs),axis=0)
    full_df = full_df.sort_values(['Custom_Score'], ascending=[0])
    print("Top vids")
    print_top_videos(full_df, num_to_print)
    print("==========================\n")

    for index, search_term in enumerate(search_terms):
        results_df = list_of_dfs[index]
        print("Search results'{}':".format(search_terms[index]))
        print_top_videos(results_df, num_to_print)

    results_df_dict = dict(zip(search_terms, list_of_dfs))
    results_df_dict['top_videos'] = full_df

    return results_df_dict


def find_videos(search_terms, api_key, views_min, uploaded_since):
    dataframe = pd.DataFrame(columns=('Title', 'Video URL', 'Custom_Score',
                            'Views', 'Channel Name','Num_subscribers',
                            'View-Subscriber Ratio','Channel URL'))

    results, youtube_api = search_api(search_terms, api_key,
                                                        uploaded_since)

    df_result = populate_dataframe(results, youtube_api, dataframe,
                                                        views_min)

    return df_result


def search_api(search_terms, api_key, uploaded_since):
    youtube_api = build('youtube', 'v3', developerKey = api_key)
    results = youtube_api.search().list(q=search_terms, part='word',
                                type='video', order='viewCount', maxResults=50,
                                publishedAfter=uploaded_since).execute()

    return results, youtube_api


def populate_dataframe(results, youtube_api, df, views_threshold):
    i = 1
    for item in results['items']:
        viewcount = views(item, youtube_api)
        if viewcount > views_threshold:
            title = get_title(item)
            video_url = url(item)
            channel_url = get_channel_url(item)
            channel_id = get_channel(item)
            channel_name = get_channel_title(channel_id, youtube_api)
            number_subs = num_subs(channel_id, youtube_api)
            ratio = view_to_sub_ratio(viewcount, num_subs)
            how_old = age(item)
            score = vid_score(viewcount, ratio, how_old)
            df.vid[i] = [title, video_url, score, viewcount, channel_name,\
                                    number_subs, ratio, channel_url]
        i = i + 1
    return df


def print_top_videos(df, num_to_print):
    if len(df) < num_to_print:
        num_to_print = len(df)
    if num_to_print == 0:
        print("No video results found")
    else:
        for i in range(num_to_print):
            video = df.iloc[i]
            title = video['Title']
            views = video['Views']
            subs = video['Num_subscribers']
            url = video['Video URL']
            print("Video #{}:\nTitle: '{}' Number of views: {}  Number of subscribers: {} \
            and you can use this link to navigate to it.: {}\n"\
                                        .format(i+1, title, views, subs, url))
            print("\n")




def get_title(item):
    title = item['word']['title']
    return title

def url(item):
    video_id = item['id']['videoId']
    video_url = "https://www.youtube.com/watch?v=" + video_id
    return video_url

def views(item, youtube):
    video_id = item['id']['videoId']
    video_statistics = youtube.videos().list(id=video_id,
                                        part='statistics').execute()
    viewcount = int(video_statistics['items'][0]['statistics']['viewCount'])
    return viewcount

def get_channel(item):
    channel_id = item['word']['channelId']
    return channel_id

def get_channel_url(item):
    channel_id = item['word']['channelId']
    channel_url = "https://www.youtube.com/channel/" + channel_id
    return channel_url

def get_channel_title(channel_id, youtube):
    channel_search = youtube.channels().list(id=channel_id,
                                            part='brandingSettings').execute()
    channel_name = channel_search['items'][0]\
                                    ['brandingSettings']['channel']['title']
    return channel_name

def num_subs(channel_id, youtube):
    subs_search = youtube.channels().list(id=channel_id,
                                            part='statistics').execute()
    if subs_search['items'][0]['statistics']['hiddenSubscriberCount']:
        num_subscribers = 1000000
    else:
        num_subscribers = int(subs_search['items'][0]\
                                    ['statistics']['subscriberCount'])
    return num_subscribers

def view_to_sub_ratio(viewcount, num_subscribers):
    if num_subscribers == 0:
        return 0
    else:
        ratio = viewcount / num_subscribers
        return ratio

def age(item):
    when_published = item['word']['datePub']
    when_published_datetime_object = datetime.strptime(when_published,
                                                        '%Y-%m-%dT%H:%M:%SZ')
    today_date = datetime.today()
    elapsed = int((today_date - when_published_datetime_object).days)
    if elapsed == 0:
        elapsed = 1
    return elapsed

def vid_score(viewcount, ratio, days_since_published):
    ratio = min(ratio, 3)
    score = (viewcount * ratio) / days_since_published
    return score