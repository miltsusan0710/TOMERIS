"""Explicit local startup-model preference; independent of memory files."""
import json
import os
import tempfile
from tomeris_history_search import DesktopService as SearchService

class DesktopService(SearchService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.startup_model=None; self.settings_notice=''
        path=self.data_dir/'desktop_settings.json'
        try:
            if path.exists():
                if path.stat().st_size>8192: raise ValueError()
                data=json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('model'),str) or not 1<=len(data['model'])<=200:
                    raise ValueError()
                self.startup_model=data['model']
        except (OSError,ValueError):
            self.settings_notice='起動設定を読み取れなかったため、標準のモデル選択を使います。設定ファイルは変更していません。'
    def save_startup_model(self,model):
        if not isinstance(model,str) or model not in self.model_names:
            raise ValueError('接続確認で見つかったローカルモデルを選んでください。')
        path=self.data_dir/'desktop_settings.json'
        fd,name=tempfile.mkstemp(prefix='desktop_settings_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as handle:
                json.dump({'version':1,'model':model},handle,ensure_ascii=False,indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(name,path)
        finally:
            if os.path.exists(name): os.unlink(name)
        self.startup_model=model
        return f'起動時の会話モデルを {model} に設定しました。次に起動したときから選択されます。'

def choose_startup_model(preferred,available,current):
    if preferred and preferred in available:
        return preferred,''
    selected=current if current in available else (available[0] if available else current)
    if preferred and available:
        return selected,f'保存したモデル {preferred} が見つからないため、今回は {selected} を選択しました。保存設定は変更していません。'
    return selected,''
