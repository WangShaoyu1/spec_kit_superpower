/** Recipe / KB field keys for client-side PD preview (backend may add explicit fields later). */
export const RECIPE_VALID_KEYS = new Set([
  'name',
  'title',
  'recipe_name',
  'recipeName',
  'dish',
  '菜名',
  '菜谱名',
  '名称',
  'recipe',
  'ingredients',
  'ingredient',
  '食材',
  '原料',
  '材料',
  'steps',
  'step',
  'instructions',
  '做法',
  '步骤',
  '制作方法',
  'servings',
  '份量',
  'time',
  'duration',
  'prep_time',
  'cook_time',
  '时长',
  '描述',
  'description',
]);

export function fileBasename(path) {
  if (!path) return '';
  const parts = String(path).replace(/\\/g, '/').split('/');
  return parts[parts.length - 1] || path;
}

function splitValidInvalidFields(keys) {
  const valid = [];
  const invalid = [];
  const seen = new Set();
  for (const k of keys) {
    const nk = String(k).trim();
    if (!nk || seen.has(nk)) continue;
    seen.add(nk);
    if (RECIPE_VALID_KEYS.has(nk)) valid.push(nk);
    else invalid.push(nk);
  }
  return { valid, invalid };
}

export function extractFieldTagsFromChunk(content) {
  if (!content || typeof content !== 'string') return [];
  const t = content.trim();
  if (!t.startsWith('{') && !t.startsWith('[')) return [];
  try {
    const obj = JSON.parse(t);
    if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
      return Object.keys(obj);
    }
    if (Array.isArray(obj) && obj[0] && typeof obj[0] === 'object') {
      return Object.keys(obj[0]);
    }
  } catch {
    /* ignore */
  }
  return [];
}

export function inferFieldsFromDocument(doc) {
  if (Array.isArray(doc?.valid_fields) || Array.isArray(doc?.invalid_fields)) {
    return {
      valid: doc.valid_fields || [],
      invalid: doc.invalid_fields || [],
    };
  }
  const keySet = new Set();
  for (const ch of doc?.chunks || []) {
    extractFieldTagsFromChunk(ch.content).forEach((x) => keySet.add(x));
  }
  return splitValidInvalidFields([...keySet]);
}

export function extractRecipeFromChunkContent(content) {
  if (!content || typeof content !== 'string') return null;
  const t = content.trim();
  if (!t.startsWith('{')) return null;
  try {
    const obj = JSON.parse(t);
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return null;
    const name = obj.name || obj.title || obj.recipe_name || obj['菜名'] || obj['菜谱名'];
    let ingredients = obj.ingredients || obj['食材'] || obj['原料'];
    let steps = obj.steps || obj['步骤'] || obj['做法'] || obj.instructions;
    if (!name && ingredients == null && steps == null) return null;

    if (Array.isArray(ingredients)) ingredients = ingredients.map(String);
    else if (typeof ingredients === 'string') {
      ingredients = ingredients.split(/[,，\n]/).map((s) => s.trim()).filter(Boolean);
    } else if (ingredients != null) ingredients = [String(ingredients)];
    else ingredients = [];

    if (Array.isArray(steps)) steps = steps.map(String);
    else if (typeof steps === 'string') {
      steps = steps.split(/\n/).map((s) => s.trim()).filter(Boolean);
    } else if (steps != null) steps = [String(steps)];
    else steps = [];

    return {
      name: name != null ? String(name) : null,
      ingredients,
      steps,
    };
  } catch {
    return null;
  }
}

export function resolveIndexTime(doc) {
  if (doc?.indexed_at) return doc.indexed_at;
  const times = (doc?.chunks || []).map((c) => c.created_at).filter(Boolean);
  if (times.length) {
    return times.reduce((a, b) => (a > b ? a : b));
  }
  return doc?.updated_at || null;
}

export function getDocumentFieldStats(record) {
  const v =
    record?.valid_field_count ??
    (Array.isArray(record?.valid_fields) ? record.valid_fields.length : null);
  let t = record?.total_field_count ?? record?.total_fields ?? null;
  if (v != null && t == null && Array.isArray(record?.invalid_fields)) {
    t = v + record.invalid_fields.length;
  }
  if (v != null && t != null && t > 0) {
    return { valid: v, total: t, ratio: v / t };
  }
  return null;
}

export function ratioColor(ratio) {
  if (ratio >= 0.8) return '#52c41a';
  if (ratio >= 0.6) return '#faad14';
  return '#ff4d4f';
}

export function previewFieldsFromFileSample(text, fileName) {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  if (ext === 'json') {
    try {
      const obj = JSON.parse(text);
      const keys =
        obj && typeof obj === 'object' && !Array.isArray(obj)
          ? Object.keys(obj)
          : Array.isArray(obj) && obj[0] && typeof obj[0] === 'object'
            ? Object.keys(obj[0])
            : [];
      const { valid, invalid } = splitValidInvalidFields(keys);
      return { valid, invalid, mode: 'json' };
    } catch {
      return { valid: [], invalid: [], mode: 'json', error: 'JSON 解析失败' };
    }
  }

  const keys = new Set();
  const sample = text.slice(0, 12000);
  const re = /^[ \t]*([^\s:：]{1,48})[ \t]*[:：]/gm;
  let m;
  while ((m = re.exec(sample)) !== null) {
    keys.add(m[1].trim());
  }
  const { valid, invalid } = splitValidInvalidFields([...keys]);
  return { valid, invalid, mode: 'heuristic' };
}

export function readUploadPreview(fileLike) {
  return new Promise((resolve) => {
    const raw = fileLike?.originFileObj || fileLike;
    if (!raw?.name) {
      resolve(null);
      return;
    }
    const ext = raw.name.split('.').pop()?.toLowerCase() || '';
    if (['pdf', 'xlsx', 'docx'].includes(ext)) {
      resolve({
        valid: [],
        invalid: [],
        mode: 'binary',
        hint: '此格式将在上传后由服务端解析，此处不做字段预览。',
      });
      return;
    }
    const blob = raw.slice ? raw.slice(0, 200 * 1024) : raw;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const result = previewFieldsFromFileSample(text, raw.name);
      resolve(result);
    };
    reader.onerror = () => resolve({ valid: [], invalid: [], mode: 'error', error: '无法读取文件' });
    reader.readAsText(blob);
  });
}
