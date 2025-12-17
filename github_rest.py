import requests
import json
from datetime import datetime
from collections import Counter
import os

class GitHubAnalyzer:
    def __init__(self, username, token=None, save_raw=False):
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
        self.save_raw = save_raw
        if save_raw:
            self.raw_data_dir = "github_raw_data"
            os.makedirs(self.raw_data_dir, exist_ok=True)
    
    def _save_raw_json(self, filename, data):
        """Raw JSON 데이터를 파일로 저장"""
        if self.save_raw:
            filepath = os.path.join(self.raw_data_dir, f"{self.username}_{filename}")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Raw 데이터 저장: {filepath}")
    
    def _print_raw_json(self, title, data):
        """Raw JSON을 화면에 출력"""
        print(f"\n{'='*60}")
        print(f"📄 {title} - Raw JSON")
        print('='*60)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print('='*60)
    
    def get_user_info(self, show_raw=False):
        """사용자 기본 정보"""
        url = f"{self.base_url}/users/{self.username}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"응답: {response.text}")
            return None
        
        data = response.json()
        
        # Raw JSON 출력/저장
        if show_raw:
            self._print_raw_json("사용자 정보", data)
        self._save_raw_json("user_info.json", data)
        
        # 요약 정보 출력
        print("\n" + "=" * 60)
        print(f"👤 사용자: {data.get('name', 'N/A')} (@{data['login']})")
        print(f"📝 Bio: {data.get('bio', 'N/A')}")
        print(f"📍 위치: {data.get('location', 'N/A')}")
        print(f"📊 공개 레포: {data['public_repos']}개")
        print(f"👥 팔로워: {data['followers']}명 | 팔로잉: {data['following']}명")
        print(f"📅 가입일: {data['created_at'][:10]}")
        print(f"🔗 URL: {data['html_url']}")
        print("=" * 60)
        
        return data
    
    def get_repositories(self, show_raw=False):
        """전체 레포지토리 목록"""
        url = f"{self.base_url}/users/{self.username}/repos"
        params = {"per_page": 100, "sort": "updated"}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(f"응답: {response.text}")
            return []
        
        repos = response.json()
        
        # Raw JSON 출력/저장
        if show_raw:
            self._print_raw_json(f"레포지토리 목록 (총 {len(repos)}개)", repos[:3])  # 처음 3개만 출력
        self._save_raw_json("repositories.json", repos)
        
        # 요약 정보 출력
        print(f"\n📦 총 {len(repos)}개의 레포지토리 발견\n")
        
        for i, repo in enumerate(repos[:10], 1):  # 최근 10개만 출력
            print(f"{i}. {repo['name']}")
            print(f"   ⭐ {repo['stargazers_count']} | 🍴 {repo['forks_count']} | 언어: {repo.get('language', 'N/A')}")
            print(f"   업데이트: {repo['updated_at'][:10]}")
        
        return repos
    
    def get_single_repo_languages(self, repo_name, show_raw=False):
        """특정 레포지토리의 언어 정보 (Raw 데이터 확인용)"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/languages"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            if show_raw:
                self._print_raw_json(f"{repo_name} 언어 정보", data)
            return data
        return {}
    
    def analyze_languages(self, repos, show_raw=False):
        """사용 언어 분석"""
        language_bytes = Counter()
        all_lang_data = {}
        
        print("\n🔍 언어별 코드 분석 중...")
        for repo in repos:
            if repo['fork']:  # 포크한 레포는 제외
                continue
            
            url = f"{self.base_url}/repos/{self.username}/{repo['name']}/languages"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                languages = response.json()
                all_lang_data[repo['name']] = languages
                for lang, bytes_count in languages.items():
                    language_bytes[lang] += bytes_count
        
        # Raw JSON 출력/저장
        if show_raw:
            self._print_raw_json("전체 레포지토리 언어 데이터", all_lang_data)
        self._save_raw_json("languages.json", all_lang_data)
        
        # 요약 정보 출력
        print("\n" + "=" * 60)
        print("💻 언어 분포 (바이트 기준)")
        print("=" * 60)
        
        total_bytes = sum(language_bytes.values())
        for lang, bytes_count in language_bytes.most_common(10):
            percentage = (bytes_count / total_bytes) * 100
            bar = "█" * int(percentage / 2)
            print(f"{lang:20s} {bar:50s} {percentage:5.1f}%")
        
        return language_bytes
    
    def get_single_repo_commits(self, repo_name, per_page=10, show_raw=False):
        """특정 레포지토리의 커밋 정보 (Raw 데이터 확인용)"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/commits"
        params = {"per_page": per_page}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if show_raw:
                self._print_raw_json(f"{repo_name} 최근 커밋 {per_page}개", data)
            return data
        return []
    
    def analyze_commit_times(self, repos, show_raw=False):
        """커밋 시간대 분석"""
        commit_hours = []
        all_commits_data = {}
        
        print("\n🕐 커밋 시간대 분석 중 (최근 활동 레포 3개)...")
        
        for repo in repos[:3]:
            url = f"{self.base_url}/repos/{self.username}/{repo['name']}/commits"
            params = {"per_page": 30}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                commits = response.json()
                all_commits_data[repo['name']] = commits
                
                for commit in commits:
                    try:
                        date_str = commit['commit']['author']['date']
                        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                        hour = (dt.hour + 9) % 24  # UTC -> KST
                        commit_hours.append(hour)
                    except:
                        continue
        
        # Raw JSON 출력/저장
        if show_raw:
            self._print_raw_json("커밋 데이터 (3개 레포)", all_commits_data)
        self._save_raw_json("commits.json", all_commits_data)
        
        if not commit_hours:
            print("커밋 데이터를 찾을 수 없습니다.")
            return
        
        # 요약 정보 출력
        print("\n" + "=" * 60)
        print("⏰ 시간대별 커밋 분포 (KST 기준)")
        print("=" * 60)
        
        hour_counter = Counter(commit_hours)
        max_count = max(hour_counter.values())
        
        for hour in range(24):
            count = hour_counter.get(hour, 0)
            bar = "▓" * int((count / max_count) * 40) if count > 0 else ""
            print(f"{hour:02d}시: {bar:40s} ({count}개)")
        
        # 특성 분석
        night_commits = sum(1 for h in commit_hours if 22 <= h or h < 6)
        morning_commits = sum(1 for h in commit_hours if 6 <= h < 12)
        afternoon_commits = sum(1 for h in commit_hours if 12 <= h < 18)
        evening_commits = sum(1 for h in commit_hours if 18 <= h < 22)
        
        total = len(commit_hours)
        print("\n📊 시간대 특성:")
        print(f"   🌙 새벽 (22-06시): {night_commits}개 ({night_commits/total*100:.1f}%)")
        print(f"   🌅 오전 (06-12시): {morning_commits}개 ({morning_commits/total*100:.1f}%)")
        print(f"   ☀️  오후 (12-18시): {afternoon_commits}개 ({afternoon_commits/total*100:.1f}%)")
        print(f"   🌆 저녁 (18-22시): {evening_commits}개 ({evening_commits/total*100:.1f}%)")
        
        # 캐릭터 타입 추천
        if night_commits / total > 0.4:
            print("\n🦉 코딩 스타일: '새벽형 올빼미 마법사' - 밤의 에너지로 코드를 소환합니다!")
        elif morning_commits / total > 0.4:
            print("\n🐓 코딩 스타일: '아침형 얼리버드' - 새벽 이슬과 함께 코드를 짭니다!")
        else:
            print("\n⚖️ 코딩 스타일: '밸런스 코더' - 시간에 구애받지 않는 올라운더!")
        
        return commit_hours
    
    def get_rate_limit(self):
        """API 사용량 확인"""
        url = f"{self.base_url}/rate_limit"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            core = data['resources']['core']
            graphql = data['resources']['graphql']
            
            print("\n" + "=" * 60)
            print("📡 API Rate Limit 상태")
            print("=" * 60)
            print(f"REST API:")
            print(f"  남은 요청: {core['remaining']} / {core['limit']}")
            reset_time = datetime.fromtimestamp(core['reset'])
            print(f"  리셋 시각: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\nGraphQL API:")
            print(f"  남은 요청: {graphql['remaining']} / {graphql['limit']}")
            
            self._save_raw_json("rate_limit.json", data)


def main():
    print("🚀 GitHub 개발자 프로필 분석기 (Raw Data 버전)\n")
    
    # 사용자 입력
    username = input("GitHub 사용자 이름: ").strip()
    token = input("Personal Access Token (선택): ").strip() or None
    
    # Raw 데이터 옵션
    show_raw = input("Raw JSON을 화면에 출력할까요? (y/n, 기본 n): ").strip().lower() == 'y'
    save_raw = input("Raw JSON을 파일로 저장할까요? (y/n, 기본 y): ").strip().lower() != 'n'
    
    # 분석 시작
    analyzer = GitHubAnalyzer(username, token, save_raw=save_raw)
    
    # 1. 사용자 정보
    print("\n" + "="*60)
    print("1️⃣ 사용자 기본 정보")
    print("="*60)
    user_info = analyzer.get_user_info(show_raw=show_raw)
    if not user_info:
        return
    
    # 2. 레포지토리 목록
    print("\n" + "="*60)
    print("2️⃣ 레포지토리 목록")
    print("="*60)
    repos = analyzer.get_repositories(show_raw=show_raw)
    if not repos:
        print("레포지토리를 찾을 수 없습니다.")
        return
    
    # 3. 개별 레포 상세 정보 (옵션)
    if show_raw and len(repos) > 0:
        print("\n" + "="*60)
        print("3️⃣ 첫 번째 레포지토리 상세 정보 예시")
        print("="*60)
        first_repo = repos[0]['name']
        print(f"\n🔍 {first_repo}의 언어 정보:")
        analyzer.get_single_repo_languages(first_repo, show_raw=True)
        
        print(f"\n🔍 {first_repo}의 최근 커밋 5개:")
        analyzer.get_single_repo_commits(first_repo, per_page=5, show_raw=True)
    
    # 4. 언어 분석
    print("\n" + "="*60)
    print("4️⃣ 언어 분석")
    print("="*60)
    analyzer.analyze_languages(repos, show_raw=show_raw)
    
    # 5. 커밋 시간대 분석
    print("\n" + "="*60)
    print("5️⃣ 커밋 시간대 분석")
    print("="*60)
    analyzer.analyze_commit_times(repos, show_raw=show_raw)
    
    # 6. API 사용량
    analyzer.get_rate_limit()
    
    # 완료 메시지
    print("\n✅ 분석 완료!")
    if save_raw:
        print(f"📁 Raw 데이터는 'github_raw_data/' 폴더에 저장되었습니다.")
        print(f"   - {username}_user_info.json")
        print(f"   - {username}_repositories.json")
        print(f"   - {username}_languages.json")
        print(f"   - {username}_commits.json")
        print(f"   - {username}_rate_limit.json")


if __name__ == "__main__":
    main()