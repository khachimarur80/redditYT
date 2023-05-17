import praw
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import moviepy
from mutagen.mp3 import MP3
import os
from moviepy.editor import *
from moviepy.video.fx.all import margin
from moviepy.video.fx.all import crop
import random
import pyttsx3
from selenium.common.exceptions import NoSuchElementException
import json
import argparse

reddit = praw.Reddit(
        client_id="",
        client_secret="",
        username="",
        password="",
        user_agent = "",
    )

def create_yt_short(bg_file, clips_dir, output_dir, chosen_subreddit='askReddit', voice_id=7):

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    engine.setProperty('voice', voices[voice_id].id)
    engine.setProperty("rate", 185)
    engine.setProperty("volume", 1.0)

    directory_path = clips_dir

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")

    def test(string):
        return ''.join([char.lower() for char in string if char.isalpha()])

    def get_post():

        while True:
            while True:
                with open('picked_submissions.json', 'r') as f:
                    picked_submissions = json.load(f)

                submission = reddit.subreddit(chosen_subreddit).random()

                if not (submission.id in picked_submissions):
                    picked_submissions.append(submission.id)

                    with open('picked_submissions.json', 'w') as f:
                        json.dump(picked_submissions, f)

                    break
                else:
                    continue

            count = 1
            comments_list = []
            for comment in submission.comments:
                comments_list.append(test(comment.body))
                count += len(comment.body)
                if 400 <= count <= 500:
                    break
            if 400 <= count <= 500:
                break


        return submission, comments_list

    def get_screenshots(submission, comments_list):
        new_comments_list = []
        driver_path = '/usr/local/bin/chromedriver'
        driver = webdriver.Chrome(options=chrome_options, executable_path=driver_path)
        driver.get(f"https://www.reddit.com/r/{chosen_subreddit}/comments/{submission.id}/")

        while True:
            try:
                post = driver.find_element(By.TAG_NAME, "h1")
                post = post.find_element(By.XPATH ,'..')
                post = post.find_element(By.XPATH ,'..')
                post.screenshot(f"./{clips_dir}/1. post.png")
                break
            except NoSuchElementException:
                continue


        comments = driver.find_elements(By.TAG_NAME, "p")
        new_comments_list = []
        count = 2

        for comment in comments[:10]:
            comment = comment.find_element(By.XPATH ,'..')
            comment = comment.find_element(By.XPATH ,'..')
            if (test(comment.text) in comments_list) and not(comment.text in new_comments_list):
                comment.screenshot(f'./{clips_dir}/'+str(count)+'. '+comment.text[:15]+".png")
                new_comments_list.append(comment.text)
                count += 1

        driver.quit()

        return new_comments_list

    post = get_post()

    new_comments_list = get_screenshots(post[0], post[1])

    def get_audios(submission):

        directory_path = clips_dir

        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) and file_path.endswith('.mp3'):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        engine.save_to_file(submission.title, f"./{clips_dir}/1. post.mp3")
        engine.startLoop(False)
        engine.iterate()
        engine.endLoop()

        count = 2

        for comment in new_comments_list:
            engine.save_to_file(comment, f'./{clips_dir}/'+str(count)+'. '+comment[:15]+'.mp3')
            engine.startLoop(False)
            engine.iterate()
            engine.endLoop()
            count += 1


    get_audios(post[0])

    def create_vid(submission):
        dir_path = f'./{clips_dir}'
        file_list = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')], reverse=False)

        clips = []
        output_video_file = submission.title+'.mp4'

        count = 0
        start = random.randint(180, (59*60 + 57 -180))

        raw_background_video_clip = VideoFileClip(bg_file)

        width, height = raw_background_video_clip.size

        cropped_width = width * (6 / 16)
        x1 = (width - cropped_width) / 2
        x2 = x1 + cropped_width

        background_video_clip = crop(raw_background_video_clip, x1=x1, y1=0, x2=x2, y2=height)

        for file in file_list:
            image_file = f'./{clips_dir}/{file[:-4]}.png'
            audio_file = f'./{clips_dir}/{file[:-4]}.mp3'

            audio_clip = AudioFileClip(audio_file)
            partial_background_video_clip = background_video_clip.subclip(start, start+audio_clip.duration)
            image_clip = ImageClip(image_file).resize(width=background_video_clip.w*.8)

            start += audio_clip.duration

            image_clip = image_clip.set_duration(audio_clip.duration)

            composite_clip = CompositeVideoClip([partial_background_video_clip, image_clip.set_pos('center')])
            composite_clip = composite_clip.set_audio(audio_clip)
            clips.append(composite_clip)

            count += 1

        composite_clip = concatenate_videoclips(clips, method='compose')
        composite_clip.write_videofile(f'./{output_dir}/'+output_video_file, fps=30, audio_codec='aac')

    create_vid(post[0])

subreddit_list = []

for subreddit in reddit.subreddits.popular(limit=1000):
    if subreddit.lang == "en" and subreddit.submission_type=='self':
        subreddit_list.append(subreddit)
    elif subreddit.lang == "es" and subreddit.submission_type=='self':
        subreddit_list.append(subreddit)

subreddit_choice = None

parser = argparse.ArgumentParser()
parser.add_argument("--subreddit", type=str, help="a string variable")
args = parser.parse_args()

if args.subreddit:
    subreddit_choice = args.subreddit

else:
    subreddit_choice = random.choice(subreddit_list).display_name

print('Creating short on random post of: r/'+subreddit_choice+'.')
create_yt_short('background.mp4', 'Clips', 'Creations', subreddit_choice)