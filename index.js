document.addEventListener('DOMContentLoaded', () => {
    const STATIC_CONFIG_URL = './all_live_configs.json?t=' + Date.now();
    const STATIC_CACHE_VERSION_URL = './cache_version.txt?t=' + Date.now();
    
    const WORKER_URLS = [
        'https://v2v-proxy.mbrgh87.workers.dev',
        'https://v2v.mbrgh87.workers.dev',
        'https://rapid-scene-1da6.mbrgh87.workers.dev',
        'https://winter-hill-0307.mbrgh87.workers.dev',
    ];
    
    const getEl = (id) => document.getElementById(id);
    const statusBar = getEl('status-bar');
    const xrayWrapper = getEl('xray-content-wrapper');
    const singboxWrapper = getEl('singbox-content-wrapper');
    const qrModal = getEl('qr-modal');
    const qrContainer = getEl('qr-code-container');
    const toastEl = getEl('toast');

    const showToast = (message, isError = false) => {
        toastEl.textContent = message;
        toastEl.className = `toast show ${isError ? 'error' : ''}`;
        setTimeout(() => toastEl.classList.remove('show'), 3000);
    };

    window.copyToClipboard = async (text, successMessage = 'کپی شد!') => {
        try {
            await navigator.clipboard.writeText(text);
            showToast(successMessage);
        } catch (err) { 
            showToast('خطا در کپی کردن!', true); 
        }
    };

    window.openQrModal = (text) => {
        if (!window.QRCode) { 
            showToast('کتابخانه QR در حال بارگذاری است...', true); 
            return; 
        }
        qrContainer.innerHTML = '';
        new QRCode(qrContainer, { 
            text, 
            width: 256, 
            height: 256, 
            correctLevel: QRCode.CorrectLevel.H 
        });
        qrModal.style.display = 'flex';
    };

    qrModal.addEventListener('click', (e) => {
        if (e.target === qrModal) {
            qrModal.style.display = 'none';
        }
    });

    let allLiveConfigsData = null;
    let realPingResults = {};

    const getConfigHash = (config) => {
        try {
            const url = new URL(config);
            return `${url.protocol}//${url.hostname}:${url.port}:${url.username}`;
        } catch {
            return config;
        }
    };

    const removeDuplicates = (configs) => {
        const seen = new Set();
        return configs.filter(config => {
            const hash = getConfigHash(config);
            if (seen.has(hash)) return false;
            seen.add(hash);
            return true;
        });
    };

    const shortenName = (name, protocol, server) => {
        if (!name || name.length > 25) {
            return `${protocol}-${server.substring(0, 12)}`;
        }
        return name;
    };

    window.copyProtocolConfigs = (coreName, protocol) => {
        const coreData = allLiveConfigsData[coreName];
        if (!coreData || !coreData[protocol] || coreData[protocol].length === 0) {
            showToast('کانفیگی یافت نشد!', true);
            return;
        }
        const configs = coreData[protocol].join('\n');
        window.copyToClipboard(configs, `${coreData[protocol].length} کانفیگ ${protocol.toUpperCase()} کپی شد!`);
    };

    window.selectAllProtocol = (coreName, protocol) => {
        const checkboxes = document.querySelectorAll(`input.config-checkbox[data-core="${coreName}"][data-protocol="${protocol}"]`);
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
        });
        showToast(allChecked ? 'انتخاب همه لغو شد' : 'همه انتخاب شدند');
    };

    window.generateSubscription = async (coreName, scope, format, action) => {
        let configs = [];
        if (scope === 'selected') {
            const checkboxes = document.querySelectorAll(`input.config-checkbox[data-core="${coreName}"]:checked`);
            if (checkboxes.length === 0) {
                showToast('هیچ کانفیگی انتخاب نشده!', true);
                return;
            }
            configs = Array.from(checkboxes).map(cb => decodeURIComponent(cb.dataset.config));
        } else if (scope === 'auto') {
            configs = getTopConfigsFromBackend(coreName);
            if (configs.length === 0) {
                showToast('کانفیگی یافت نشد!', true);
                return;
            }
        }
        configs = removeDuplicates(configs);
        if (configs.length === 0) {
            showToast('کانفیگی یافت نشد!', true);
            return;
        }
        
        showToast(`در حال ساخت ${format}...`);
        
        const createPromises = WORKER_URLS.map(async (workerUrl, index) => {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000);
                const response = await fetch(`${workerUrl}/create-sub`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ configs, format }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (response.ok) {
                    const data = await response.json();
                    if (data.url) {
                        return { success: true, url: data.url, workerIndex: index + 1 };
                    }
                }
            } catch (error) {
                console.error(`Worker ${index + 1} failed:`, error);
            }
            return { success: false };
        });
        
        try {
            const firstSuccess = await Promise.race(
                createPromises.map(p => p.then(result => result.success ? result : Promise.reject(result)))
            ).catch(() => null);
            
            if (firstSuccess) {
                if (action === 'copy') {
                    await window.copyToClipboard(firstSuccess.url, `✅ لینک ${format} کپی شد! (Worker ${firstSuccess.workerIndex})`);
                } else if (action === 'qr') {
                    window.openQrModal(firstSuccess.url);
                    showToast(`✅ QR ${format} ساخته شد!`);
                }
                return;
            }
            
            const allResults = await Promise.all(createPromises);
            const successResult = allResults.find(r => r.success);
            
            if (successResult) {
                if (action === 'copy') {
                    await window.copyToClipboard(successResult.url, `✅ لینک ${format} کپی شد!`);
                } else if (action === 'qr') {
                    window.openQrModal(successResult.url);
                    showToast(`✅ QR ${format} ساخته شد!`);
                }
                return;
            }
            
            throw new Error('All workers failed');
        } catch (error) {
            console.error('Subscription creation failed:', error);
            showToast(`❌ خطا در ساخت ${format}!`, true);
        }
    };

    const getTopConfigsFromBackend = (coreName) => {
        const coreData = allLiveConfigsData[coreName];
        const allConfigs = [];
        for (const protocol in coreData) {
            coreData[protocol].forEach((config, idx) => {
                const key = `${coreName}-${protocol}-${idx}`;
                const ping = realPingResults[key];
                if (ping && ping > 0 && ping < 500) {
                    allConfigs.push({ config, ping });
                }
            });
        }
        if (allConfigs.length === 0) {
            for (const protocol in coreData) {
                allConfigs.push(...coreData[protocol].slice(0, 5).map(config => ({ config, ping: 9999 })));
            }
        }
        allConfigs.sort((a, b) => a.ping - b.ping);
        return removeDuplicates(allConfigs.slice(0, 20).map(item => item.config));
    };

    const fetchAndRender = async () => {
        console.log('🚀 Starting V2V Client...');
        statusBar.textContent = 'بارگذاری...';
        try {
            console.log('📥 Fetching configs from:', STATIC_CONFIG_URL);
            const configResponse = await fetch(STATIC_CONFIG_URL, { 
                cache: 'no-store',
                headers: { 'Accept': 'application/json' }
            });
            if (!configResponse.ok) {
                throw new Error(`HTTP ${configResponse.status}: ${configResponse.statusText}`);
            }
            const responseText = await configResponse.text();
            console.log('📦 Response length:', responseText.length);
            allLiveConfigsData = JSON.parse(responseText);
            console.log('✅ Parsed JSON successfully');
            if (!allLiveConfigsData.xray || !allLiveConfigsData.singbox) {
                throw new Error('Invalid data structure');
            }
            for (const core in allLiveConfigsData) {
                for (const protocol in allLiveConfigsData[core]) {
                    const before = allLiveConfigsData[core][protocol].length;
                    allLiveConfigsData[core][protocol] = removeDuplicates(allLiveConfigsData[core][protocol]);
                    const after = allLiveConfigsData[core][protocol].length;
                    if (before !== after) {
                        console.log(`🧹 Removed ${before - after} duplicates from ${core}/${protocol}`);
                    }
                }
            }
            let cacheVersion = 'نامشخص';
            try {
                const versionResponse = await fetch(STATIC_CACHE_VERSION_URL, { cache: 'no-store' });
                if (versionResponse.ok) {
                    cacheVersion = await versionResponse.text();
                }
            } catch (e) {
                console.warn('Cache version fetch failed:', e);
            }
            const updateTime = new Date(parseInt(cacheVersion) * 1000).toLocaleString('fa-IR', { 
                dateStyle: 'short', 
                timeStyle: 'short' 
            });
            statusBar.textContent = `آخرین بروزرسانی: ${updateTime}`;
            console.log('🎨 Rendering cores...');
            renderCore('xray', allLiveConfigsData.xray, xrayWrapper);
            renderCore('singbox', allLiveConfigsData.singbox, singboxWrapper);
            const xrayTotal = Object.values(allLiveConfigsData.xray).reduce((sum, arr) => sum + arr.length, 0);
            const singboxTotal = Object.values(allLiveConfigsData.singbox).reduce((sum, arr) => sum + arr.length, 0);
            console.log(`📊 Stats: Xray=${xrayTotal}, Singbox=${singboxTotal}, Total=${xrayTotal + singboxTotal}`);
            console.log('✅ V2V loaded successfully!');
        } catch (error) {
            console.error('❌ Fatal error:', error);
            statusBar.textContent = 'خطا در بارگذاری';
            xrayWrapper.innerHTML = `<div class="alert">❌ خطا: ${error.message}<br><small>لطفاً صفحه را رفرش کنید</small></div>`;
            singboxWrapper.innerHTML = `<div class="alert">❌ خطا: ${error.message}<br><small>لطفاً صفحه را رفرش کنید</small></div>`;
            showToast('خطا در دریافت کانفیگ‌ها!', true);
        }
    };

    const renderCore = (coreName, coreData, wrapper) => {
        if (!coreData || Object.keys(coreData).length === 0) {
            wrapper.innerHTML = `<div class="alert">کانفیگی یافت نشد.</div>`;
            return;
        }
        const totalConfigs = Object.values(coreData).reduce((sum, arr) => sum + arr.length, 0);
        const realTestButton = `<button class="test-button" style="background: linear-gradient(135deg, #c31432, #240b36); margin-bottom: 15px;" onclick="window.startRealPingTest('${coreName}')" id="real-test-${coreName}-btn">🌐 تست از شبکه شما (${totalConfigs} کانفیگ)</button>`;
        const copySelectedButton = `<button class="action-btn-wide" onclick="window.copySelectedConfigs('${coreName}')">📋 کپی موارد انتخابی</button>`;
        let contentHtml = `<div class="action-bar">${realTestButton}${copySelectedButton}</div>`;
        if (coreName === 'xray') {
            contentHtml += `<div class="sub-section"><div class="sub-title">🔷 Xray Subscription (خام)</div><div class="sub-actions"><button class="sub-btn" onclick="window.generateSubscription('${coreName}', 'selected', 'xray', 'copy')">انتخابی</button><button class="sub-btn primary" onclick="window.generateSubscription('${coreName}', 'auto', 'xray', 'copy')">خودکار (بهترین‌ها)</button><button class="sub-btn qr" onclick="window.generateSubscription('${coreName}', 'auto', 'xray', 'qr')">📱 QR</button></div></div><div class="sub-section"><div class="sub-title">⚡ Clash for Xray</div><div class="sub-actions"><button class="sub-btn" onclick="window.generateSubscription('${coreName}', 'selected', 'xray-clash', 'copy')">انتخابی</button><button class="sub-btn primary" onclick="window.generateSubscription('${coreName}', 'auto', 'xray-clash', 'copy')">خودکار (بهترین‌ها)</button><button class="sub-btn qr" onclick="window.generateSubscription('${coreName}', 'auto', 'xray-clash', 'qr')">📱 QR</button></div></div>`;
        } else if (coreName === 'singbox') {
            contentHtml += `<div class="sub-section"><div class="sub-title">📦 Singbox Subscription</div><div class="sub-actions"><button class="sub-btn" onclick="window.generateSubscription('${coreName}', 'selected', 'singbox', 'copy')">انتخابی</button><button class="sub-btn primary" onclick="window.generateSubscription('${coreName}', 'auto', 'singbox', 'copy')">خودکار (بهترین‌ها)</button><button class="sub-btn qr" onclick="window.generateSubscription('${coreName}', 'auto', 'singbox', 'qr')">📱 QR</button></div></div><div class="sub-section"><div class="sub-title">⚡ Clash for Singbox</div><div class="sub-actions"><button class="sub-btn" onclick="window.generateSubscription('${coreName}', 'selected', 'singbox-clash', 'copy')">انتخابی</button><button class="sub-btn primary" onclick="window.generateSubscription('${coreName}', 'auto', 'singbox-clash', 'copy')">خودکار (بهترین‌ها)</button><button class="sub-btn qr" onclick="window.generateSubscription('${coreName}', 'auto', 'singbox-clash', 'qr')">📱 QR</button></div></div>`;
        }
        for (const protocol in coreData) {
            const configs = coreData[protocol];
            if (configs.length === 0) continue;
            const protocolMap = {'vmess': 'VMess', 'vless': 'VLESS', 'trojan': 'Trojan', 'ss': 'Shadowsocks', 'hy2': 'Hysteria2', 'tuic': 'TUIC'};
            const protocolName = protocolMap[protocol] || protocol.toUpperCase();
            contentHtml += `<div class="protocol-group" data-protocol="${protocol}"><div class="protocol-header"><span class="protocol-name">${protocolName} <span class="badge">${configs.length}</span></span><div class="protocol-actions"><button class="btn-copy-protocol" onclick="window.selectAllProtocol('${coreName}', '${protocol}')" title="انتخاب همه">☑️</button><button class="btn-copy-protocol" onclick="window.copyProtocolConfigs('${coreName}', '${protocol}')" title="کپی همه">📋</button><svg class="toggle-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></div></div><ul class="config-list">`;
            configs.forEach((config, idx) => {
                try {
                    const urlObj = new URL(config);
                    const server = urlObj.hostname;
                    const port = urlObj.port;
                    const rawName = decodeURIComponent(urlObj.hash.substring(1) || `${protocol}-${server}`);
                    const name = shortenName(rawName, protocol, server);
                    contentHtml += `<li class="config-item" data-config-key="${coreName}-${protocol}-${idx}"><input type="checkbox" class="config-checkbox" data-core="${coreName}" data-protocol="${protocol}" data-config="${encodeURIComponent(config)}" id="${coreName}-${protocol}-${idx}"><div class="config-info"><label for="${coreName}-${protocol}-${idx}" class="config-name">${name}</label><span class="server">${server}:${port}</span></div><span class="ping-result" id="ping-${coreName}-${protocol}-${idx}"></span><div class="config-btns"><button class="btn-icon" onclick="window.copyToClipboard(decodeURIComponent('${encodeURIComponent(config)}'))" title="کپی">📋</button><button class="btn-icon" onclick="window.openQrModal(decodeURIComponent('${encodeURIComponent(config)}'))" title="QR">📱</button></div></li>`;
                } catch (e) {
                    console.warn('Config parse error:', e);
                }
            });
            contentHtml += `</ul></div>`;
        }
        wrapper.innerHTML = contentHtml;
        wrapper.querySelectorAll('.protocol-header').forEach(header => {
            header.addEventListener('click', (e) => {
                if (!e.target.classList.contains('btn-copy-protocol') && !e.target.closest('.btn-copy-protocol')) {
                    header.closest('.protocol-group').classList.toggle('open');
                }
            });
        });
    };

    window.copySelectedConfigs = (coreName) => {
        const checkboxes = document.querySelectorAll(`input.config-checkbox[data-core="${coreName}"]:checked`);
        if (checkboxes.length === 0) {
            showToast('هیچ کانفیگی انتخاب نشده!', true);
            return;
        }
        const configs = Array.from(checkboxes).map(cb => decodeURIComponent(cb.dataset.config));
        window.copyToClipboard(configs.join('\n'), `${configs.length} کانفیگ کپی شد!`);
    };

    async function tcpPingReal(server, port, protocol, attempts = 2) {
        const latencies = [];
        let useHttps = false;
        const httpsProtocols = ['vless', 'vmess', 'trojan', 'tuic', 'hy2'];
        const httpsPorts = ['443', '8443', '2096', '2053', '2083', '2087', '2052', '2082', '8880'];
        if (httpsProtocols.includes(protocol) || httpsPorts.includes(port)) {
            useHttps = true;
        }
        const connectionProtocol = useHttps ? 'https' : 'http';
        for (let i = 0; i < attempts; i++) {
            try {
                const start = performance.now();
                await new Promise((resolve, reject) => {
                    const img = new Image();
                    const timeout = setTimeout(() => {
                        img.src = '';
                        reject(new Error('timeout'));
                    }, 4000);
                    img.onload = img.onerror = () => {
                        clearTimeout(timeout);
                        resolve();
                    };
                    img.src = `${connectionProtocol}://${server}:${port}/favicon.ico?_=${Date.now()}_${i}`;
                });
                const latency = Math.round(performance.now() - start);
                if (latency < 4000) {
                    latencies.push(latency);
                }
            } catch {}
            if (i < attempts - 1 && latencies.length === 0) {
                await new Promise(r => setTimeout(r, 150));
            }
        }
        if (latencies.length === 0) {
            return { status: 'Dead', latency: null };
        }
        const avg = Math.round(latencies.reduce((a, b) => a + b) / latencies.length);
        return {
            status: 'Live',
            latency: avg,
            min: Math.min(...latencies),
            max: Math.max(...latencies)
        };
    }

    window.startRealPingTest = async (coreName) => {
        const btn = getEl(`real-test-${coreName}-btn`);
        if (!btn) return;
        const confirmTest = confirm(`🌐 تست واقعی از شبکه شما\n\nاین تست مستقیماً از اینترنت شما در ایران انجام میشه.\n\n✅ همه پروتکل‌ها پشتیبانی میشن: VMess, VLESS, Trojan, SS, Hy2, TUIC\n⚡ سرعت بالا با تست موازی 50 کانفیگ همزمان\n⏱️ زمان تقریبی: 2-4 دقیقه\n\nادامه میدی؟`);
        if (!confirmTest) return;
        btn.disabled = true;
        btn.innerHTML = `<span class="loader-small"></span> در حال تست...`;
        realPingResults = {};
        const coreData = allLiveConfigsData[coreName];
        const allConfigs = [];
        for (const protocol in coreData) {
            coreData[protocol].forEach((config, idx) => {
                try {
                    const urlObj = new URL(config);
                    allConfigs.push({ config, protocol, idx, server: urlObj.hostname, port: urlObj.port || '443' });
                } catch {}
            });
        }
        let completed = 0;
        const total = allConfigs.length;
        let liveCount = 0;
        let deadCount = 0;
        showToast(`شروع تست ${total} کانفیگ...`);
        const BATCH_SIZE = 50;
        const startTime = Date.now();
        for (let i = 0; i < allConfigs.length; i += BATCH_SIZE) {
            const batch = allConfigs.slice(i, i + BATCH_SIZE);
            await Promise.all(batch.map(async (item) => {
                const { config, protocol, idx, server, port } = item;
                const resultEl = getEl(`ping-${coreName}-${protocol}-${idx}`);
                if (!resultEl) return;
                resultEl.innerHTML = '<span class="loader-mini"></span>';
                const result = await tcpPingReal(server, port, protocol, 2);
                if (result.status === 'Live') {
                    const color = result.latency < 200 ? '#4CAF50' : result.latency < 500 ? '#FFC107' : '#F44336';
                    resultEl.innerHTML = `<span style="color: ${color}; font-weight: bold;" title="تست واقعی: ${result.min}-${result.max}ms">${result.latency}ms</span>`;
                    realPingResults[`${coreName}-${protocol}-${idx}`] = result.latency;
                    liveCount++;
                } else {
                    resultEl.innerHTML = '<span style="color: #F44336;" title="غیرقابل دسترس">✗</span>';
                    realPingResults[`${coreName}-${protocol}-${idx}`] = 9999;
                    deadCount++;
                }
                completed++;
                const progress = Math.round((completed / total) * 100);
                const elapsed = Math.round((Date.now() - startTime) / 1000);
                btn.textContent = `تست ${progress}% (${completed}/${total}) - ${elapsed}s`;
            }));
        }
        const totalTime = Math.round((Date.now() - startTime) / 1000);
        btn.disabled = false;
        btn.innerHTML = `🌐 تست واقعی از شبکه شما (${total} کانفیگ)`;
        showToast(`✅ تست ${totalTime}s - زنده: ${liveCount} | مرده: ${deadCount}`);
        sortConfigsByRealPing(coreName);
        if (liveCount > 0) {
            setTimeout(() => {
                const createSub = confirm(`✅ تست تکمیل شد در ${totalTime} ثانیه!\n\n${liveCount} کانفیگ از ${total} از شبکه شما قابل دسترسی هستند.\n\nساب لینک از بهترین‌ها بسازیم؟`);
                if (createSub) {
                    const format = coreName === 'xray' ? 'xray' : 'singbox';
                    window.generateSubscription(coreName, 'auto', format, 'copy');
                }
            }, 1500);
        }
    };

    function sortConfigsByRealPing(coreName) {
        const wrapper = coreName === 'xray' ? xrayWrapper : singboxWrapper;
        const protocolGroups = wrapper.querySelectorAll('.protocol-group');
        protocolGroups.forEach(group => {
            const configList = group.querySelector('.config-list');
            if (!configList) return;
            const items = Array.from(configList.querySelectorAll('.config-item'));
            items.sort((a, b) => {
                const keyA = a.dataset.configKey;
                const keyB = b.dataset.configKey;
                const pingA = realPingResults[keyA] || 9999;
                const pingB = realPingResults[keyB] || 9999;
                return pingA - pingB;
            });
            items.forEach(item => configList.appendChild(item));
        });
        console.log(`📊 ${coreName} sorted by real ping`);
    }

    fetchAndRender();
});

