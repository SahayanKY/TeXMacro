# journal.jsonに基づいて置換

import os
import re
import json


replaceTablePath = os.path.dirname(__file__) + '/journal.json'
originalBibFile = 'export.bib'
newBibFile = originalBibFile

# テーブル読み込み
replaceTable = json.load(open(replaceTablePath, 'r'))
# bibファイル読み込み
# 改行コードを変更しない(newline='')
with open(originalBibFile, mode='r', encoding='UTF-8', newline='') as f:
    bibData = f.read()

# 各テーブルセット毎に置換処理を行っていく
for orgJ, newJ in replaceTable.items():
    orgStr = r'journal={'+orgJ+'},'
    newStr = 'journal={'+newJ+'},'
    bibData = re.sub(orgStr, newStr, bibData, flags=re.IGNORECASE)

# bibファイル書き込み
# 改行コードを変更しない(newline='')
with open(newBibFile, mode='w', encoding='UTF-8', newline='') as f:
    f.write(bibData)




