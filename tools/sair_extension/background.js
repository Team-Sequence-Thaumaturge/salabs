// SAIR Chrome Extension Service Worker (background.js)
console.log("⚡ SAIR 1-Click Auto Injector Background Service Worker initialized!");

let lastTabInjectTimes = {};

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'SAIR_SCAN_TARGET_TABS') {
        chrome.tabs.query({ currentWindow: true }, (tabs) => {
            const detectedTabs = tabs.filter(t => 
                t.url && (
                    t.url.includes('labs.google/fx') || 
                    t.url.includes('flow') || 
                    t.url.includes('jules') ||
                    t.url.includes('gemini.google.com') ||
                    t.url.includes('gemini') ||
                    t.url.includes('manus.im') ||
                    t.url.includes('manus.ai') ||
                    t.url.includes('manus') ||
                    t.url.includes('chatgpt.com') || 
                    t.url.includes('openai.com') || 
                    t.url.includes('claude.ai') || 
                    t.url.includes('midjourney.com') ||
                    (t.url.includes('google.') && !t.url.includes('sair.quanxs.com'))
                )
            ).map(t => {
                let domainName = 'Target AI';
                const u = t.url;
                if (u.includes('labs.google') || u.includes('flow')) domainName = 'Google Flow';
                else if (u.includes('jules')) domainName = 'Google Jules';
                else if (u.includes('gemini')) domainName = 'Gemini AI';
                else if (u.includes('manus')) domainName = 'Manus AI';
                else if (u.includes('chatgpt') || u.includes('openai')) domainName = 'ChatGPT';
                else if (u.includes('claude')) domainName = 'Claude AI';
                else if (u.includes('midjourney')) domainName = 'Midjourney';

                return {
                    id: t.id,
                    title: t.title || t.url,
                    url: t.url,
                    domain: domainName
                };
            });

            sendResponse({ success: true, tabs: detectedTabs });
        });
        return true;
    }

    if (request.action === 'SAIR_INJECT_PAYLOAD') {
        const { specText, imageBase64, targetTabId } = request;
        
        chrome.tabs.query({ currentWindow: true }, (tabs) => {
            let activeTargetTab = null;

            if (targetTabId && targetTabId !== 'none' && targetTabId !== 'auto') {
                activeTargetTab = tabs.find(t => t.id === parseInt(targetTabId, 10));
            }

            if (!activeTargetTab) {
                const flowTab = tabs.find(t => t.url && (t.url.includes('labs.google/fx') || t.url.includes('flow')));
                const julesTab = tabs.find(t => t.url && t.url.includes('jules'));
                const geminiTab = tabs.find(t => t.url && (t.url.includes('gemini.google.com') || t.url.includes('gemini')));
                const manusTab = tabs.find(t => t.url && (t.url.includes('manus.im') || t.url.includes('manus')));
                const chatGptTab = tabs.find(t => t.url && (t.url.includes('chatgpt.com') || t.url.includes('openai.com')));
                const claudeTab = tabs.find(t => t.url && t.url.includes('claude.ai'));
                const midjourneyTab = tabs.find(t => t.url && t.url.includes('midjourney.com'));

                activeTargetTab = flowTab || julesTab || geminiTab || manusTab || chatGptTab || claudeTab || midjourneyTab;
            }

            if (!activeTargetTab) {
                sendResponse({ success: false, error: '타겟 AI 탭(Google Flow/Jules/Gemini/Manus/ChatGPT/Claude)을 찾을 수 없습니다. 타겟 탭이 열려있는지 확인해 주세요!' });
                return;
            }

            // 1,000ms Debounce Lock per target tab ID
            const now = Date.now();
            if (lastTabInjectTimes[activeTargetTab.id] && (now - lastTabInjectTimes[activeTargetTab.id] < 1000)) {
                console.log(`[SAIR Background] Suppressed duplicate tab injection for Tab #${activeTargetTab.id} within 1000ms`);
                sendResponse({ success: true, tabTitle: activeTargetTab.title, textInjected: true, imageInjected: true });
                return;
            }
            lastTabInjectTimes[activeTargetTab.id] = now;

            // Auto-focus & activate target tab for instant DOM event execution
            try {
                chrome.tabs.update(activeTargetTab.id, { active: true });
            } catch(e) {}

            chrome.tabs.sendMessage(activeTargetTab.id, {
                action: 'EXECUTE_AUTO_INJECT',
                specText: specText,
                imageBase64: imageBase64
            }, (response) => {
                const err = chrome.runtime.lastError;
                if (err) {
                    sendResponse({ success: false, error: `타겟 탭[${activeTargetTab.title}]에 익스텐션 연결이 필요합니다. 해당 타겟 탭을 F5(새로고침) 해 주세요!` });
                } else {
                    sendResponse({ 
                        success: true, 
                        tabTitle: activeTargetTab.title,
                        textInjected: response?.textInjected || false,
                        imageInjected: response?.imageInjected || false
                    });
                }
            });
        });
        return true; // Keep response channel open async
    }
});
