// ===== Keyword Cache =====
let keywordCache = [];

async function refreshKeywordCache() {
    try {
        const res = await fetch('/api/keywords?q=');
        const data = await res.json();
        keywordCache = data.keywords || [];
    } catch (e) { /* silent */ }
}

// ===== Autocomplete =====
let selectedSuggestionIndex = -1;

function setupAutocomplete() {
    const input = document.getElementById('todo-input');
    const list = document.getElementById('autocomplete-list');
    if (!input || !list) return;

    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => filterSuggestions(input, list), 150);
    });

    input.addEventListener('keydown', (e) => {
        const items = list.querySelectorAll('.autocomplete-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, items.length - 1);
            updateActiveSuggestion(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
            updateActiveSuggestion(items);
        } else if (e.key === 'Enter' && selectedSuggestionIndex >= 0) {
            e.preventDefault();
            items[selectedSuggestionIndex]?.click();
        } else if (e.key === 'Escape') {
            list.classList.add('hidden');
            selectedSuggestionIndex = -1;
        }
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !list.contains(e.target)) {
            list.classList.add('hidden');
            selectedSuggestionIndex = -1;
        }
    });
}

function filterSuggestions(input, list) {
    const text = input.value;
    const parts = text.split(/\s+/);
    const partial = parts[parts.length - 1] || '';

    if (partial.length < 1) {
        list.classList.add('hidden');
        selectedSuggestionIndex = -1;
        return;
    }

    const matches = keywordCache
        .filter(kw => kw.startsWith(partial.toLowerCase()) && kw !== partial.toLowerCase())
        .slice(0, 8);

    if (matches.length === 0) {
        list.classList.add('hidden');
        selectedSuggestionIndex = -1;
        return;
    }

    list.innerHTML = matches.map(kw =>
        `<li class="autocomplete-item" data-keyword="${kw}">${kw}</li>`
    ).join('');
    list.classList.remove('hidden');
    selectedSuggestionIndex = -1;

    list.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            const kw = item.dataset.keyword;
            parts[parts.length - 1] = kw;
            input.value = parts.join(' ');
            list.classList.add('hidden');
            input.focus();
        });
    });
}

function updateActiveSuggestion(items) {
    items.forEach((item, i) => {
        item.classList.toggle('active', i === selectedSuggestionIndex);
    });
}

// ===== Todo CRUD =====

async function addTodo() {
    const input = document.getElementById('todo-input');
    const title = input.value.trim();
    if (!title) { showToast('请输入待办内容'); return; }

    try {
        const res = await fetch('/api/todos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title }),
        });
        if (res.status === 401) { window.location.href = '/login'; return; }
        if (!res.ok) { const err = await res.json(); showToast(err.error); return; }
        const data = await res.json();
        prependTodo(data.todo);
        input.value = '';
        input.focus();
        document.getElementById('autocomplete-list').classList.add('hidden');
        refreshKeywordCache();
        checkEmptyState();
    } catch (e) { showToast('网络错误，请重试'); }
}

function prependTodo(todo) {
    const list = document.getElementById('todo-list');
    // Remove empty state if present
    const empty = document.querySelector('.empty-state');
    if (empty) empty.remove();
    // Create list if needed
    if (!list) {
        const section = document.querySelector('.todo-list-section');
        const ul = document.createElement('ul');
        ul.id = 'todo-list';
        section.appendChild(ul);
    }
    const el = createTodoElement(todo);
    document.getElementById('todo-list').prepend(el);
}

function createTodoElement(todo) {
    const li = document.createElement('li');
    li.className = `todo-item ${todo.is_completed ? 'completed' : ''}`;
    li.dataset.id = todo.id;
    li.innerHTML = `
        <input type="checkbox" class="todo-checkbox" ${todo.is_completed ? 'checked' : ''}
               onchange="toggleComplete(${todo.id}, this)">
        <div class="todo-body">
            <span class="todo-title">${escapeHtml(todo.title)}</span>
            <span class="todo-meta">
                创建: ${formatTime(todo.created_at)}
                ${todo.completed_at ? ` · 完成: ${formatTime(todo.completed_at)}` : ''}
            </span>
        </div>
        <button class="todo-delete" onclick="deleteTodo(${todo.id}, this.closest('.todo-item'))">✕</button>
    `;
    return li;
}

async function toggleComplete(id, checkbox) {
    const isCompleted = checkbox.checked;
    try {
        const res = await fetch(`/api/todos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_completed: isCompleted }),
        });
        if (res.status === 401) { window.location.href = '/login'; return; }
        if (!res.ok) { checkbox.checked = !isCompleted; showToast('操作失败'); return; }
        const data = await res.json();
        const item = document.querySelector(`.todo-item[data-id="${id}"]`);
        if (item) {
            item.className = `todo-item ${data.todo.is_completed ? 'completed' : ''}`;
            const meta = item.querySelector('.todo-meta');
            const created = formatTime(data.todo.created_at);
            const completed = data.todo.completed_at ? ` · 完成: ${formatTime(data.todo.completed_at)}` : '';
            meta.textContent = `创建: ${created}${completed}`;
        }
    } catch (e) { checkbox.checked = !isCompleted; showToast('网络错误'); }
}

async function deleteTodo(id, el) {
    if (!confirm('确定删除这个待办？')) return;
    try {
        const res = await fetch(`/api/todos/${id}`, { method: 'DELETE' });
        if (res.status === 401) { window.location.href = '/login'; return; }
        if (!res.ok) { showToast('删除失败'); return; }
        el.classList.add('removing');
        setTimeout(() => {
            el.remove();
            checkEmptyState();
            // Also remove from unfinished list if present
            const ufItem = document.querySelector(`.unfinished-list .todo-item[data-id="${id}"]`);
            if (ufItem) ufItem.remove();
        }, 200);
    } catch (e) { showToast('网络错误'); }
}

function checkEmptyState() {
    const list = document.getElementById('todo-list');
    if (list && list.children.length === 0) {
        const section = document.querySelector('.todo-list-section');
        section.innerHTML = '<div class="empty-state"><p>🎉 全部搞定！添加新的待办吧。</p></div>';
    }
}

// ===== Unfinished Toggle =====
function toggleUnfinished() {
    document.getElementById('unfinished-section').classList.toggle('collapsed');
}

// ===== Helpers =====
function formatTime(isoStr) {
    if (!isoStr) return '';
    const d = isoStr.replace('T', ' ').substring(0, 16);
    return d;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showToast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

// ===== Enter key for add =====
document.addEventListener('DOMContentLoaded', () => {
    setupAutocomplete();
    refreshKeywordCache();

    const input = document.getElementById('todo-input');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const list = document.getElementById('autocomplete-list');
                if (list && !list.classList.contains('hidden') && selectedSuggestionIndex >= 0) {
                    // handled by autocomplete keydown
                    return;
                }
                e.preventDefault();
                addTodo();
            }
        });
    }
});
