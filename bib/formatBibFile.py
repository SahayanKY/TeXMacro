import sys
import platform
import argparse
import re


def findIndexes(string, obj):
    """
    stringに含まれるobjの位置を全て検索
    インデックスのリストを返す
    """
    indexList = []
    start = 0
    while True:
        i = string.find(obj, start)
        if i == -1:
            break
        indexList.append(i)
        start = i+1
    return indexList

def loadBibFile(bibFilePath):
    # bibファイル読み込み
    # 改行コードを変更しない(newline='')
    with open(bibFilePath, mode='r', encoding='UTF-8', newline='') as f:
        bibData = f.read()
    # 改行コードとタブ文字を除去
    bibData = re.sub('\r', '', re.sub('\n', '', re.sub('\t','',bibData)))

    # bibData内の構造を解析するため、括弧のネスト具合を調べる
    # 括弧の存在する位置を特定
    leftbraceIndexList = findIndexes(bibData, '{')
    rightbraceIndexList = findIndexes(bibData, '}')
    # bibDataの各位置におけるネストレベルを計算
    nestLevel = np.zeros(len(bibData), dtype=np.int32)
    for i in leftbraceIndexList:
        nestLevel[i:] += 1
    for i in rightbraceIndexList:
        nestLevel[i:] -= 1

    # rootレベル(レベル0)はbibエントリーの区切り位置に存在するので、
    # エントリーの区切りに用いる
    rightbraceNestLevel = nestLevel[rightbraceIndexList]
    rightbraceRootLevelIndexList = np.array(rightbraceIndexList)[np.where(rightbraceNestLevel == 0)[0]]

    # エントリーリストの保存先を確保
    entryList = []
    # rootレベル毎のbibDataを切り分け、それぞれをcovertBibEntryToDictに投げる
    start = 0
    for end in rightbraceRootLevelIndexList:
        end += 1
        __bibData = bibData[start:end]
        __nestLevel = nestLevel[start:end]
        entryList.append(__convertBibEntryToDict(__bibData, __nestLevel))
        start = end

    return entryList

def __convertBibEntryToDict(entryStr, nestLevel):
    if len(entryStr) != len(nestLevel):
        raise ValueError('lengths of two arrays didnot match.')

    commaIndexList = findIndexes(entryStr, ',')
    newlinecommaIndexList = np.array(commaIndexList)[np.where(nestLevel[commaIndexList] == 1)[0]]
    linedata = []
    start = 0
    for end in newlinecommaIndexList:
        linedata.append(entryStr[start:end])
        start = end + 1
    linedata.append(entryStr[start:-1])
    # start と -1が同じ位置になる場合(***},}等、最後に余計に','が入っていた場合、空文字になる)
    # -> 後で取り除く
    """linedata==
    ['@article{RefWorks:RefID:204-palmer2010universal',
     'author={David S. Palmer and Andrey I. Frolov and Ekaterina L. Ratkova and Maxim V. Fedorov}',
     'year={2010}',
     'month={Dec 15,}',
     'title={Towards a universal method for calculating hydration free energies: a 3D reference interaction site model with partial molar volume correction}',
     'journal={Journal of physics. Condensed matter}',
     'volume={22}',
     'number={49}',
     'pages={492101}',
     'note={3D-RISM/KH?による溶媒和エネルギーは実験値に対して17.3kcal/mol過大評価した。その誤差はモル体積と強い相関があることが示される}',
     'abstract={We report a simple universal method to systematically improve the accuracy of hydration free energies calculated using an integral equation theory of molecular liquids, the 3D reference interaction site model. A strong linear correlation is observed between the difference of the experimental and (uncorrected) calculated hydration free energies and the calculated partial molar volume for a data set of 185 neutral organic molecules from different chemical classes. By using the partial molar volume as a linear empirical correction to the calculated hydration free energy, we obtain predictions of hydration free energies in excellent agreement with experiment (R = 0.94, σ = 0.99\xa0kcal\xa0mol (- 1) for a test set of 120 organic molecules).}',
     'isbn={0953-8984}',
     'url={http://iopscience.iop.org/0953-8984/22/49/492101}',
     'doi={10.1088/0953-8984/22/49/492101}']
    """
    # 1行目は'{'でsplit
    # 2行目以降は'='でsplit
    # 行頭、行末、区切り文字前後の空白は取り除いておく
    splitlinedata = [0] * len(linedata)
    splitlinedata[0] = re.split(' *{ *', re.sub('^ +','', re.sub(' +$','', linedata[0])))
    for i in range(1, len(linedata)):
        # サイズ2固定でsplit
        splitlinedata[i] = re.split(' *= *', re.sub('^ +','', re.sub(' +$','', linedata[i])), 1)

    # チェック
    # 1行目は
    # - 2要素でなければならない
    # - 1要素目は'@'から始まらなければならない
    # 2行目以降は
    # - 2要素が正常
    # - 1要素の場合空文字(もしくは空白文字の連続(ただしsplit時に空文字に変換済み))でなければならない(その場合はlistから除外する)
    # - 2要素目が'{}'で囲まれている場合は'{}'を外す
    dropList = []
    for i, l in enumerate(splitlinedata):
        if i == 0:
            if len(l) != 2:
                raise ValueError('not 2 elements')
            if not l[0].startswith('@'):
                raise ValueError('not start with @')
        else:
            if len(l) == 2:
                if l[1].startswith('{'):
                    l[1] = l[1][1:-1]
                continue
            elif len(l) == 1:
                if l[0] == '':
                    dropList.append(i)
                else:
                    raise ValueError('failed to parse: {}'.format(l[0]))
            else:
                # 基本的にあり得ない(split('=',1)のため)
                pass

    # 空文字の行は除去
    splitlinedata = [l for i,l in enumerate(splitlinedata) if i not in dropList]
    # 1行目の'@'を除去
    splitlinedata[0][0] = splitlinedata[0][0][1:]

    # 辞書型に変換
    entryDict = dict(splitlinedata[1:])
    entryDict['entry'] = splitlinedata[0][0]
    entryDict['id'] = splitlinedata[0][1]

    return entryDict





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='formatBibFile : Automatically format bib file to shorten journal name and to replace illegal char.')

    parser.add_argument('bibFilePath', help='path to bib file')
    parser.add_argument('--removeAbst', help='flag to remove abstracts', action='store_true')

    args = parser.parse_args()

    # バージョン確認
    print('python:{}'.format(platform.python_version()))
    if sys.version_info[0] != 3:
        print('Warnings:formatBibFile assumes python3.')

    # bibファイル読み込み
    bibEntryList = loadBibFile(args.bibFilePath)


