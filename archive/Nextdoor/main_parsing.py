import json
import os
import glob
def main():
    folders = "C:\\scrap_tutorial-master\\Nextdoor\\json\\product\\Atlanta\\*.json"
    files_html = glob.glob(folders)
    for item in files_html[:1]:
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
        city = data_json['data']['neighborhood']['city']
        neighbors = data_json['data']['neighborhood']['neighborhoodStats'][0]['text']['text'].replace(' neighbors', '')


        print(neighbors)


if __name__ == '__main__':
    main()
