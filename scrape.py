import requests
import re
import asyncio
from tqdm import tqdm
import os

class Scrapper:
    '''pass in the anime link from yugen anime and the quality of the video'''

    def __init__(self,link:str,quality:str="360") -> None:
        
        self.m3u8_general_link=None
        self.m3u8_link=None
        self.anime_name=None
        self.link=link
        self.quality=quality
        self.current_episode=int(re.search(r'(\d+)\/$',self.link).group(1))
        self.all_content={}

    def Get_episodeplayer(self)->str:
        """this function gets the m3u8 player link and anime name
        the m3u8 player link returned is for a specific quality.
        the general m3u8 link can also be obtained via self.m3u8_general_link
        """
        with requests.Session() as s:
            resp=s.get(self.link)

            #get anime name
            if self.anime_name is None:
                _name_=re.search(r'<title>(.*)</title>',resp.text)
                self.anime_name= _name_.group(1).split("Episode")[0]
                self.anime_name=re.sub(r'[^a-zA-Z0-9|\"|\']','_',self.anime_name)
            
            #find the embed number to make the link then send a request there to find the m3u8 link
            embed_link=re.search(r'src="\/\/yugenanime.tv\/e\/(.*?)\/"',resp.text) #finds the embed link

            #now get the m3u8 link
            headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                    "authority":"yugenanime.tv",
                    "Referer":f"https://yugenanime.tv/e/{embed_link.group(1)}/",
                    "X-Requested-With":"XMLHttpRequest",
                    "Origin":"https://yugenanime.tv"
                    }
            
            resp2=s.post(f"https://yugenanime.tv/api/embed/",data={"id":embed_link.group(1),"ac":"0"},headers=headers)
            # print(resp2.text)
            # https://www042.vipanicdn.net/streamhls/231a4e0d29a1199f8c6234a79aa964fd/ep.17.1691805891.m3u8

            self.m3u8_general_link=resp2.json().get("hls")[0]
            self.m3u8_link=f"{self.m3u8_general_link[:len(self.m3u8_general_link)-5]}.{self.quality}.m3u8" #get this for a specific quality
            
            return self.m3u8_link
    
    def Get_linkslist(self)->list:#this function returns a list containing all the links which needs to be downloaded
        
        if self.m3u8_link is None:
            raise Exception("m3u8 player link is missing please call Get_episodeplayer first or run Auto_download")

        resp=requests.get(self.m3u8_link)
        if resp.status_code==404:
            raise Exception("Specified quality not available please try another quality")
        
        search=re.findall(r'(\d+)\.*ts',resp.text)

        link_list=[(f"{self.m3u8_general_link[:len(self.m3u8_general_link)-5]}.{item}.ts") for item in search ]
        return link_list

    def Increment_episode(self):
        self.link=re.sub(r'(\d+)\/$',lambda x:str(int(x.group(1))+1)+"/",self.link) #increments the link to next episode
        resp=requests.get(self.link)
        if resp.status_code==404:
            raise Exception(f"Specified number of episodes not available downloaded till episode {self.current_episode}")
        self.current_episode=self.current_episode+1

    def Decrement_episode(self):
        self.link=re.sub(r'(\d+)\/$',lambda x:str(int(x.group(1))-1)+"/",self.link) #decrements the link to prev episode
        self.current_episode=self.current_episode-1

    def Make_dir(self):
        '''this function makes a directory with the anime name'''
        try:
            os.mkdir(self.anime_name)
        except FileExistsError:
            pass

    def Check_dir(self,dir):
        '''this function checks if the file exists or not'''
        if os.path.exists(dir):
            return True
        else:
            return False


    def Make_files(self,all_links:list):
        '''this function makes files and downloads the content'''

        self.Make_dir()
        if self.Check_dir(f"{self.anime_name}/{self.anime_name}_episode {self.current_episode}.mp4"):
            choice=input("File already exists do you want to overwrite it? (y/n),auto-overwrite in 20 seconds:")
            if choice=='n' or choice=='N':
                pass
            elif choice=='y' or choice=='Y':
                os.remove(f"{self.anime_name}/{self.anime_name}_episode {self.current_episode}.mp4")
            else:
                asyncio.sleep(20)
                os.remove(f"{self.anime_name}/{self.anime_name}_episode {self.current_episode}.mp4")
        
        with requests.Session() as session:
            for link in tqdm(all_links,dynamic_ncols=True):
                s=session.get(link)
                with open(f"{self.anime_name}/{self.anime_name}_episode {self.current_episode}.mp4","ab") as f:
                    f.write(s.content)
                print(f"downloaded {self.anime_name}_episode {self.current_episode}.mp4")
        

    def Auto_download(self,number_of_episodes:int=1):
        '''this function follows the flow to download the anime'''
        
        for i in range(number_of_episodes):
            self.Get_episodeplayer()
            all_links=self.Get_linkslist()
            self.Make_files(all_links)
            self.Increment_episode()
        
if __name__=='__main__':

    link="https://yugenanime.tv/watch/18258/bleach-sennen-kessen-hen-ketsubetsu-tan/7/"

    scrapper=Scrapper(link,"360")
    scrapper.Auto_download()
