from pathlib import Path
p=Path('outputs/tomeris_capabilities.py');s=p.read_text(encoding='utf-8')
s=s.replace('def __init__(self,model,turns): self.base=LocalProvider(model=model); self.turns=turns','def __init__(self,model,turns,style=""): self.base=LocalProvider(model=model); self.turns=turns; self.style=style')
s=s.replace("return self.base.generate(messages[:-1]+context+messages[-1:])", "style=[{'role':'system','content':self.style}] if self.style else []\n        return self.base.generate(messages[:-1]+style+context+messages[-1:])")
s=s.replace('answer=core.generate_checked_response(ContextProvider(model,self.session_turns),self.store,query)', 'from tomeris_conversation_preferences import conversation_style\n        answer=core.generate_checked_response(ContextProvider(model,self.session_turns,conversation_style(self.store)),self.store,query)')
p.write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_desktop_v0311.py').read_text(encoding='utf-8').replace('from tomeris_location_guard import','from tomeris_conversation_preferences import').replace('v0.31.1','v0.32')
Path('outputs/tomeris_desktop_v032.py').write_text(s,encoding='utf-8')
