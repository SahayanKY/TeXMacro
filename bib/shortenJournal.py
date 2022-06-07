import sys
import os
import re
import csv

import pandas as pd
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')



# bibファイルへのパス
bibFilePath = 'export.bib'
newbibFilePath = 'newexport.bib'


class AbbConverter:
    """
    LTWAに基づいて入力された単語を略語に変換する
    https://www.issn.org/services/online-services/access-to-the-ltwa/

    nltk
    https://self-development.info/%E3%80%90python%E3%80%91%E8%87%AA%E7%84%B6%E8%A8%80%E8%AA%9E%E5%87%A6%E7%90%86%E3%83%A9%E3%82%A4%E3%83%96%E3%83%A9%E3%83%AA%E3%81%AEnltk%E3%82%92%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB/
    https://qiita.com/m__k/items/ffd3b7774f2fde1083fa
    """

    def __init__(self):
        """
        コンストラクタ
        """

        # 一々変換するのは無駄なので変換した結果を保持しておく
        # 以前の変換履歴をロードする
        self.__journalTablePath = 'journal.csv'
        if os.path.exists(self.__journalTablePath):
            df = pd.read_csv(self.__journalTablePath, encoding='utf-8', sep=';')
            self.__journalDict = df.set_index('NAME').to_dict()['ABBREVIATION']
        else:
            self.__journalDict = {}

        # 単語の略語への変換表をロードする
        self.__wordTablePath = 'ltwa_20210702.csv'
        df = pd.read_csv(self.__wordTablePath, encoding='utf-8', sep=';')
        # n.a.を除外
        df = df[df['ABBREVIATIONS']!='n.a.']


        # 複合語の変換テーブル
        self.__compwordConvertTable = df[df['WORDS'].str.contains(' ')]

        # 複合語を除外
        df = df[~df['WORDS'].str.contains(' ')]
        #
        # journal -> j. の様に完全一致のパターン0
        # chemic- -> chem. の様に前方一致のパターン1
        # -field -> -f. の様に後方一致のパターン2
        # -graph- -> -gr. の様に前方・後方一致のパターン3
        # の3種に分けて考える
        # 先頭・末端のハイフンは取り除いておく
        self.__convertTable0 = df[df['WORDS'].str.contains('^[^-].+[^-]$')]
        self.__convertTable1 = df[df['WORDS'].str.contains('^[^-].+-$')].replace('-$', '', regex=True)
        self.__convertTable2 = df[df['WORDS'].str.contains('^-.+[^-]$')].replace('^-', '', regex=True)
        self.__convertTable3 = df[df['WORDS'].str.contains('^-[^-]+-$')].replace('^-', '', regex=True).replace('-$', '', regex=True)


    def convert(self, name):
        """
        入力された文字列nameをISO4に基づいて略称を得る
        """

        if name in self.__journalDict:
            # 以前に変換したことのある名称ならば辞書を参照し、それを返す
            return self.__journalDict[name]

        #
        # 新しく略称を生成する場合
        #

        # 複合語をまず変換
        # united states of america等
        # 複合語に冠詞等が含まれている可能性があるため、dropする前に置換しておく
        # 該当しそうな複合語パターンを絞り込む
        compwordConvertTable = self.__checkCompoundWord(name)
        if len(compwordConvertTable) != 0:
            # 該当しそうなパターンが見つかった場合
            # TODO 複数の複合語が含まれている可能性を考慮した置換の仕方にする

            pass

        # トークンリストを取得
        tokens = self.__getTokens(name)

        # 冠詞などを除去
        tokens = self.__dropTokens(tokens)

        if len(tokens) == 1:
            # Natureなど、名詞1単語のみの名前の場合は略語に置換しない
            # 辞書に新しく追加する
            abb = tokens[0][0]
        else:
            # 一般の場合(2単語以上の略語を含む場合)
            # 略語トークンリストを取得
            tokens = [self.__convertAbb(t) for t,pos in tokens]
            # トークンを結合して一つの文にする
            abb = self.__joinTokens(tokens)

        # 辞書に新しく追加する
        self.__journalDict[name] = abb
        return abb

    def __getTokens(self, sentence):
        """
        入力された文をトークンに分解し、
        品詞を解析する

        journal of the american chemical society
        > [('journal', 'NN'), ('of', 'IN'), ('the', 'DT'), ('american', 'JJ'), ('chemical', 'NN'), ('society', 'NN')]
        """
        tokens = nltk.word_tokenize(sentence)
        tagged = nltk.pos_tag(tokens)

        return tagged

    def __dropTokens(self, tokens):
        """
        入力されたトークンリストから
        冠詞・前置詞・接続詞を取り除く
        DT ... a, the (限定詞)
        IN ... of, after, for (前置詞、従属接続詞)
        CC ... and, (調整接続詞)
        """
        droppedTokens = [(t,pos) for t,pos in tokens if pos not in ['DT','IN','CC']]

        return droppedTokens

    def __convertAbb(self, token):
        """
        入力されたトークン(単語)をISO4(LTWA)の変換表に基づいて略語に直す
        """

        # chemic- -> chem. の様に前方一致のパターン1
        # -graph- -> -gr. の様に前方・後方一致のパターン3
        # -field -> -f. の様に後方一致のパターン2
        # この順に置換していく

        print('next converted: {}'.format(token))

        # 'chemic' in 'chemical'等を判定する
        matchfunc = lambda patt : patt.upper() in token.upper()

        ##########################################
        # パターン0
        df = self.__convertTable0
        # 一致するパターンを取り出す(case:大文字小文字区別なし)
        df = df[df['WORDS'].str.contains('^'+token+'$', case=False)]
        if len(df) == 1:
            # 略語を取り出す
            abb = df.iloc[0]['ABBREVIATIONS']
            # 先頭の文字を大文字に変えて返す
            result = abb.capitalize()
            return result

        ##########################################
        # パターン1
        #
        # 例えばchefjeoiachemic-のようなパターンが存在した場合にこれに引っかかるのでは？
        # -> 'chefjeoiachemic' not in 'chemical'なので大丈夫
        df = self.__convertTable1
        # 先頭の2文字が合うものをまず抽出(case:大文字小文字区別なし)
        df = df[df['WORDS'].str.contains('^'+token[0:2], case=False)]
        # 合うパターンを探す
        df = df[df['WORDS'].map(matchfunc)]
        if len(df) != 0:
            # 最長マッチしているパターンを取り出し、そのパターンに従って略語に置換
            abb =  df.iloc[df['WORDS'].map(len).argmax()]['ABBREVIATIONS']
            # 先頭の文字を大文字に変えて返す
            result = abb.capitalize()
            return result

        ##########################################
        # パターン3
        df = self.__convertTable3
        # 合うパターンを探す
        df = df[df['WORDS'].map(matchfunc)]

        if len(df) != 0:
            # 最長マッチしているパターンを取り出し、そのパターンに従って略語に置換
            # -graph- -> -gr. : word = 'graph', abb = 'gr'
            word, abb = df.iloc[df['WORDS'].map(len).argmax()][['WORDS', 'ABBREVIATIONS']]
            # -graph- -> -gr. ならハイフンの部分を付け足してあげる必要がある
            # ハイフンの部分を取り出すためにword以降を取り除く
            hyphen = re.sub(word.lower()+'.*', '', token.lower())
            result = hyphen.capitalize() + abb
            return result

        ##########################################
        # パターン2
        df = self.__convertTable2
        # 末端の2文字が合うものをまず抽出(case:大文字小文字区別なし)
        df = df[df['WORDS'].str.contains(token[-2:]+'$', case=False)]
        # 合うパターンを探す
        df = df[df['WORDS'].map(matchfunc)]

        if len(df) != 0:
            # 最長マッチしているパターンを取り出し、そのパターンに従って略語に置換
            # -field -> -f. : word = 'field', abb = 'f'
            word, abb =  df.iloc[df['WORDS'].map(len).argmax()][['WORDS', 'ABBREVIATIONS']]
            # -field -> -f. ならハイフンの部分を付け足してあげる必要がある
            # ハイフンの部分を取り出すためにword以降を取り除く
            hyphen = re.sub(word.lower()+'.*', '', token.lower())
            result = hyphen.capitalize() + abb
            return result

        #
        # 合うパターンがなかった場合
        # そのまま返す
        return token

    def __joinTokens(self, tokens):
        """
        入力されたトークンリストを一文になるように結合する
        """
        sentence = ' '.join(tokens)

        # , や : などの直前には空白を入れないので、
        # ' ,' -> ',' や ' :' -> ':' に置換する
        sentence = re.sub(' ,', ',', sentence)
        sentence = re.sub(' :', ':', sentence)

        return sentence

    def __checkCompoundWord(self, name):
        """
        入力された雑誌名中に複合語(united states of america等)が存在するかどうかをとりあえずチェックする
        候補を絞り込むだけなので、正確にマッチングはしない

        戻り値:
        マッチした複合語の変換パターンDataFrame
        候補がない場合は空のDataFrameになる
        """
        # 簡単にスクリーニングするためにパターンのハイフンを除去
        df = self.__compwordConvertTable
        df = df.replace('^-', '', regex=True).replace('-$', '', regex=True)

        # 'chemic' in 'chemical'等を判定する
        matchfunc = lambda patt : patt.upper() in name.upper()
        # 判定
        matchresult = df['WORDS'].map(matchfunc)

        # マッチしたパターンが無くても複数あってもとりあえず候補全部を返す
        # マッチパターンがない場合はlen(df)==0となるのでそれで判別
        matchpattdf = df[matchresult]
        return self.__compwordConvertTable.loc[matchpattdf.index]



    def updateJournalTable(self):
        """
        名称の変換履歴を外部ファイルに書き出し、保存する
        """
        self.__journalDict.to_csv(self.__journalTablePath, sep=';', index=None, quoting=csv.QUOTE_ALL)





