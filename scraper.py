import logging
import asyncio
from typing import Optional, Callable
from playwright.async_api import async_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)

class CaptionScraper:
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.browser: BrowserContext = None
        self.page: Page = None
        self.running = False
        self.latest_captions = []
        self.on_caption: Optional[Callable[[str], None]] = None # Callback function

    async def connect(self):
        try:
            logger.info(f"Attempting to connect to Chrome at http://localhost:{self.cdp_port}...")
            async with async_playwright() as p:
                # connect_over_cdp connects to an existing browser instance
                try:
                    self.browser = await p.chromium.connect_over_cdp(f"http://localhost:{self.cdp_port}")
                except Exception as e:
                    logger.error(f"Failed to connect to browser: {e}")
                    logger.warning("Ensure Chrome is running with: --remote-debugging-port=9222")
                    return

                logger.info("Connected to Browser. Scanning contexts...")
                contexts = self.browser.contexts
                if not contexts:
                    logger.error("No browser contexts found.")
                    return
                
                # Iterate all pages to find a meeting
                target_page = None
                all_pages = []
                for context in contexts:
                    for page in context.pages:
                        all_pages.append(page.url)
                        if "meet.google.com" in page.url or "zoom.us" in page.url or "teams.microsoft.com" in page.url:
                            target_page = page
                            break
                    if target_page: break
                
                logger.info(f"Open Pages: {all_pages}")
                
                if target_page:
                    self.page = target_page
                    logger.info(f"Attached to meeting tab: {self.page.url}")
                    await self.monitor_captions()
                else:
                    logger.warning("No meeting tab found (Meet/Zoom/Teams). Monitoring ACTIVE tab as fallback.")
                    # Fallback: Monitor the last used page or just the first one
                    if context.pages:
                        self.page = context.pages[0]
                        await self.monitor_captions()
                    else:
                        logger.error("No pages found to monitor.")

        except Exception as e:
            logger.error(f"Global Scraper Error: {e}")

    async def monitor_captions(self):
        self.running = True
        title = await self.page.title()
        logger.info(f"Started monitoring captions on: {title} ({self.page.url})")
        
        # Inject MutationObserver
        await self.page.expose_function("on_caption", self._handle_caption)
        
        # Helper to log from browser to python console
        await self.page.expose_function("py_log", lambda msg: logger.debug(f"[Browser] {msg}"))

        await self.page.evaluate("""
            () => {
                console.log("Stealth Pilot: Injecting Observer...");
                window.py_log("Injecting Observer...");
                
                const observer = new MutationObserver((mutations) => {
                    for (const mutation of mutations) {
                        if (mutation.type === 'childList') {
                            mutation.addedNodes.forEach(node => {
                                let text = "";
                                if (node.nodeType === Node.TEXT_NODE) {
                                    text = node.textContent;
                                } else if (node.innerText) {
                                    text = node.innerText; 
                                }
                                
                                if (text && text.trim().length > 0) {
                                    // Log everything for debug
                                    // window.py_log("Mutation: " + text.substring(0, 30));
                                    window.on_caption(text.trim());
                                }
                            });
                        }
                        else if (mutation.type === 'characterData') {
                             window.on_caption(mutation.target.textContent.trim());
                        }
                    }
                });
                
                // Observe Body to catch everything
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });
                
                window.py_log("Observer Attached to BODY.");
            }
        """)
        
        # Keep alive
        while self.running:
            await asyncio.sleep(1)

    def _handle_caption(self, text: str):
        # Filter noise
        if not text or len(text) < 5: return
        
        # Deduplicate immediate repeats
        if self.latest_captions and text in self.latest_captions[-1]:
            return
            
        self.latest_captions.append(text)
        if len(self.latest_captions) > 10:
            self.latest_captions.pop(0)
            
        logger.info(f"Caption: {text}")
        
        # Heuristic: If it looks like a question, send to UI
        if self.on_caption:
            self.on_caption(text)

    def stop(self):
        self.running = False

