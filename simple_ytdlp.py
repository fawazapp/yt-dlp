import json
import re
import sys
import urllib.parse
import urllib.request


def _extract_video_id(url: str) -> str:
    qs = urllib.parse.urlparse(url)
    if qs.hostname in ('youtu.be', 'www.youtu.be'):
        return qs.path.lstrip('/')
    if qs.path == '/watch':
        return urllib.parse.parse_qs(qs.query)['v'][0]
    # fallback to regex
    m = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', url)
    if not m:
        raise ValueError('Invalid YouTube URL')
    return m.group(1)


def get_video_info(url: str) -> dict:
    video_id = _extract_video_id(url)
    with urllib.request.urlopen(url) as resp:
        webpage = resp.read().decode('utf-8')

    api_key = re.search(r"\"INNERTUBE_API_KEY\":\"([^"]+)\"", webpage)
    if not api_key:
        raise ValueError('Unable to extract API key')

    player_url = f"https://www.youtube.com/youtubei/v1/player?key={api_key.group(1)}"
    data = {
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "20.10.38",
                "androidSdkVersion": 30,
            }
        },
        "videoId": video_id,
        "contentCheckOk": True,
        "racyCheckOk": True,
    }
    req = urllib.request.Request(player_url, data=json.dumps(data).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        info = json.loads(resp.read().decode('utf-8'))

    title = info.get('videoDetails', {}).get('title')
    formats = info.get('streamingData', {}).get('formats', []) + \
        info.get('streamingData', {}).get('adaptiveFormats', [])
    formats = [f for f in formats if 'url' in f]
    if not formats:
        raise ValueError('No downloadable formats found')
    best = max(formats, key=lambda f: f.get('height', 0))
    return {'title': title, 'url': best['url']}


def main() -> None:
    if len(sys.argv) != 2:
        print('Usage: python simple_ytdlp.py <YouTube URL>', file=sys.stderr)
        raise SystemExit(1)
    data = get_video_info(sys.argv[1])
    print(json.dumps(data))


if __name__ == '__main__':
    main()
