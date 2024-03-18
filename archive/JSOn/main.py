def main():
    import ijson

    filename = "cd_ua_2023-03.json"
    with open(filename, 'r') as f:
        objects = ijson.items(f, 'item')  # 'item' зависит от структуры вашего JSON
        for obj in objects:
            # теперь вы работаете с одним объектом в JSON, и можете его анализировать
            print(obj['metaData']['declarationId'])




def pandas_json():
    import pandas as pd

    df = pd.read_json('cd_ua_2023-03.json')

    df.to_csv('json.csv', index=None)
if __name__ == '__main__':
    # main()
    pandas_json()
