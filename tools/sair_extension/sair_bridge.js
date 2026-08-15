// SAIR Cockpit Bridge Script (sair_bridge.js)
console.log("⚡ SAIR Cockpit Extension Bridge loaded!");

document.documentElement.setAttribute('data-sair-ext', 'active');
window.__SAIR_EXTENSION_ACTIVE__ = true;
window.__SAIR_EXT__ = true;

let lastInjectTime = 0;

window.addEventListener('message', (event) => {
    if (!event.data) return;

    if (event.data.type === 'SAIR_TRIGGER_SCAN_TABS') {
        try {
            if (typeof chrome !== 'undefined' && chrome && chrome.runtime && typeof chrome.runtime.sendMessage === 'function') {
                chrome.runtime.sendMessage({ action: 'SAIR_SCAN_TARGET_TABS' }, (response) => {
                    const err = chrome.runtime.lastError;
                    if (!err && response && response.success) {
                        window.postMessage({ type: 'SAIR_SCAN_TABS_RESULT', success: true, tabs: response.tabs }, '*');
                    } else {
                        window.postMessage({ type: 'SAIR_SCAN_TABS_RESULT', success: false, tabs: [] }, '*');
                    }
                });
            } else {
                window.postMessage({ type: 'SAIR_SCAN_TABS_RESULT', success: false, tabs: [] }, '*');
            }
        } catch(e) {
            window.postMessage({ type: 'SAIR_SCAN_TABS_RESULT', success: false, tabs: [] }, '*');
        }
    }

    if (event.data.type === 'SAIR_TRIGGER_AUTO_INJECT') {
        const now = Date.now();
        if (now - lastInjectTime < 1000) {
            console.log("⚡ [SAIR Bridge] Suppressed duplicate postMessage trigger within 1000ms!");
            return;
        }
        lastInjectTime = now;

        const { specText, imageBase64, targetTabId } = event.data;

        // Guaranteed OS Clipboard Population on User Click Event
        if (specText && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
            try {
                navigator.clipboard.writeText(specText).then(() => {
                    console.log("⚡ [SAIR Bridge] OS Clipboard populated with prompt specification!");
                }).catch(() => {});
            } catch(e) {}
        }
        
        try {
            if (typeof chrome !== 'undefined' && chrome && chrome.runtime && typeof chrome.runtime.sendMessage === 'function') {
                chrome.runtime.sendMessage({
                    action: 'SAIR_INJECT_PAYLOAD',
                    specText: specText,
                    imageBase64: imageBase64,
                    targetTabId: targetTabId
                }, (response) => {
                    const err = chrome.runtime.lastError;
                    if (err) {
                        window.postMessage({ type: 'SAIR_AUTO_INJECT_RESULT', success: false, error: '익스텐션 백그라운드 연결이 초기화되었습니다. SAIR 탭을 F5(새로고침) 해 주세요.' }, '*');
                    } else if (response && response.success) {
                        window.postMessage({ type: 'SAIR_AUTO_INJECT_RESULT', success: true, tabTitle: response.tabTitle }, '*');
                    } else {
                        window.postMessage({ type: 'SAIR_AUTO_INJECT_RESULT', success: false, error: response?.error || 'Target tab not found' }, '*');
                    }
                });
            } else {
                window.postMessage({ type: 'SAIR_AUTO_INJECT_RESULT', success: false, error: '크롬 익스텐션 컨텍스트가 비활성화되었습니다. SAIR 탭을 F5(새로고침) 해 주세요!' }, '*');
            }
        } catch(e) {
            console.warn("[SAIR Bridge Error Handled]:", e);
            window.postMessage({ type: 'SAIR_AUTO_INJECT_RESULT', success: false, error: '익스텐션 연결 예외 발생. SAIR 탭을 F5(새로고침) 해 주세요!' }, '*');
        }
    }
});
