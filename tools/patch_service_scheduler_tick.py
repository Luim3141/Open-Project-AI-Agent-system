"""Script to patch service.py with background reporting scheduler tick."""
from pathlib import Path

path = Path("openproject/ai/gateway/service.py")
content = path.read_text(encoding="utf-8")

# 1. Initialize _reporting_tick_at
old_init = """        self._knowledge_thread = None
        self._native_scan_at = 0"""

new_init = """        self._knowledge_thread = None
        self._native_scan_at = 0
        self._reporting_tick_at = 0"""

assert old_init in content, "old_init not found"
content = content.replace(old_init, new_init, 1)

# 2. Add reporting scheduler tick inside start_knowledge_worker dispatch loop
old_loop = """                        if self.config.get('engineering',{}).get('enabled') is True:
                            from .engineering import scoped_service
                            scan(scoped_service(self,6),20,authority='machine')
                except Exception as error:"""

new_loop = """                        if self.config.get('engineering',{}).get('enabled') is True:
                            from .engineering import scoped_service
                            scan(scoped_service(self,6),20,authority='machine')
                    # Background reporting scheduler tick (Finding B)
                    if self.config.get('engineering', {}).get('enabled') is True and time.monotonic() >= self._reporting_tick_at:
                        self._reporting_tick_at = time.monotonic() + 30
                        from .engineering import scoped_service
                        from . import engineering_reporting
                        engineering_reporting.check_and_run_scheduled_reports(scoped_service(self, 6), 20)
                except Exception as error:"""

assert old_loop in content, "old_loop not found"
content = content.replace(old_loop, new_loop, 1)

path.write_text(content, encoding="utf-8")
print("SUCCESSFULLY PATCHED service.py")
