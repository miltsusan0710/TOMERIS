from pathlib import Path
root=Path('outputs')
s=(root/'tomeris_desktop_v017.py').read_text(encoding='utf-8-sig').replace('v0.17','v0.18')
s=s.replace('from tomeris_restore import DesktopService as PlanService','from tomeris_history_search import DesktopService as PlanService\nfrom tomeris_history_search_ui import ConversationPanel')
s=s.replace('    def restore_dialog(self):', "        panel=getattr(self,'conversation_panel',None)\n        if panel is not None:\n            panel.state()\n    def restore_dialog(self):")
s=s.replace('    def view(self,kind):',"    def view(self,kind):\n        if kind=='history':\n            if not self.busy and not self.closing:\n                self.conversation_panel=ConversationPanel(self)\n            return")
s=s.replace('                        if not restore_open and not history_open', "                        conversation_open=getattr(self,'conversation_panel',None) and self.conversation_panel.window.winfo_exists()\n                        if not conversation_open and not restore_open and not history_open")
(root/'tomeris_desktop_v018.py').write_text(s,encoding='utf-8')
