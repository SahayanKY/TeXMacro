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
        df = pd.read_csv(self.__journalTablePath, encoding='utf-8', sep=';')
        self.__journalDict = df.set_index('NAME').to_dict()['ABBREVIATION']

        # 単語の略語への変換表をロードする
        self.__wordTablePath = 'ltwa_20210702.csv'
        df = pd.read_csv(self.__wordTablePath, encoding='utf-8', sep=';')
        # chemic- -> chem. の様に前方一致のパターン1
        # -field -> -f. の様に後方一致のパターン2
        # -graph- -> -gr. の様に前方・後方一致のパターン3
        # の3種に分けて考える
        self.__convertTable1 = df[df['WORDS'].str.contains('-$')]
        self.__convertTable2 = df[df['WORDS'].str.contains('^-')]
        self.__convertTable3 = df[df['WORDS'].str.contains('^-[^-]+-$')]


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

        # トークンリストを取得
        tokens = self.__getTokens(name)
        # 冠詞などを除去
        tokens = self.__dropTokens(tokens)
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
        droppedTokens = [(t,pos) for t,pos in tokens if pos not in ['DT','IN','NN']]

        return droppedTokens

    def __convertAbb(self, token):
        """
        入力されたトークン(単語)をISO4(LTWA)の変換表に基づいて略語に直す
        """
        # TODO 実装
        abb = none

        return abb

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

    def updateJournalTable(self):
        """
        名称の変換履歴を外部ファイルに書き出し、保存する
        """
        self.__journalDict.to_csv(self.__journalTablePath, sep=';', index=None, quoting=csv.QUOTE_ALL)





