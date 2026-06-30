// static/src/mrp_display_record_ext/js/mrp_display_record.js

console.log("🟢 [MRP] DOM 数据加载器启动");

// 获取 CSRF Token
function getCSRFToken() {
    return window.odoo?.csrf_token ||
           document.querySelector('meta[name="csrf-token"]')?.content ||
           '';
}

// 加载工序数据
async function loadOperationData(operationId) {
    console.log(`📡 加载工序数据 ID: ${operationId}`);

    const csrfToken = getCSRFToken();

    try {
        const response = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Odoo-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    model: 'mrp.routing.workcenter',
                    method: 'read',
                    args: [[parseInt(operationId)], ['miclen_work_id', 'equipment_ids', 'printing_plate', 'die_mold']],
                    kwargs: { context: {} }
                },
                id: Date.now()
            })
        });

        const result = await response.json();
        console.log(`📡 RPC 结果:`, result);

        if (result.result && result.result.length > 0) {
            const data = result.result[0];

            // 如果 equipment_ids 是 ID 数组，查询设备名称
            if (data.equipment_ids && data.equipment_ids.length > 0) {
                const equipmentNames = await loadEquipmentNames(data.equipment_ids);
                data.equipment_names = equipmentNames;
            }

            return data;
        }
        return null;
    } catch (error) {
        console.error(`❌ 加载失败:`, error);
        return null;
    }
}

// 查询设备名称
async function loadEquipmentNames(equipmentIds) {
    console.log(`📡 查询设备名称: ${equipmentIds.join(', ')}`);

    const csrfToken = getCSRFToken();

    try {
        const response = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Odoo-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    model: 'maintenance.equipment',
                    method: 'search_read',
                    args: [[['id', 'in', equipmentIds]], ['name', 'display_name']],
                    kwargs: { context: {} }
                },
                id: Date.now() + 1
            })
        });

        const result = await response.json();
        console.log(`📡 设备名称结果:`, result);

        if (result.result && result.result.length > 0) {
            // 按原顺序返回名称
            const nameMap = {};
            result.result.forEach(item => {
                nameMap[item.id] = item.display_name || item.name || item.id;
            });
            return equipmentIds.map(id => nameMap[id] || id);
        }
        return equipmentIds.map(id => id);
    } catch (error) {
        console.error(`❌ 查询设备名称失败:`, error);
        return equipmentIds.map(id => id);
    }
}

// 处理所有卡片
async function processAllCards() {
    console.log(`🟡 开始处理卡片...`);

    const cards = document.querySelectorAll('.card-footer.bg-light.p-2.border-top');
    console.log(`🔍 找到 ${cards.length} 个卡片`);

    for (const card of cards) {
        // 检查是否已处理
        if (card.dataset.mrpUpdated === 'true') {
            console.log(`  ⏭️ 卡片已处理，跳过`);
            continue;
        }

        // 从隐藏 input 中获取数据
        const workorderIdInput = card.querySelector('.mrp-workorder-id');
        const operationIdInput = card.querySelector('.mrp-operation-id');

        const workorderId = workorderIdInput?.value;
        const operationId = operationIdInput?.value;

        console.log(`  📍 workorder_id=${workorderId}, operation_id=${operationId}`);

        if (!operationId || operationId === 'undefined' || operationId === '') {
            console.log(`  ⚠️ 没有 operation_id，跳过`);
            continue;
        }

        // 加载数据
        const data = await loadOperationData(operationId);
        if (data) {
            // 更新网版
            const printingPlateEl = card.querySelector('.mrp-printing-plate');
            if (printingPlateEl) {
                printingPlateEl.textContent = data.printing_plate || '(空)';
                console.log(`  ✅ 网版: ${data.printing_plate || '(空)'}`);
            }

            // 更新刀模
            const dieMoldEl = card.querySelector('.mrp-die-mold');
            if (dieMoldEl) {
                dieMoldEl.textContent = data.die_mold || '(空)';
                console.log(`  ✅ 刀模: ${data.die_mold || '(空)'}`);
            }

            // 更新设备 - 显示名称
            const equipmentEl = card.querySelector('.mrp-equipment');
            if (equipmentEl) {
                if (data.equipment_names && data.equipment_names.length > 0) {
                    const names = data.equipment_names.join(', ');
                    equipmentEl.textContent = names;
                    console.log(`  ✅ 设备: ${names}`);
                } else {
                    equipmentEl.textContent = '(空)';
                    console.log(`  ✅ 设备: (空)`);
                }
            }

            card.dataset.mrpUpdated = 'true';
        } else {
            console.log(`  ⚠️ 卡片数据加载失败`);
            // 显示错误信息
            const printingPlateEl = card.querySelector('.mrp-printing-plate');
            if (printingPlateEl) printingPlateEl.textContent = '加载失败';

            const dieMoldEl = card.querySelector('.mrp-die-mold');
            if (dieMoldEl) dieMoldEl.textContent = '加载失败';

            const equipmentEl = card.querySelector('.mrp-equipment');
            if (equipmentEl) equipmentEl.textContent = '加载失败';
        }
    }

    console.log(`✅ 卡片处理完成`);
}

// 监听 DOM 变化
function setupObserver() {
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                // 检查是否有新的卡片
                const cards = document.querySelectorAll('.card-footer.bg-light.p-2.border-top:not([data-mrp-updated])');
                if (cards.length > 0) {
                    console.log(`🟡 发现 ${cards.length} 个新卡片`);
                    setTimeout(processAllCards, 2000);
                }
                break;
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log(`🟢 监听器已设置`);
}

// 初始化
function init() {
    console.log(`🟢 MRP 数据加载器初始化`);

    // 首次加载
    setTimeout(processAllCards, 3000);

    // 设置监听器
    setupObserver();

    // 暴露手动触发函数
    window.mrpProcessCards = processAllCards;
    console.log(`🟢 使用 window.mrpProcessCards() 手动加载`);
}

// 页面加载完成后执行
if (document.readyState === 'complete') {
    init();
} else {
    document.addEventListener('DOMContentLoaded', init);
}

console.log(`🟢 MRP 数据加载器已启动`);