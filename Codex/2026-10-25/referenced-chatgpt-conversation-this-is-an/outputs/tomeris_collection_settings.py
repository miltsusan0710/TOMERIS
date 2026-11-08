"""Persistent auto-collection switch; corrupt state stops collection."""
import json,os,tempfile,time
from tomeris_public_learning import DesktopService as BaseService,TOPICS
MAX_SETTINGS_BYTES=4096

def validate_settings(data):
    if not isinstance(data,dict) or set(data)!={'version','enabled'} or type(data['version']) is not int or data['version']!=1 or type(data['enabled']) is not bool:
        raise ValueError('自動収集設定の形式が不正です。')
    return data

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.auto_settings_path=self.data_dir/'auto_collection.json';self.auto_settings_error=''
        try:
            if self.auto_settings_path.exists():
                with self.auto_settings_path.open('rb') as f:raw=f.read(MAX_SETTINGS_BYTES+1)
                if len(raw)>MAX_SETTINGS_BYTES:raise ValueError('設定の容量超過')
                self.auto_sources_enabled=validate_settings(json.loads(raw))['enabled']
        except (ValueError,OSError,UnicodeError):
            self.auto_sources_enabled=False;self.auto_settings_error='設定を読み取れないため自動収集を停止しています。元ファイルは保持しています。'
    def set_auto_collection(self,enabled):
        if enabled and self.auto_settings_error:raise ValueError(self.auto_settings_error)
        # Even failed persistence must stop the current process immediately.
        if not enabled:self.auto_sources_enabled=False
        if self.auto_settings_error:raise ValueError(self.auto_settings_error)
        raw=json.dumps(validate_settings(dict(version=1,enabled=enabled))).encode('utf-8')
        fd,name=tempfile.mkstemp(prefix='auto_collection_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(name,self.auto_settings_path)
        finally:
            if os.path.exists(name):os.unlink(name)
        self.auto_sources_enabled=enabled
        if enabled:self.auto_sources_next=max(self.auto_sources_next,time.monotonic()+600)
    def prepare_context(self,text):
        command=text.strip().rstrip('。！？!?')
        if command not in ('自動資料収集を停止','自動資料収集を再開','自動資料収集の状態'):return super().prepare_context(text)
        self.clear_tool_context();error=''
        try:
            if command!='自動資料収集の状態':self.set_auto_collection(command=='自動資料収集を再開')
        except (OSError,ValueError) as exc:error='\n設定の保存に失敗しました。'+str(exc)+'\nこの起動中の停止と、次回起動時の設定は別です。'
        answer=('自動資料収集：有効' if self.auto_sources_enabled else '自動資料収集：停止中')+f'\n今回の起動で {self.auto_sources_index}/{len(TOPICS)} テーマを試行。'+self.auto_sources_status
        answer+='\n保存済みの有効／停止設定は次回起動にも引き継ぎます。初回は有効。Wikipediaの固定3テーマのみ、10分以上の間隔で収集します。資料学習の停止中は収集しません。'
        answer+=error or ('\n'+self.auto_settings_error if self.auto_settings_error else '')
        return text,self.track(text,answer)
