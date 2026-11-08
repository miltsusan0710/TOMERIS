"""Explain action boundaries; never turn a generated answer into execution."""
import re
from tomeris_learning_review import DesktopService as BaseService

POLICY = ('通常の公開情報の検索、要約、資料収集・整理、計算は、繰り返し許可を求めず進めます。\n\n'
          '外部送信・公開、購入・契約、重要ファイルの削除・上書き、権限変更、個人情報の外部提供は、対象と内容を示して事前確認します。\n\n'
          '暴力・差別・迫害の推奨や扇動が疑われる資料は確認待ちにし、その間も別のテーマを収集します。判定には見逃し・誤検出があります。\n\n'
          '未対応の操作は実行したとは答えません。現在、メール送信・購入・契約・任意ファイル操作の実行機能はありません。'
          '既存の削除・復元などの画面操作は、それぞれの確認手順に従います。')

def important_request(text):
    text=text.strip().rstrip('。！!？?')
    if re.search(r'[「」『』\n]|しない|しないで|せず|やめ|方法|手順|とは|について',text):return None
    if not re.search(r'(?:して|してください|してほしい|してくれ|しろ)$',text):return None
    patterns=(('外部送信・公開',r'(?:メール|メッセージ|SNS|投稿|個人情報|住所|電話番号).*(?:送信|公開|投稿)'),
              ('購入・契約',r'(?:購入|契約|注文|課金)(?:して|してください|してほしい|してくれ|しろ)$'),
              ('ファイル変更',r'(?:ファイル|フォルダ|ディレクトリ|ドライブ).*(?:削除|上書き|消去)'),
              ('権限変更',r'(?:アクセス権|管理者権限|権限).*(?:変更|付与|解除)'))
    return next((kind for kind,pattern in patterns if re.search(pattern,text)),None)

class DesktopService(BaseService):
    def policy_reply(self,text):
        if text.strip().rstrip('。！？!?') in ('実行方針を教えて','確認が必要な操作は','自動でできることは'):
            return self.track(text,POLICY)
        kind=important_request(text)
        if kind:
            return self.track(text,'【実行前の確認が必要な操作：'+kind+'】\n依頼：'+text+
                '\n\nこの種類の操作を会話から実行する機能はまだありません。実行はしていません。'
                '実装時には、対象・変更内容・送信先や費用などを示し、確認を得た内容だけ実行します。'
                '\n今は下書きや手順の提案まで対応できます。')
        return None
    def chat(self,text,model,use_memory=False):
        answer=self.policy_reply(text)
        return answer if answer is not None else super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.policy_reply(question)
        return answer if answer is not None else super().web_chat(question,model,use_memory,automatic,progress)
