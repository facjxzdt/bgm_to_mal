import json
import re
import time

import requests

bangumi_token = ''
bangumi_user = ''

l1 = {}
l2 = []
l3 = []
l4 = []

p1 = []
p2 = []
p3 = []


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
        url = self.api_url + '/v0/subjects/{}'.format(str(bgm_id))
        page = requests.get(url, headers=self.headers)
        _json = page.json()
        names.append(_json['name'])
        for i in _json['infobox']:
            if i['key'] == '中文名':
                names.append(i['value'])
            elif i['key'] == '别名':
                for j in i['value']:
                    names.append(j['v'])
        return names

    # 关于bgm：type=1想看 2看完 3正在看
    def sort_animes(self):
        count = 0
        anime_list = self.get_collection()
        wanted = []
        watching = []
        have_watched = []
        animes = {}
        for anime in anime_list:
            _l = {}
            if anime['type'] == 1:
                _l = {anime['subject']['id']: self.get_other_name(anime['subject']['id'])}
                print(_l)
                print('bgm侧已完成{}'.format(count))
                count += 1
                wanted.append(_l)
            elif anime['type'] == 2:
                _l = {anime['subject']['id']: self.get_other_name(anime['subject']['id'])}
                print(_l)
                print('bgm侧已完成{}'.format(count))
                count += 1
                have_watched.append(_l)
            elif anime['type'] == 3:
                _l = {anime['subject']['id']: self.get_other_name(anime['subject']['id'])}
                print(_l)
                print('bgm侧已完成{}'.format(count))
                count += 1
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

        anl_watching = []
        anl_watched = []
        anl_wanted = []

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
                    for m in ids:
                        if m['name'] == 'Bangumi.tv':
                            match = re.search(r'/subject/(\d+)', m['url'])
                            if match:
                                subject_id = match.group(1)
                            else:
                                continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        for m1 in ids:
                            if m1['name'] == 'MyAnimeList':
                                match_mal = re.search(r'/anime/(\d+)', m1['url'])
                                if match_mal:
                                    mal_id = match_mal.group(1)
                                    mal_watching.append(mal_id)
                                    print(mal_id)
                                else:
                                    continue
                            if m1['name'] == 'AniList':
                                match_anl = re.search(r'/anime/(\d+)', m1['url'])
                                if match_anl:
                                    anl_id = match_anl.group(1)
                                    anl_watching.append(anl_id)
                                    print(anl_id)
                                else:
                                    continue
            except:
                pass
            global l2
            l2 = mal_watching
            global p1
            p1 = anl_watching
            print(anl_watching)
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
                    for m in ids:
                        if m['name'] == 'Bangumi.tv':
                            match = re.search(r'/subject/(\d+)', m['url'])
                            if match:
                                subject_id = match.group(1)
                            else:
                                continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        for m1 in ids:
                            if m1['name'] == 'MyAnimeList':
                                match_mal = re.search(r'/anime/(\d+)', m1['url'])
                                if match_mal:
                                    mal_id = match_mal.group(1)
                                    mal_watched.append(mal_id)
                                    print(mal_id)
                                else:
                                    continue
                            if m1['name'] == 'AniList':
                                match_anl = re.search(r'/anime/(\d+)', m1['url'])
                                if match_anl:
                                    anl_id = match_anl.group(1)
                                    anl_watched.append(anl_id)
                                    print(anl_id)
                                else:
                                    continue
            except:
                pass
            global l3
            l3 = mal_watched
            global p2
            p2 = anl_watched
            print(anl_watched)
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
                    for m in ids:
                        if m['name'] == 'Bangumi.tv':
                            match = re.search(r'/subject/(\d+)', m['url'])
                            if match:
                                subject_id = match.group(1)
                            else:
                                continue
                    if str(list(i.keys())[0]) == str(subject_id):
                        print(1)
                        for m1 in ids:
                            if m1['name'] == 'MyAnimeList':
                                match_mal = re.search(r'/anime/(\d+)', m1['url'])
                                if match_mal:
                                    mal_id = match_mal.group(1)
                                    mal_wanted.append(mal_id)
                                    print(mal_id)
                                else:
                                    continue
                            if m1['name'] == 'AniList':
                                match_anl = re.search(r'/anime/(\d+)', m1['url'])
                                if match_anl:
                                    anl_id = match_anl.group(1)
                                    anl_wanted.append(anl_id)
                                    print(anl_id)
                                else:
                                    continue
            except:
                pass
            global l4
            l4 = mal_wanted
            global p3
            p3 = anl_wanted
            print(mal_wanted)
            print(anl_wanted)


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

    def update_animes(self, malid, status):
        data = {
            'status': status
        }
        url = self.url + '/v2/anime/{}/my_list_status'.format(malid)
        requests.put(url, headers=self.headers, data=data)

    def update(self, anilist: list, status):
        for i in anilist:
            self.update_animes(i, status)
            time.sleep(1)

class Anilist:
    def __init__(self):
        with open('anl_token.json', 'r') as token_file:
            self.token = json.load(token_file)['access_token']
            print(self.token)
    def update_anime_list(self,media_id, status, progress):
        url = 'https://graphql.anilist.co'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        query = '''
        mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int) {
            SaveMediaListEntry (mediaId: $mediaId, status: $status, progress: $progress) {
                id
                status
                progress
            }
        }
        '''
        variables = {
            'mediaId': media_id,
            'status': status,
            'progress': progress
        }
        response = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
        return response.json()

    def update(self,status,progress,_anilist):
        print(_anilist)
        for i in _anilist:
            print(self.update_anime_list(i,status,progress=progress))
            print('ok')
            time.sleep(2)
if __name__ == '__main__':
    print('现在开始迁移 迁移前请注意是否mal鉴权成功')
    ddp = DDplay()
    bgm = Bangumi()
    mal = Myanimelist()
    #anl = Anilist()
    l1 = bgm.sort_animes()
    print('在看：{} 看过：{} 看完：{}'.format(len(l1['watching']), len(l1['have_watched']), len(l1['wanted'])))
    ddp.search_anime(l1)
    mal.update(l2,'watching')
    mal.update(l3,'completed')
    mal.update(l4,'plan_to_watch')
    '''
    anl.update('CURRENT',_anilist=p1,progress=0)
    anl.update('COMPLETED',_anilist=p2,progress=0)
    anl.update('PLANNING',_anilist=p3,progress=0)
    '''
