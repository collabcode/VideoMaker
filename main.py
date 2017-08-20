from moviepy.editor import *
import feedparser
from bs4 import BeautifulSoup
from gtts import gTTS
from selenium import webdriver
from PIL import Image
import io, math
import numpy as np
import re
import requests
from datetime import datetime
import os

print(str(datetime.now()),"Begin program")
os.system('del /F /Q .\\temp\\*')
os.system('python Music_Generator_Demo-master/rbm_chords.py')
print(str(datetime.now()),"Audio refreshed")

videoSize = (1280, 720)
textSize = (1180,150)

driver = webdriver.PhantomJS()
driver.set_window_size(videoSize[0], videoSize[1])

i = 0
seperator = "\n" + "____________________________________________________" + "\n"+ "\n"
text_list = []
image_list = []
url = 'https://www.reddit.com/r/aww/.rss'
d = feedparser.parse(url)
for post in d.entries:
    try:

        description = post.description
        soup = BeautifulSoup(description)
        link = soup.find('a', href=True, text='[link]')
        for l in soup.findAll('a', href=True):
            if l.text == '[link]':
                link = l["href"]
        if " submitted by " in description:
            description = post.description.split(' submitted by ')[0]
        soup = BeautifulSoup(description)
        description = soup.get_text().strip()
        description=re.sub(r'^https?:\/\/.*[\r\n]*', '', description, flags=re.MULTILINE)
        if len(description)< 500 and not (link.endswith(".gif") or link.endswith(".gifv")):
            data = None
            img=None
            if link.endswith("jpg") or link.endswith("png"):
                response = requests.get(link)
                data = response.content
                img = Image.open(io.BytesIO(data))
                baseheight = videoSize[1]
                hpercent = (baseheight / float(img.size[1]))
                wsize = int((float(img.size[0]) * float(hpercent)))
                if hpercent < 1:
                    img = img.resize((wsize, baseheight), Image.ANTIALIAS)
            else:
                driver.get(link)
                data = driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(data))
                img = img.crop((0, 0, videoSize[0], videoSize[1]))

            numpy_array = np.asarray(img)

            text_list.append((post.title , description, link,numpy_array))
        else:
            continue
        i +=1
        if i==10:
            break
    except:
        print("Error")

print(str(datetime.now()),"Feed fetching done")

clip_list = []
#transitionClip = TextClip(' ',size=videoSize,fontsize=20,color='Black',bg_color='Black').set_duration(2)
i=0
for entry in text_list:
    try:
        ttsText = entry[0]+ ". " + entry[1]
        ttsText = re.sub("[\(\[].*?[\)\]]", "", ttsText)
        ttsText = re.sub('[^A-Za-z0-9. ]+', ' ',ttsText)[:100]

        print(entry[0], ttsText, entry[2])
        tts = gTTS(text=ttsText, lang='en', slow=False)

        tts.save("temp/temp.mp3")
        af = AudioFileClip("temp/temp.mp3")
        bg = AudioFileClip('temp/generated_chord_' + str(i%10) + '.mid')
        af = concatenate_audioclips([af, bg])

        duration_t = af.duration
        duration_i = af.duration
        if af.duration<10:
            duration_t=10
            duration_i = 10

        entry_clip_list = []
        '''
        if len(entry[1])>5:
            tc = TextClip(entry[0] + seperator + entry[1],  font='Amiri-regular',bg_color='transparent',size=textSize,fontsize = 20, color = 'white',method='caption').set_duration(duration_t)
        else:
            tc= TextClip(entry[0],  font='Amiri-regular',bg_color='transparent',size=textSize,fontsize = 40, color = 'white',method='caption').set_duration(duration_t)
        '''
        tc = TextClip(entry[0], font='Amiri-regular', bg_color='transparent', size=textSize, fontsize=int(100/math.pow(len(entry[0]),1/3)), color='white',
                      method='caption').set_duration(duration_t)
        ic = ImageClip(entry[3], duration=duration_i,transparent=True).set_position(("center","top"))#.resize(videoSize)
        i+=1
        txt_col = tc.on_color(size=(ic.w + tc.w, tc.h),color=(0, 0, 0), pos=(6, 'center'), col_opacity=0.6)
        w, h = videoSize
        txt_mov = txt_col.set_pos(lambda t: (max(w / 30, int(w - 0.5 * w * t)),
                                             max(5 * h / 6, int(100 * t))))
        clip =  CompositeVideoClip([ic,txt_mov],size=videoSize).set_audio(af)
        '''
        entry_clip_list.append(tc)
        entry_clip_list.append(ic)
        if duration_t > 3:
            entry_clip_list.append(tc)
        #entry_clip_list.append(transitionClip)
        clip = concatenate(entry_clip_list, method = "compose").set_audio(af)
        '''
        clip_list.append(clip)

    except UnicodeEncodeError:
        txt_clip = TextClip("Issue with text", bg_color='transparent',size=videoSize,fontsize = 20, color = 'white',method='caption').set_duration(2)
        clip_list.append(txt_clip)
        #clip_list.append(transitionClip)
print(str(datetime.now()),"Clip creation done")
if clip_list.__len__()>0:
    fade_duration = 2
    clip_list = [clip.crossfadein(fade_duration) for clip in clip_list]
    final_clip = concatenate(clip_list, method = "compose", padding = fade_duration*1.5)
    filename = (url.split("//")[1].replace("www.","").replace(".","_").replace("/","_"))+ "_"+(str(datetime.now()).split(".")[0]).replace("-","_").replace(":","_") + ".mp4"
    final_clip.write_videofile(filename,fps=12, bitrate="5000k",codec = 'libx264',threads=100,preset='ultrafast')
    print(str(datetime.now()),"concatenation done")
else:
    print(str(datetime.now()), 'No data')

os.system('del /F /Q .\\temp\\*')
print(str(datetime.now()),"Cleanup done")