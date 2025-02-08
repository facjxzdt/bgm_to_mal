import json
import re
import time
import logging
import os
from typing import Dict, List, Optional
import requests
import webbrowser

# 基础配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CONFIG = {
    'BANGUMI_TOKEN': '',
    'BANGUMI_USER': '',
    'REQUEST_RETRIES': 3,
    'REQUEST_TIMEOUT': 10,
    'API_DELAY': 1,
    'AUTH_SERVER': 'https://auth.amoe.moe',
    'USE_ANILIST': False,
}


class APIClient:
    """基础API客户端"""
    def __init__(self, base_url: str, headers: Dict[str, str] | None = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(headers or {})

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        for attempt in range(CONFIG['REQUEST_RETRIES']):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=CONFIG['REQUEST_TIMEOUT'],
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.warning(f"请求失败: {e}, 重试 {attempt + 1}/{CONFIG['REQUEST_RETRIES']}")
                time.sleep(2 ** attempt)
        return None

class BangumiClient(APIClient):
    """Bangumi API客户端"""
    def __init__(self):
        super().__init__(
            base_url='https://api.bgm.tv',
            headers={
                'User-Agent': 'BangumiSync/1.0',
                'Authorization': f'Bearer {CONFIG["BANGUMI_TOKEN"]}'
            }
        )

    def get_collections(self) -> List[Dict]:
        collections = []
        offset = 0
        limit = 100
        while True:
            data = self._request('GET', 
                               f'/v0/users/{CONFIG["BANGUMI_USER"]}/collections',
                               params={'limit': limit, 'offset': offset})
            if not data or 'data' not in data:
                break
            collections.extend(data['data'])
            if len(data['data']) < limit:
                break
            offset += limit
            time.sleep(CONFIG['API_DELAY'])
        return collections

    def get_subject_info(self, subject_id: int) -> Optional[Dict]:
        """获取动画主题的详细信息"""
        return self._request('GET', f'/v0/subjects/{subject_id}')

    def process_collections(self) -> Dict[str, List[Dict]]:
        """处理收藏数据并进行分类"""
        collections = self.get_collections()
        logging.info(f"获取到 {len(collections)} 条收藏记录")
        categorized = {
            'watching': [],
            'completed': [],
            'planned': []
        }

        for item in collections:
            subject_id = item['subject']['id']
            logging.info(f"正在处理作品 ID: {subject_id}")
            names = self._get_subject_names(subject_id)
            
            if not names:
                logging.error(f"获取作品 ID: {subject_id} 的信息失败")
                continue

            logging.debug(f"作品名称: {names}")
            entry = {
                'subject_id': subject_id,
                'names': names,
                'type': item['type']
            }

            if item['type'] == 1:
                categorized['planned'].append(entry)
            elif item['type'] == 2:
                categorized['completed'].append(entry)
            elif item['type'] == 3:
                categorized['watching'].append(entry)

        logging.info(f"分类统计: 在看 {len(categorized['watching'])}，已完成 {len(categorized['completed'])}，计划看 {len(categorized['planned'])}")
        return categorized

    def _get_subject_names(self, subject_id: int) -> List[str]:
        """获取动画的所有别名"""
        info = self.get_subject_info(subject_id)
        if not info:
            return []

        names = [info.get('name', '')]

        for item in info.get('infobox', []):
            if item['key'] == '中文名':
                names.append(item['value'])
            elif item['key'] == '别名':
                names.extend([v['v'] for v in item['value']])

        return list(set(filter(None, names)))

class DandanPlayClient(APIClient):
    """弹弹play API客户端"""
    def __init__(self):
        super().__init__(
            base_url='https://api.dandanplay.net',
            headers={'User-Agent': 'BangumiSync/1.0'}
        )
        self.auth_server = CONFIG['AUTH_SERVER']



    def _get_auth_headers(self, path: str) -> Dict[str, str]:
        """获取认证头信息"""
        try:
            response = requests.post(
                f"{self.auth_server}/auth",
                json={"path": path}
            )
            response.raise_for_status()
            return response.json()["headers"]
        except Exception as e:
            logging.error(f"获取认证头信息失败: {e}")
            return {}

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """重写_request方法以添加认证头"""
        # 获取认证头
        auth_headers = self._get_auth_headers(endpoint)
        
        # 更新请求头
        headers = kwargs.get('headers', {})
        headers.update(auth_headers)
        kwargs['headers'] = headers
        
        return super()._request(method, endpoint, **kwargs)

    def search_anime(self, keyword: str) -> Optional[Dict]:
        return self._request('GET', '/api/v2/search/anime', params={'keyword': keyword})

    def get_external_ids(self, anime_id: int) -> Dict:
        """获取动画的外部数据库ID"""
        data = self._request('GET', f'/api/v2/bangumi/{anime_id}')
        if not data:  # 添加空值检查
            return {}
        return self._parse_external_ids(data.get('bangumi', {}).get('onlineDatabases', []))

    def _parse_external_ids(self, databases: List[Dict]) -> Dict:
        """解析外部数据库ID"""
        ids = {}
        for db in databases:
            if db['name'] == 'Bangumi.tv':
                if match := re.search(r'/subject/(\d+)', db['url']):
                    ids['bgm'] = match.group(1)
            elif db['name'] == 'MyAnimeList':
                if match := re.search(r'/anime/(\d+)', db['url']):
                    ids['mal'] = match.group(1)
            elif db['name'] == 'AniList':
                if match := re.search(r'/anime/(\d+)', db['url']):
                    ids['anilist'] = match.group(1)
        return ids

    def find_matches(self, bangumi_data: Dict) -> Dict:
        """匹配Bangumi数据到其他平台"""
        matched_ids = {'mal': [], 'anilist': []}
        mapping_data = {
            'matches': [],
            'failed': []
        }
        total_entries = sum(len(entries) for entries in bangumi_data.values())
        processed = 0

        for status, entries in bangumi_data.items():
            for entry in entries:
                processed += 1
                logging.info(f"正在处理第 {processed}/{total_entries} 个条目: {entry['names'][0]}")
                
                match_info = {
                    'bgm_id': entry['subject_id'],
                    'names': entry['names'],
                    'status': status,
                    'matched': False
                }

                # 优先使用日文原名搜索
                primary_name = entry['names'][0]
                result = self.search_anime(primary_name)
                
                if not result or not result.get('animes'):
                    # 如果原名搜索失败，尝试使用中文名
                    if len(entry['names']) > 1:
                        result = self.search_anime(entry['names'][1])
                
                if not result or not result.get('animes'):
                    logging.warning(f"未找到匹配: {entry['names']}")
                    mapping_data['failed'].append(match_info)
                    continue

                # 获取前三个结果并尝试匹配
                for anime in result['animes'][:3]:
                    external_ids = self.get_external_ids(anime['animeId'])
                    if external_ids.get('bgm') == str(entry['subject_id']):
                        match_info.update({
                            'matched': True,
                            'mal_id': external_ids.get('mal'),
                            'anilist_id': external_ids.get('anilist'),
                            'dandanplay_id': anime['animeId']
                        })
                        mapping_data['matches'].append(match_info)
                        
                        if mal_id := external_ids.get('mal'):
                            matched_ids['mal'].append((mal_id, status))
                            logging.info(f"MAL ID 匹配成功: {mal_id}")
                        if anilist_id := external_ids.get('anilist'):
                            matched_ids['anilist'].append((anilist_id, status))
                            logging.info(f"AniList ID 匹配成功: {anilist_id}")
                        break
                
                if not match_info['matched']:
                    mapping_data['failed'].append(match_info)
                
                time.sleep(CONFIG['API_DELAY'])

        # 保存匹配结果到JSON文件
        with open('anime_mappings.json', 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)

        logging.info(f"匹配完成: MAL {len(matched_ids['mal'])} 条, AniList {len(matched_ids['anilist'])} 条")
        logging.info(f"匹配结果已保存到 anime_mappings.json")
        return matched_ids

class MALClient(APIClient):
    """MyAnimeList API客户端"""
    STATUS_MAPPING = {
        'watching': 'watching',
        'completed': 'completed',
        'planned': 'plan_to_watch'
    }

    def __init__(self, token: str):
        """
        初始化MAL客户端
        :param token: MAL的访问令牌
        """
        super().__init__(
            base_url='https://api.myanimelist.net/v2',
            headers={'Authorization': f'Bearer {token}'}
        )

    def update_status(self, item_id: str, status: str) -> bool:
        """更新动画观看状态"""
        mal_status = self.STATUS_MAPPING.get(status)
        if not mal_status:
            return False
        response = self._request('PATCH', f'/anime/{item_id}/my_list_status', 
                               data={'status': mal_status})
        return response is not None

class AniListClient:
    """AniList GraphQL客户端"""
    STATUS_MAPPING = {
        'watching': 'CURRENT',
        'completed': 'COMPLETED',
        'planned': 'PLANNING'
    }

    def __init__(self, token: str):
        """
        初始化AniList客户端
        :param token: AniList的访问令牌
        """
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def update_status(self, item_id: str, status: str) -> bool:
        """更新动画观看状态"""
        anilist_status = self.STATUS_MAPPING.get(status)
        if not anilist_status:
            return False
            
        mutation = """
        mutation ($id: Int, $status: MediaListStatus) {
            SaveMediaListEntry (mediaId: $id, status: $status) {
                id
                status
            }
        }
        """
        variables = {'id': int(item_id), 'status': anilist_status}
        response = requests.post('https://graphql.anilist.co',
                               json={'query': mutation, 'variables': variables},
                               headers=self.headers)
        return response.status_code == 200

class SyncManager:
    """同步管理器"""
    def __init__(self, use_cached_mappings: bool = True):
        self.use_cached_mappings = use_cached_mappings
        self.auth_server = CONFIG['AUTH_SERVER']
        self.mal = None
        self.anilist = None
        self.bangumi = BangumiClient()
        self.dandanplay = DandanPlayClient()
        self.init_clients()

    def init_clients(self):
        """初始化客户端"""
        try:
            print("\n=== 认证流程 ===")
            print("请在每个服务认证完成后，从网页复制显示的access token")
            
            # MAL认证
            print("\n1. 正在打开MAL认证页面...")
            webbrowser.open(f"{self.auth_server}/login/mal")
            mal_token = input("请复制MAL的access token: ").strip()
            
            # AniList认证（仅在启用时进行）
            if CONFIG['USE_ANILIST']:
                print("\n2. 正在打开AniList认证页面...")
                webbrowser.open(f"{self.auth_server}/login/anilist")
                anilist_token = input("请复制AniList的access token: ").strip()
            else:
                anilist_token = None
            
            # 初始化客户端
            if mal_token:
                self.mal = MALClient(mal_token)
                print("MAL客户端初始化成功")
            else:
                raise Exception("MAL token为空")
            
            if CONFIG['USE_ANILIST'] and anilist_token:
                self.anilist = AniListClient(anilist_token)
                print("AniList客户端初始化成功")
            elif CONFIG['USE_ANILIST']:
                raise Exception("AniList token为空")
            
            print("\n=== 认证完成 ===")
            
        except Exception as e:
            logging.error(f"客户端初始化失败: {e}")
            raise

    def sync(self):
        """执行同步"""
        try:
            logging.info("开始同步...")
            
            if self.use_cached_mappings and os.path.exists('anime_mappings.json'):
                logging.info("使用缓存的映射数据...")
                matched_ids = self._load_cached_mappings()
            else:
                logging.info("重新获取并匹配数据...")
                bangumi_data = self.bangumi.process_collections()
                matched_ids = self.dandanplay.find_matches(bangumi_data)
            
            self._sync_to_service('mal', matched_ids.get('mal', []))
            if CONFIG['USE_ANILIST']:
                self._sync_to_service('anilist', matched_ids.get('anilist', []))
            
            logging.info("同步完成！")
            
        except Exception as e:
            logging.error(f"同步过程出错: {e}")
            raise

    def _load_cached_mappings(self) -> Dict:
        """从缓存的JSON文件加载映射数据"""
        matched_ids = {'mal': [], 'anilist': []}
        try:
            with open('anime_mappings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for match in data['matches']:
                    if match['mal_id']:
                        matched_ids['mal'].append((match['mal_id'], match['status']))
                    if match['anilist_id']:
                        matched_ids['anilist'].append((match['anilist_id'], match['status']))
            logging.info(f"从缓存加载: MAL {len(matched_ids['mal'])} 条, AniList {len(matched_ids['anilist'])} 条")
            return matched_ids
        except Exception as e:
            logging.error(f"加载缓存数据失败: {str(e)}")
            return {'mal': [], 'anilist': []}

    def _sync_to_service(self, service: str, items: List[tuple]):
        """通用同步方法"""
        logging.info(f"开始同步到 {service}...")
        client = self.mal if service == 'mal' else self.anilist
        if client is None:
            logging.error(f"{service} 客户端未初始化")
            return
            
        success = 0
        for item_id, status in items:
            try:
                if client.update_status(item_id, status):
                    success += 1
                    logging.info(f"{service} 更新成功: {item_id} -> {status}")
            except Exception as e:
                logging.error(f"{service} 更新出错: {str(e)}")
            time.sleep(CONFIG['API_DELAY'])

        logging.info(f"{service} 同步完成: 成功 {success}/{len(items)}")

class AuthManager:
    """授权管理类"""
    def __init__(self):
        self.auth_server = CONFIG['AUTH_SERVER']


    def check_auth_status(self) -> bool:
        """检查授权状态"""
        try:
            response = requests.get(f"{self.auth_server}/auth/status")
            response.raise_for_status()
            status = response.json()
            return status['mal'] and status['anilist']
        except Exception as e:
            logging.error(f"检查授权状态失败: {e}")
            return False

    def print_auth_instructions(self):
        """打印授权指引"""
        print("\n=== 授权指引 ===")
        print("请在浏览器中完成以下步骤：")
        print(f"1. 访问 {self.auth_server}/login/mal 完成 MyAnimeList 授权")
        print(f"2. 访问 {self.auth_server}/login/anilist 完成 AniList 授权")
        print("\n完成授权后，请按回车键继续...")

    def wait_for_auth(self):
        """等待用户完成授权"""
        while True:
            if self.check_auth_status():
                print("\n✓ 授权完成！开始执行同步任务...\n")
                return True
            
            self.print_auth_instructions()
            input()  # 等待用户按回车
            print("正在检查授权状态...")

def main():
    """主函数"""
    try:
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建同步管理器并执行同步
        manager = SyncManager(use_cached_mappings=False)
        manager.sync()
        
    except Exception as e:
        logging.error(f"程序执行出错: {e}")
        raise

if __name__ == '__main__':
    main()