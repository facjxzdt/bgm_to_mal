import re
import json
import requests
import time

bangumi_token = ''
bangumi_user = ''

l1 = {}
l2 = []
l3 = []
l4 = []
class Bangumi:
    def __init__(self):
        self.api_url = 'https://api.bgm.tv'
        self.token = bangumi_token
        self.user = bangumi_user
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'Authorization': 'Bearer {}'.format(self.token)
        }

    def get_collection(self):
        animes = []
        limit = 100
        offset = 0
        while True:
            params = {'limit': limit, 'offset': offset}

            page = requests.get(self.api_url + '/v0/users/{}/collections'.format(self.user), headers=self.headers,
                                params=params)

            if page.status_code != 200:
                continue
            json = page.json()
            animes.extend(json['data'])
            if len(json['data']) < limit:
                break
            offset += limit

        return animes

    def get_other_name(self, bgm_id):
        names = []
        url = self.api_url+'/v0/subjects/{}'.format(str(bgm_id))
        page = requests.get(url,headers=self.headers)
        _json = page.json()
        for i in _json['infobox']:
            if i['key']=='中文名':
                names.append(i['value'])
            elif i['key'] == '别名':
                for j in i['value']:
                    names.append(j['v'])
        return names

    # 关于bgm：type=1想看 2看完 3正在看
    def sort_animes(self):
        anime_list = self.get_collection()
        wanted = []
        watching = []
        have_watched = []
        animes = {}
        for anime in anime_list:
            _l = {}
            if anime['type'] == 1:
                _l = {anime['subject']['id']:self.get_other_name(anime['subject']['id'])}
                wanted.append(_l)
            elif anime['type'] == 2:
                _l = {anime['subject']['id']:self.get_other_name(anime['subject']['id'])}
                have_watched.append(_l)
            elif anime['type'] == 3:
                _l = {anime['subject']['id']:self.get_other_name(anime['subject']['id'])}
                watching.append(_l)
        animes = {'watching': watching, 'have_watched': have_watched, 'wanted': wanted}
        print(animes)
        return animes


class DDplay:
    def __init__(self):
        self.api_url = 'https://api.dandanplay.net'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        }

    def get_ids(self, ddid):
        id = ddid
        url = self.api_url + '/api/v2/bangumi/{}'.format(id)
        page = requests.get(url, headers=self.headers)
        _json = page.json()
        return _json['bangumi']['onlineDatabases']

    def search_anime(self, ani: dict):
        ani = ani
        watching = ani['watching']
        have_watched = ani['have_watched']
        wanted = ani['wanted']
        url = self.api_url + '/api/v2/search/anime'
        mal_watching = []
        mal_watched = []
        mal_wanted = []

        for i in watching:
            i = dict(i)
            for k in i.values():
                params = {'keyword': k}
                page = requests.get(url, params=params, headers=self.headers)
                _json = page.json()
                try:
                    if len(_json['animes']) != 0:
                        break
                except:
                    break
            try:
                for anime in _json['animes']:
                    id = anime['animeId']
                    ids = self.get_ids(id)
                    match = re.search(r'/subject/(\d+)', ids[0]['url'])
                    if match:
                        subject_id = match.group(1)
                    else:
                        continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        match_mal = re.search(r'/anime/(\d+)', ids[1]['url'])
                        if match_mal:
                            mal_id = match_mal.group(1)
                            print(mal_id)
                        else:
                            continue
                        mal_watching.append(mal_id)
            except:
                pass
            global l2
            l2 = mal_watching
            print(mal_watching)

        for i in have_watched:
            i = dict(i)
            for k in i.values():
                params = {'keyword': k}
                page = requests.get(url, params=params, headers=self.headers)
                _json = page.json()
                try:
                    if len(_json['animes']) != 0:
                        break
                except:
                    break
            try:
                for anime in _json['animes']:
                    id = anime['animeId']
                    ids = self.get_ids(id)
                    # print(ids)
                    match = re.search(r'/subject/(\d+)', ids[0]['url'])
                    if match:
                        subject_id = match.group(1)
                    else:
                        continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        match_mal = re.search(r'/anime/(\d+)', ids[1]['url'])
                        if match_mal:
                            mal_id = match_mal.group(1)
                            print(mal_id)
                        else:
                            continue
                        mal_watched.append(mal_id)
            except:
                pass
            global l3
            l3 = mal_watched
            print(mal_watched)

        for i in wanted:
            i = dict(i)
            for k in i.values():
                params = {'keyword': k}
                page = requests.get(url, params=params, headers=self.headers)
                _json = page.json()
                try:
                    if len(_json['animes']) != 0:
                        break
                except:
                    break
            try:
                for anime in _json['animes']:
                    id = anime['animeId']
                    ids = self.get_ids(id)
                    # print(ids)
                    match = re.search(r'/subject/(\d+)', ids[0]['url'])
                    if match:
                        subject_id = match.group(1)
                    else:
                        continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        match_mal = re.search(r'/anime/(\d+)', ids[1]['url'])
                        if match_mal:
                            mal_id = match_mal.group(1)
                            print(mal_id)
                        else:
                            continue
                        mal_wanted.append(mal_id)
            except:
                pass
            global l4
            l4 = mal_wanted
            print(mal_wanted)


#print(ddp.search_anime(test))
#print(bgm.get_other_name(404809))

class Myanimelist:
    def __init__(self):
        with open('token.json', 'r') as file:
            tokens = json.load(file)
        self.token = tokens['access_token']
        self.url = 'https://api.myanimelist.net'
        self.headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    def update_animes(self,malid,status):
        data = {
            'status': status
        }
        url = self.url + '/v2/anime/{}/my_list_status'.format(malid)
        requests.put(url,headers=self.headers,data=data)
    def update(self,anilist:list,status):
        for i in anilist:
            self.update_animes(i,status)
            time.sleep(1)

if __name__ == '__main__':
    print('现在开始迁移 迁移前请注意是否mal鉴权成功')
    ddp = DDplay()
    bgm = Bangumi()
    mal = Myanimelist()
    l1 = bgm.sort_animes()
    print('在看：{} 看过：{} 看完：{}'.format(len(l1['watching']),len(l1['have_watched']),len(l1['wanted'])))
    ddp.search_anime(l1)
    mal.update(l2,'watching')
    mal.update(l3,'completed')
    mal.update(l4,'plan_to_watch')