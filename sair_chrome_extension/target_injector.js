// SAIR Target AI Site DOM Injector Script (target_injector.js v1.2.8 Zero-DOM-Mutation Paste Engine)
console.log("⚡ SAIR Universal Target Injector Active on: " + window.location.href);

if (window === window.top) {
    let injectionLock = false;

    // Zero-CSP Pure In-Memory Base64 Data URI to Blob Conversion
    const dataURItoBlob = (dataURI) => {
        try {
            const parts = dataURI.split(',');
            const byteString = atob(parts[1] || parts[0]);
            const mimeMatch = parts[0].match(/:(.*?);/);
            const mimeString = mimeMatch ? mimeMatch[1] : 'image/png';

            const ab = new ArrayBuffer(byteString.length);
            const ia = new Uint8Array(ab);
            for (let i = 0; i < byteString.length; i++) {
                ia[i] = byteString.charCodeAt(i);
            }
            return new Blob([ab], { type: mimeString });
        } catch(e) {
            console.error("[SAIR Injector] dataURItoBlob conversion error:", e);
            return null;
        }
    };

    // Deep Shadow DOM Query Selector for Web Components & Shadow Roots
    const findDeepElement = (selector, root = document, requireVisible = true) => {
        try {
            let el = root.querySelector(selector);
            if (el && (!requireVisible || (el.offsetWidth || el.offsetHeight || el.getClientRects().length))) {
                return el;
            }

            const allNodes = root.querySelectorAll('*');
            for (const node of allNodes) {
                if (node.shadowRoot) {
                    const found = findDeepElement(selector, node.shadowRoot, requireVisible);
                    if (found) return found;
                }
            }
        } catch(e) {}
        return null;
    };

    // Find ALL Deep Matching Elements
    const findAllDeepElements = (selector, root = document, requireVisible = true) => {
        let results = [];
        try {
            const nodes = Array.from(root.querySelectorAll(selector)).filter(el => 
                !requireVisible || (el.offsetWidth || el.offsetHeight || el.getClientRects().length)
            );
            results.push(...nodes);

            const allNodes = root.querySelectorAll('*');
            for (const node of allNodes) {
                if (node.shadowRoot) {
                    const sub = findAllDeepElements(selector, node.shadowRoot, requireVisible);
                    results.push(...sub);
                }
            }
        } catch(e) {}
        return results;
    };

    // 🛡️ Zero-DOM-Mutation Focus Handler (NEVER mutates/appends DOM nodes to prevent React 'removeChild' Exception)
    const focusEditorSafely = (el) => {
        try {
            if (!el || !document.contains(el)) return;
            if (window.focus) window.focus();
            el.focus();

            try {
                document.dispatchEvent(new Event('selectionchange', { bubbles: true }));
                el.dispatchEvent(new Event('focus', { bubbles: true }));
            } catch(e) {}
        } catch(e) {}
    };

    // 100% Pure Event Paste Injector for Text
    const injectTextViaPaste = (el, text) => {
        try {
            focusEditorSafely(el);

            const placeholder = el.querySelector('[data-slate-placeholder="true"]');
            if (placeholder) {
                try { placeholder.style.display = 'none'; } catch(e) {}
            }

            // Always write to native OS Clipboard first
            if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
                try { navigator.clipboard.writeText(text).catch(() => {}); } catch(e) {}
            }

            // Dispatch Pure Synthetic Paste Event (Carrying Text DataTransfer)
            const dtText = new DataTransfer();
            dtText.setData('text/plain', text);
            dtText.setData('text/html', '<p>' + text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, '<br>') + '</p>');
            
            const pasteEvt = new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: dtText });
            let handled = el.dispatchEvent(pasteEvt);

            // Fallback for native inputs
            if (!handled || (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT')) {
                try {
                    if (el._valueTracker) { try { el._valueTracker.setValue(''); } catch(e) {} }
                    const prototype = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
                    const nativeSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
                    if (nativeSetter) nativeSetter.call(el, text);
                    else el.value = text;
                } catch(e) {}
            }

            try {
                el.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
                el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: text }));
                el.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
                el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
            } catch(e) {}

            return true;
        } catch(e) {
            console.warn("[SAIR Injector] Text paste injection error:", e);
            return false;
        }
    };

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'EXECUTE_AUTO_INJECT') {
            if (injectionLock) {
                sendResponse({ success: true, warning: 'Injection in progress...' });
                return true;
            }
            injectionLock = true;

            const { specText, imageBase64 } = request;

            sendResponse({ success: true, textInjected: true, imageInjected: true });

            const executeInjection = () => {
                const textSelectors = [
                    'div[data-slate-editor="true"]',
                    '[data-slate-editor="true"]',
                    'gmp-prompt-input textarea',
                    'gmp-prompt-input div[contenteditable="true"]',
                    'gmp-prompt-input',
                    'textarea[placeholder*="무엇을"]',
                    'div[placeholder*="무엇을"]',
                    'textarea[placeholder*="만들고"]',
                    'div[placeholder*="만들고"]',
                    '#prompt-textarea',
                    'rich-textarea div[contenteditable="true"]',
                    'div[aria-label*="Prompt"]',
                    'div[aria-label*="프롬프트"]',
                    'div[aria-label*="Jules"]',
                    'textarea[aria-label*="Jules"]',
                    'textarea',
                    'div[contenteditable="true"]'
                ];

                let targetElements = [];
                for (const sel of textSelectors) {
                    const found = findAllDeepElements(sel, document, true);
                    if (found.length > 0) {
                        targetElements.push(...found);
                    }
                }

                targetElements = Array.from(new Set(targetElements));
                
                let primaryTargetEl = null;
                if (targetElements.length > 0) {
                    primaryTargetEl = targetElements.find(el => 
                        el.getAttribute('contenteditable') === 'true' || 
                        el.tagName === 'TEXTAREA' || 
                        el.hasAttribute('data-slate-editor')
                    ) || targetElements[targetElements.length - 1];
                }

                if (!primaryTargetEl) {
                    injectionLock = false;
                    return;
                }

                let domMaxLength = 99999;
                const attrMax = primaryTargetEl.getAttribute('maxlength') || primaryTargetEl.dataset?.maxlength;
                if (attrMax) domMaxLength = parseInt(attrMax, 10);

                const isLimitExceeded = specText && specText.length > domMaxLength;
                const boxText = (isLimitExceeded && domMaxLength < 99999) ? 
                    specText.substring(0, Math.max(50, domMaxLength - 30)) + "..." : 
                    specText;

                const hasImage = imageBase64 && imageBase64.startsWith('data:image');

                // STEP 1: Zero-DOM-Mutation Paste Text Injection
                if (boxText) {
                    injectTextViaPaste(primaryTargetEl, boxText);
                }

                // STEP 2: Pure Paste Image Injection (120ms Timeout)
                setTimeout(() => {
                    if (hasImage) {
                        try {
                            const imgBlob = dataURItoBlob(imageBase64);
                            if (imgBlob) {
                                const imgFile = new File([imgBlob], "sair_render_matrix.png", { type: "image/png" });
                                const dtImg = new DataTransfer();
                                dtImg.items.add(imgFile);

                                const imgPasteEvt = new ClipboardEvent('paste', { bubbles: true, cancelable: true, clipboardData: dtImg });
                                primaryTargetEl.dispatchEvent(imgPasteEvt);
                            }
                        } catch(e) {
                            console.warn("[SAIR Injector] Image paste exception:", e);
                        }
                    }

                    setTimeout(() => { injectionLock = false; }, 300);
                }, 120);
            };

            executeInjection();
            return true;
        }
    });
}
